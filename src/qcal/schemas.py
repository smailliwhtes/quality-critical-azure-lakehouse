"""Explicit Spark schemas shared by batch, streaming, and test entrypoints."""

from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)

QUALITY_SOURCE_SCHEMA = StructType(
    [
        StructField("observation_id", StringType(), True),
        StructField("batch_id", StringType(), True),
        StructField("site_id", StringType(), True),
        StructField("product_id", StringType(), True),
        StructField("test_type", StringType(), True),
        StructField("result_value", DoubleType(), True),
        StructField("unit", StringType(), True),
        StructField("spec_lower", DoubleType(), True),
        StructField("spec_upper", DoubleType(), True),
        StructField("sample_temperature_c", DoubleType(), True),
        StructField("event_timestamp", StringType(), True),
        StructField("source_system", StringType(), True),
        StructField("schema_version", StringType(), True),
        StructField("analyst_shift", StringType(), True),
    ]
)

BATCH_MASTER_SCHEMA = StructType(
    [
        StructField("batch_id", StringType(), False),
        StructField("site_id", StringType(), False),
        StructField("product_id", StringType(), False),
        StructField("lot_number", StringType(), False),
        StructField("manufactured_at", StringType(), False),
        StructField("release_status", StringType(), False),
        StructField("effective_at", StringType(), False),
        StructField("sequence_number", LongType(), False),
        StructField("schema_version", StringType(), False),
    ]
)

CDC_EVENT_SCHEMA = StructType(
    [
        StructField("event_id", StringType(), False),
        StructField("batch_id", StringType(), False),
        StructField("operation", StringType(), False),
        StructField("sequence_number", LongType(), False),
        StructField("effective_at", StringType(), False),
        StructField("release_status", StringType(), False),
        StructField("source_system", StringType(), False),
        StructField("schema_version", StringType(), False),
    ]
)

TELEMETRY_SOURCE_SCHEMA = StructType(
    [
        StructField("event_id", StringType(), True),
        StructField("sensor_id", StringType(), True),
        StructField("batch_id", StringType(), True),
        StructField("site_id", StringType(), True),
        StructField("metric_name", StringType(), True),
        StructField("value", DoubleType(), True),
        StructField("unit", StringType(), True),
        StructField("event_ts", StringType(), True),
        StructField("sequence_number", LongType(), True),
        StructField("firmware_version", StringType(), True),
        StructField("source_system", StringType(), True),
        StructField("schema_version", StringType(), True),
    ]
)

SITE_SCHEMA = StructType(
    [
        StructField("site_id", StringType(), False),
        StructField("site_name", StringType(), False),
        StructField("region", StringType(), False),
        StructField("active", BooleanType(), False),
    ]
)

PRODUCT_SCHEMA = StructType(
    [
        StructField("product_id", StringType(), False),
        StructField("product_name", StringType(), False),
        StructField("target_assay_pct", DoubleType(), False),
        StructField("temperature_limit_c", DoubleType(), False),
    ]
)

