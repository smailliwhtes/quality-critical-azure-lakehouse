"""Validate the preprovisioned Unity Catalog namespaces and attached runtime."""

import argparse

from common import set_task_value, spark, utc_now

parser = argparse.ArgumentParser()
parser.add_argument("--catalog", required=True)
args = parser.parse_args()

catalog_identifier = f"`{args.catalog.replace('`', '``')}`"
required_schemas = {"bronze", "silver", "gold", "governance"}
actual_schemas = {
    str(row[0]) for row in spark.sql(f"SHOW SCHEMAS IN {catalog_identifier}").collect()
}
missing_schemas = sorted(required_schemas - actual_schemas)
if missing_schemas:
    raise RuntimeError(f"Unity Catalog is missing required schemas: {missing_schemas}")

set_task_value("catalog", args.catalog)
set_task_value("schema_count", str(len(required_schemas)))
set_task_value("spark_version", spark.version)
set_task_value("validated_at_utc", utc_now())
