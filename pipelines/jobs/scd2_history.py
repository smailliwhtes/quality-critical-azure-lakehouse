"""Deterministic SCD2 fallback used only when Lakeflow AUTO CDC is unavailable."""

import argparse

from common import (
    BATCH_MASTER_SCHEMA,
    CDC_EVENT_SCHEMA,
    build_scd2_history,
    spark,
    volume_path,
)

parser = argparse.ArgumentParser()
parser.add_argument("--catalog", required=True)
args = parser.parse_args()

source = volume_path(args.catalog, "source")
batches = spark.read.schema(BATCH_MASTER_SCHEMA).json(f"{source}/batch/batch_master.jsonl")
changes = spark.read.schema(CDC_EVENT_SCHEMA).json(f"{source}/cdc/batch_change_events.jsonl")
history = build_scd2_history(batches, changes)
history.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{args.catalog}.silver.batch_history_scd2"
)
