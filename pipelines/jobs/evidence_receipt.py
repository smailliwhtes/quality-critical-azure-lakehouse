"""Persist a sanitized machine receipt after successful end-to-end validation."""

import argparse
import hashlib

from common import put_json, spark, task_run_id, utc_now, volume_path
from pyspark.sql import functions as F

parser = argparse.ArgumentParser()
parser.add_argument("--catalog", required=True)
parser.add_argument("--execution-commit", required=True)
args = parser.parse_args()

tables = [
    "bronze.batch_quality_raw",
    "bronze.batch_change_events",
    "bronze.sensor_telemetry_raw",
    "silver.batch_quality_valid",
    "silver.sensor_telemetry_valid",
    "silver.batch_master_current",
    "silver.batch_history_scd2",
    "silver.quarantined_quality_records",
    "silver.quarantined_telemetry",
    "gold.fact_batch_quality",
    "gold.fact_cold_chain_excursion",
    "gold.dim_batch_history",
    "gold.dim_site",
    "gold.dim_product",
    "gold.kpi_quality_summary",
]
row_counts = {table: spark.table(f"{args.catalog}.{table}").count() for table in tables}


def content_hash(table: str) -> str:
    dataframe = spark.table(f"{args.catalog}.{table}")
    volatile_provenance = {"ingest_timestamp_utc", "pipeline_run_id"}
    columns = sorted(column for column in dataframe.columns if column not in volatile_provenance)
    row_hashes = dataframe.select(
        F.sha2(
            F.to_json(
                F.struct(*[F.col(column) for column in columns]),
                options={"ignoreNullFields": "false"},
            ),
            256,
        ).alias("row_hash")
    ).orderBy("row_hash")
    digest = hashlib.sha256()
    for row in row_hashes.toLocalIterator():
        digest.update(row.row_hash.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


hash_tables = [
    "silver.batch_quality_valid",
    "silver.sensor_telemetry_valid",
    "silver.batch_history_scd2",
    "gold.fact_batch_quality",
    "gold.fact_cold_chain_excursion",
    "gold.kpi_quality_summary",
]
content_hashes = {table: content_hash(table) for table in hash_tables}
duplicate_business_keys = {
    "fact_batch_quality": spark.sql(
        f"""
        SELECT count(*) duplicate_groups FROM (
          SELECT observation_id FROM {args.catalog}.gold.fact_batch_quality
          GROUP BY observation_id HAVING count(*) > 1
        )
        """
    ).first().duplicate_groups,
    "kpi_quality_summary": spark.sql(
        f"""
        SELECT count(*) duplicate_groups FROM (
          SELECT site_id, product_id, reporting_date
          FROM {args.catalog}.gold.kpi_quality_summary
          GROUP BY site_id, product_id, reporting_date HAVING count(*) > 1
        )
        """
    ).first().duplicate_groups,
}
current_version_violations = spark.sql(
    f"""
    SELECT count(*) violation_groups FROM (
      SELECT batch_id FROM {args.catalog}.gold.dim_batch_history
      GROUP BY batch_id HAVING sum(CASE WHEN is_current THEN 1 ELSE 0 END) <> 1
    )
    """
).first().violation_groups
aggregates = spark.sql(
    f"""
    SELECT
      sum(batches_processed) AS batches_processed_sum,
      sum(records_quarantined) AS records_quarantined_sum,
      round(avg(quality_pass_rate), 12) AS mean_quality_pass_rate
    FROM {args.catalog}.gold.kpi_quality_summary
    """
).first().asDict()
run_id = task_run_id()
receipt = {
    "schema": "part4-lakeflow-job-receipt/v1",
    "captured_at_utc": utc_now(),
    "run_id": run_id,
    "execution_commit": args.execution_commit,
    "runtime": spark.conf.get("spark.databricks.clusterUsageTags.sparkVersion", spark.version),
    "catalog": args.catalog,
    "row_counts": row_counts,
    "content_hashes": content_hashes,
    "content_hash_definition": {
        "algorithm": "SHA-256 over ordered canonical row SHA-256 values",
        "excluded_volatile_provenance": ["ingest_timestamp_utc", "pipeline_run_id"],
    },
    "duplicate_business_keys": duplicate_business_keys,
    "current_version_violations": current_version_violations,
    "aggregates": aggregates,
    "validation": "PASS",
}
put_json(volume_path(args.catalog, "evidence", f"jobs/{run_id}.json"), receipt)
