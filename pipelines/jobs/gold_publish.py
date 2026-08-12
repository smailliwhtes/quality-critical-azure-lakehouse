"""Publish six business-facing Gold objects from governed Silver tables."""

import argparse

from common import (
    PRODUCT_SCHEMA,
    SITE_SCHEMA,
    build_gold_tables,
    put_json,
    spark,
    task_run_id,
    utc_now,
    volume_path,
)
from pyspark.sql import functions as F

parser = argparse.ArgumentParser()
parser.add_argument("--catalog", required=True)
args = parser.parse_args()

source = volume_path(args.catalog, "source")
sites = spark.read.schema(SITE_SCHEMA).json(f"{source}/reference/sites.jsonl")
products = spark.read.schema(PRODUCT_SCHEMA).json(f"{source}/reference/products.jsonl")
history = spark.table(f"{args.catalog}.silver.batch_history_scd2")
if "__END_AT" in history.columns:
    history = (
        history.withColumnRenamed("__START_AT", "effective_start_utc")
        .withColumnRenamed("__END_AT", "effective_end_utc")
        .withColumn("is_current", F.col("effective_end_utc").isNull())
        .withColumn("is_current_int", F.when(F.col("is_current"), 1).otherwise(0))
    )

gold = build_gold_tables(
    quality_valid=spark.table(f"{args.catalog}.silver.batch_quality_valid"),
    telemetry_valid=spark.table(f"{args.catalog}.silver.sensor_telemetry_valid"),
    batch_history=history,
    sites=sites,
    products=products,
    quarantined_quality=spark.table(f"{args.catalog}.silver.quarantined_quality_records"),
)
for table_name, dataframe in gold.items():
    dataframe.write.format("delta").mode("overwrite").option(
        "overwriteSchema", "true"
    ).saveAsTable(f"{args.catalog}.gold.{table_name}")

table_comments = {
    "fact_batch_quality": "One accepted laboratory quality observation per observation_id.",
    "fact_cold_chain_excursion": "One detected cold-chain excursion per sensor event.",
    "dim_batch_history": "SCD Type 2 batch history with exactly one current version.",
    "dim_site": "One synthetic manufacturing site per site_id.",
    "dim_product": "One synthetic regulated product per product_id.",
    "kpi_quality_summary": "Daily site and product quality, quarantine, and throughput KPIs.",
}
for table_name, comment in table_comments.items():
    full_name = f"{args.catalog}.gold.{table_name}"
    spark.sql(f"COMMENT ON TABLE {full_name} IS '{comment}'")
    spark.sql(
        f"""
        ALTER TABLE {full_name} SET TBLPROPERTIES (
          'portfolio.tier' = 'gold',
          'data.classification' = 'synthetic',
          'project' = 'linkedin-part4'
        )
        """
    )

governance = {
    "schema": "part4-governance-control-receipt/v1",
    "captured_at_utc": utc_now(),
    "run_id": task_run_id(),
    "comments_and_properties": "APPLIED",
    "unity_catalog_tags": "NOT_ATTEMPTED",
    "column_mask": "NOT_ATTEMPTED",
    "status": "DEMONSTRATED",
    "limitation": "",
}
try:
    for table_name in table_comments:
        spark.sql(
            f"""
            ALTER TABLE {args.catalog}.gold.{table_name}
            SET TAGS ('portfolio' = 'linkedin-part4', 'data_classification' = 'synthetic')
            """
        )
    governance["unity_catalog_tags"] = "APPLIED"
except Exception as error:
    governance["unity_catalog_tags"] = "PRODUCTION_BLUEPRINT"
    governance["limitation"] = f"Unity Catalog tags unavailable: {type(error).__name__}"

try:
    spark.sql(
        f"""
        CREATE OR REPLACE FUNCTION {args.catalog}.governance.mask_quality_value(value DOUBLE)
        RETURNS DOUBLE
        COMMENT 'Returns raw synthetic quality values only to account administrators.'
        RETURN CASE
          WHEN is_account_group_member('admins') THEN value
          ELSE CAST(NULL AS DOUBLE)
        END
        """
    )
    spark.sql(
        f"""
        ALTER TABLE {args.catalog}.gold.fact_batch_quality
        ALTER COLUMN result_value
        SET MASK {args.catalog}.governance.mask_quality_value
        """
    )
    governance["column_mask"] = "APPLIED"
    governance["status"] = "VERIFIED"
except Exception as error:
    governance["column_mask"] = "PRODUCTION_BLUEPRINT"
    limitation = f"Column masking unavailable: {type(error).__name__}"
    governance["limitation"] = "; ".join(
        item for item in [governance["limitation"], limitation] if item
    )

put_json(
    volume_path(
        args.catalog,
        "evidence",
        f"governance/{governance['run_id']}.json",
    ),
    governance,
)
