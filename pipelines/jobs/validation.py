"""Fail the run if Gold grains, current history, or duplicate invariants break."""

import argparse

from common import set_task_value, spark

parser = argparse.ArgumentParser()
parser.add_argument("--catalog", required=True)
args = parser.parse_args()

checks = {
    "quality_rows_positive": f"SELECT count(*) > 0 ok FROM {args.catalog}.gold.fact_batch_quality",
    "no_quality_key_duplicates": f"""
        SELECT count(*) = 0 ok FROM (
          SELECT observation_id FROM {args.catalog}.gold.fact_batch_quality
          GROUP BY observation_id HAVING count(*) > 1
        )
    """,
    "one_current_batch_version": f"""
        SELECT count(*) = 0 ok FROM (
          SELECT batch_id FROM {args.catalog}.gold.dim_batch_history
          GROUP BY batch_id HAVING sum(CASE WHEN is_current THEN 1 ELSE 0 END) <> 1
        )
    """,
    "kpi_grain_unique": f"""
        SELECT count(*) = 0 ok FROM (
          SELECT site_id, product_id, reporting_date
          FROM {args.catalog}.gold.kpi_quality_summary
          GROUP BY site_id, product_id, reporting_date HAVING count(*) > 1
        )
    """,
}
results = {name: bool(spark.sql(query).first().ok) for name, query in checks.items()}
failed = [name for name, passed in results.items() if not passed]
assert not failed, f"Gold validation failures: {failed}"
set_task_value("validation_results", results)
