"""Land quality and CDC inputs in Bronze with source fidelity and provenance."""

import argparse

from common import (
    BATCH_MASTER_SCHEMA,
    CDC_EVENT_SCHEMA,
    QUALITY_SOURCE_SCHEMA,
    spark,
    task_run_id,
    utc_now,
    volume_path,
)
from pyspark.sql import functions as F

parser = argparse.ArgumentParser()
parser.add_argument("--catalog", required=True)
parser.add_argument("--storage-account-name", required=True)
parser.add_argument("--incident-mode", choices=["true", "false"], default="false")
args = parser.parse_args()

run_id = task_run_id()
ingest_timestamp = utc_now()
landing = volume_path(
    args.catalog,
    "landing",
    "landing/batch-quality/836901141adce556adec1811d132127953d52c9b",
)
source = volume_path(args.catalog, "source")

quality = spark.read.schema(QUALITY_SOURCE_SCHEMA).json(landing)
if args.incident_mode == "true":
    failure = spark.read.schema(QUALITY_SOURCE_SCHEMA).json(
        f"{source}/hard_failure/reserved_schema_failure.jsonl"
    )
    quality = quality.unionByName(failure, allowMissingColumns=True)

quality_columns = sorted(QUALITY_SOURCE_SCHEMA.fieldNames())
quality_bronze = (
    quality.withColumn("source_file", F.input_file_name())
    .withColumn("ingest_timestamp_utc", F.to_timestamp(F.lit(ingest_timestamp)))
    .withColumn("event_timestamp_utc", F.col("event_timestamp"))
    .withColumn("pipeline_run_id", F.lit(run_id))
    .withColumn(
        "record_hash",
        F.sha2(
            F.to_json(
                F.struct(*[F.col(column) for column in quality_columns]),
                options={"ignoreNullFields": "false"},
            ),
            256,
        ),
    )
)
quality_bronze.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable(f"{args.catalog}.bronze.batch_quality_raw")

batches = spark.read.schema(BATCH_MASTER_SCHEMA).json(f"{source}/batch/batch_master.jsonl")
changes = spark.read.schema(CDC_EVENT_SCHEMA).json(f"{source}/cdc/batch_change_events.jsonl")
baseline_events = batches.select(
    F.concat(F.lit("BASE-"), F.col("batch_id")).alias("event_id"),
    "batch_id",
    F.lit("INSERT").alias("operation"),
    "sequence_number",
    "effective_at",
    "release_status",
    "site_id",
    "product_id",
    "lot_number",
    "manufactured_at",
    F.lit("batch_master_synthetic").alias("source_system"),
    "schema_version",
)
change_events = changes.alias("change").join(batches.alias("base"), "batch_id").select(
    "change.event_id",
    "batch_id",
    "change.operation",
    "change.sequence_number",
    "change.effective_at",
    "change.release_status",
    "base.site_id",
    "base.product_id",
    "base.lot_number",
    "base.manufactured_at",
    "change.source_system",
    "change.schema_version",
)
cdc = baseline_events.unionByName(change_events)
cdc_columns = sorted(cdc.columns)
cdc_bronze = (
    cdc.withColumn("source_file", F.lit("source/batch-and-cdc"))
    .withColumn("ingest_timestamp_utc", F.to_timestamp(F.lit(ingest_timestamp)))
    .withColumn("pipeline_run_id", F.lit(run_id))
    .withColumn(
        "record_hash",
        F.sha2(F.to_json(F.struct(*[F.col(column) for column in cdc_columns])), 256),
    )
)
cdc_bronze.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{args.catalog}.bronze.batch_change_events"
)
