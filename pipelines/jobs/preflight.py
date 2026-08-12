"""Create governed catalog namespaces and validate the attached runtime."""

import argparse

from common import set_task_value, spark, utc_now

parser = argparse.ArgumentParser()
parser.add_argument("--catalog", required=True)
args = parser.parse_args()

spark.sql(f"CREATE CATALOG IF NOT EXISTS {args.catalog}")
for schema in ["bronze", "silver", "gold", "governance"]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {args.catalog}.{schema}")

spark.sql(
    f"COMMENT ON CATALOG {args.catalog} IS "
    "'Governed synthetic batch-quality and telemetry data product for Part 4.'"
)
set_task_value("catalog", args.catalog)
set_task_value("spark_version", spark.version)
set_task_value("validated_at_utc", utc_now())
