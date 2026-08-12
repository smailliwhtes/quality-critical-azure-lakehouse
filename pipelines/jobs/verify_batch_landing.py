"""Fail if ADF did not land the six pinned quality files and 30,000 rows."""

import argparse

from common import QUALITY_SOURCE_SCHEMA, dbutils, set_task_value, spark, volume_path

parser = argparse.ArgumentParser()
parser.add_argument("--storage-account-name", required=True)
parser.add_argument("--catalog", default="part4_ops")
args = parser.parse_args()

if dbutils is None:
    raise RuntimeError("Databricks utilities are required to inspect governed landing files")

landing_path = volume_path(
    args.catalog,
    "landing",
    "landing/batch-quality/836901141adce556adec1811d132127953d52c9b",
)
files = [item for item in dbutils.fs.ls(landing_path) if item.name.endswith(".jsonl")]
rows = spark.read.schema(QUALITY_SOURCE_SCHEMA).json(landing_path).count()
total_bytes = sum(item.size for item in files)

assert len(files) == 6, f"Expected six landed quality files; received {len(files)}"
assert rows == 30_000, f"Expected 30,000 landed quality rows; received {rows}"
set_task_value("landing_file_count", len(files))
set_task_value("landing_row_count", rows)
set_task_value("landing_bytes", total_bytes)
