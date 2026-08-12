"""Consume a bounded Event Hubs stream through Kafka into checkpointed Delta Bronze."""

import argparse
import json

from common import dbutils, put_json, spark, task_run_id, utc_now, volume_path
from pyspark.sql import functions as F

parser = argparse.ArgumentParser()
parser.add_argument("--catalog", required=True)
parser.add_argument("--event-hubs-namespace", required=True)
parser.add_argument("--event-hub-name", required=True)
parser.add_argument("--storage-account-name", required=True)
parser.add_argument("--secret-scope", required=True)
args = parser.parse_args()

if dbutils is None:
    raise RuntimeError("Databricks utilities are required to resolve the Event Hubs secret")

connection_string = dbutils.secrets.get(
    scope=args.secret_scope, key="eventhubs-connection-string"
)
jaas = (
    'org.apache.kafka.common.security.plain.PlainLoginModule required '
    f'username="$ConnectionString" password="{connection_string}";'
)
raw = (
    spark.readStream.format("kafka")
    .option(
        "kafka.bootstrap.servers",
        f"{args.event_hubs_namespace}.servicebus.windows.net:9093",
    )
    .option("subscribe", args.event_hub_name)
    .option("kafka.security.protocol", "SASL_SSL")
    .option("kafka.sasl.mechanism", "PLAIN")
    .option("kafka.sasl.jaas.config", jaas)
    .option("startingOffsets", "earliest")
    .option("failOnDataLoss", "false")
    .option("maxOffsetsPerTrigger", 5000)
    .load()
)

schema = """
event_id STRING, sensor_id STRING, batch_id STRING, site_id STRING,
metric_name STRING, value DOUBLE, unit STRING, event_ts STRING,
sequence_number BIGINT, firmware_version STRING, source_system STRING,
schema_version STRING
"""
parsed = raw.select(
    F.from_json(F.col("value").cast("string"), schema).alias("event"),
    "partition",
    "offset",
    F.col("timestamp").alias("kafka_timestamp_utc"),
    F.col("value").cast("string").alias("raw_payload"),
).select("event.*", "partition", "offset", "kafka_timestamp_utc", "raw_payload")

run_id = task_run_id()
bronze = (
    parsed.withColumn(
        "source_file",
        F.concat(
            F.lit("eventhubs://"),
            F.lit(args.event_hub_name),
            F.lit("/partition-"),
            F.col("partition"),
        ),
    )
    .withColumn("ingest_timestamp_utc", F.current_timestamp())
    .withColumn("event_timestamp_utc", F.col("event_ts"))
    .withColumn("pipeline_run_id", F.lit(run_id))
    .withColumn("record_hash", F.sha2("raw_payload", 256))
)
checkpoint = volume_path(args.catalog, "checkpoints", "structured-streaming/bronze-telemetry")
query = (
    bronze.writeStream.format("delta")
    .outputMode("append")
    .option("checkpointLocation", checkpoint)
    .trigger(availableNow=True)
    .toTable(f"{args.catalog}.bronze.sensor_telemetry_raw")
)
query.awaitTermination()
progress = query.lastProgress or {}
receipt = {
    "schema": "part4-stream-progress/v1",
    "captured_at_utc": utc_now(),
    "run_id": run_id,
    "checkpoint": "governed-volume/structured-streaming/bronze-telemetry",
    "progress": json.loads(json.dumps(progress, default=str)),
}
put_json(volume_path(args.catalog, "evidence", f"streaming/{run_id}.json"), receipt)
