"""Lakeflow AUTO CDC declaration for batch SCD Type 2 history."""

from pyspark import pipelines as dp
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.getActiveSession()
if spark is None:
    raise RuntimeError("Lakeflow requires an active Spark session")
CATALOG = spark.conf.get("part4.catalog", "part4_ops")


@dp.view(name="batch_change_source")
def batch_change_source():
    return spark.readStream.table(f"{CATALOG}.bronze.batch_change_events")


dp.create_streaming_table(
    name="batch_history_scd2",
    comment="Batch master history maintained by Lakeflow AUTO CDC using SCD Type 2 semantics.",
)

dp.create_auto_cdc_flow(
    target="batch_history_scd2",
    source="batch_change_source",
    keys=["batch_id"],
    sequence_by=F.struct("sequence_number", "effective_at"),
    apply_as_deletes=F.expr("operation = 'DELETE'"),
    except_column_list=[
        "event_id",
        "operation",
        "source_file",
        "source_system",
        "ingest_timestamp_utc",
        "pipeline_run_id",
        "record_hash",
        "schema_version",
    ],
    stored_as_scd_type=2,
    track_history_column_list=["release_status", "site_id", "product_id"],
)
