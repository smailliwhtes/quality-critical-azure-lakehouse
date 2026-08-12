"""Lakeflow quality expectations for deterministic batch and telemetry inputs."""

from pyspark import pipelines as dp
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

spark = SparkSession.getActiveSession()
if spark is None:
    raise RuntimeError("Lakeflow requires an active Spark session")
CATALOG = spark.conf.get("part4.catalog", "part4_ops")


def _quality_evaluated():
    source = spark.read.table(f"{CATALOG}.bronze.batch_quality_raw")
    known = spark.read.table(f"{CATALOG}.bronze.batch_change_events").select(
        F.col("batch_id").alias("_known_batch_id"),
        F.col("site_id").alias("_known_site_id"),
        F.col("product_id").alias("_known_product_id"),
    ).distinct()
    duplicate_window = Window.partitionBy("record_hash").orderBy(
        "source_file", "pipeline_run_id", "ingest_timestamp_utc"
    )
    expected_unit = (
        F.when(F.col("test_type").isin("assay", "purity", "moisture"), F.lit("%"))
        .when(F.col("test_type") == "bioburden", F.lit("CFU/g"))
        .otherwise(F.lit(None).cast("string"))
    )
    return (
        source.join(known, source.batch_id == known._known_batch_id, "left")
        .withColumn("_parsed_event_timestamp", F.try_to_timestamp("event_timestamp_utc"))
        .withColumn("_duplicate_rank", F.row_number().over(duplicate_window))
        .withColumn("_expected_unit", expected_unit)
        .withColumn(
            "quarantine_reason",
            F.when(F.col("observation_id").isNull(), F.lit("NULL_BUSINESS_KEY"))
            .when(F.col("batch_id").isNull(), F.lit("NULL_BATCH_ID"))
            .when(F.col("site_id").isNull(), F.lit("NULL_SITE_ID"))
            .when(F.col("_known_batch_id").isNull(), F.lit("UNKNOWN_BATCH"))
            .when(F.col("site_id") != F.col("_known_site_id"), F.lit("UNKNOWN_SITE"))
            .when(F.col("product_id") != F.col("_known_product_id"), F.lit("UNKNOWN_PRODUCT"))
            .when(F.col("_parsed_event_timestamp").isNull(), F.lit("MALFORMED_TIMESTAMP"))
            .when(
                ~F.col("sample_temperature_c").between(-80.0, 80.0),
                F.lit("IMPOSSIBLE_TEMPERATURE"),
            )
            .when(
                F.col("_expected_unit").isNull() | (F.col("unit") != F.col("_expected_unit")),
                F.lit("INCONSISTENT_UNIT"),
            )
            .when(F.col("_duplicate_rank") > 1, F.lit("DUPLICATE_RECORD")),
        )
    )


@dp.table(
    name="quality_observed",
    comment=(
        "Observed quality input used to publish expectation metrics and enforce the hard contract."
    ),
)
@dp.expect("batch_id_not_null", "batch_id IS NOT NULL")
@dp.expect("site_id_not_null", "site_id IS NOT NULL")
@dp.expect("valid_event_timestamp", "try_cast(event_timestamp_utc AS TIMESTAMP) IS NOT NULL")
@dp.expect("valid_quality_domain", "result_value BETWEEN 0.0 AND 150.0")
@dp.expect_or_fail("reserved_schema_contract", "schema_version <> '99.0-reserved-failure'")
def quality_observed():
    return spark.read.table(f"{CATALOG}.bronze.batch_quality_raw")


@dp.table(
    name="batch_quality_valid",
    comment=(
        "Conformed quality observations that passed schema, key, range, unit, and duplicate rules."
    ),
)
@dp.expect_or_drop("batch_id_not_null", "batch_id IS NOT NULL")
@dp.expect_or_drop("site_id_not_null", "site_id IS NOT NULL")
def batch_quality_valid():
    return (
        _quality_evaluated()
        .filter(F.col("quarantine_reason").isNull())
        .drop("event_timestamp_utc")
        .withColumnRenamed("_parsed_event_timestamp", "event_timestamp_utc")
        .drop(
            "_duplicate_rank",
            "_expected_unit",
            "_known_batch_id",
            "_known_site_id",
            "_known_product_id",
            "quarantine_reason",
        )
    )


@dp.table(
    name="quarantined_quality_records",
    comment=(
        "Quality records retained with deterministic rejection reasons for diagnosis and replay."
    ),
)
def quarantined_quality_records():
    return _quality_evaluated().filter(F.col("quarantine_reason").isNotNull()).drop(
        "_parsed_event_timestamp",
        "_duplicate_rank",
        "_expected_unit",
        "_known_batch_id",
        "_known_site_id",
        "_known_product_id",
    )


def _telemetry_evaluated():
    source = spark.read.table(f"{CATALOG}.bronze.sensor_telemetry_raw")
    known = spark.read.table(f"{CATALOG}.bronze.batch_change_events").select(
        F.col("batch_id").alias("_known_batch_id"),
        F.col("site_id").alias("_known_site_id"),
    ).distinct()
    duplicate_window = Window.partitionBy("event_id").orderBy(
        "source_file", "partition", "offset"
    )
    return (
        source.join(known, source.batch_id == known._known_batch_id, "left")
        .withColumn("_parsed_event_timestamp", F.try_to_timestamp("event_timestamp_utc"))
        .withColumn("_duplicate_rank", F.row_number().over(duplicate_window))
        .withColumn(
            "quarantine_reason",
            F.when(F.col("event_id").isNull(), F.lit("NULL_EVENT_ID"))
            .when(F.col("batch_id").isNull(), F.lit("NULL_BATCH_ID"))
            .when(F.col("site_id").isNull(), F.lit("NULL_SITE_ID"))
            .when(F.col("_known_batch_id").isNull(), F.lit("UNKNOWN_BATCH"))
            .when(F.col("site_id") != F.col("_known_site_id"), F.lit("UNKNOWN_SITE"))
            .when(F.col("_parsed_event_timestamp").isNull(), F.lit("MALFORMED_TIMESTAMP"))
            .when(
                (F.col("metric_name") == "temperature_c")
                & ~F.col("value").between(-80.0, 80.0),
                F.lit("IMPOSSIBLE_TEMPERATURE"),
            )
            .when(
                ((F.col("metric_name") == "temperature_c") & (F.col("unit") != "C"))
                | ((F.col("metric_name") == "vibration_mm_s") & (F.col("unit") != "mm/s")),
                F.lit("INCONSISTENT_UNIT"),
            )
            .when(F.col("_duplicate_rank") > 1, F.lit("DUPLICATE_EVENT_ID")),
        )
    )


@dp.table(
    name="sensor_telemetry_valid",
    comment="Telemetry accepted by event, key, timestamp, range, and duplicate expectations.",
)
@dp.expect_or_drop("valid_event_id", "event_id IS NOT NULL")
@dp.expect_or_drop("valid_temperature_range", "value BETWEEN -80.0 AND 80.0")
def sensor_telemetry_valid():
    return (
        _telemetry_evaluated()
        .filter(F.col("quarantine_reason").isNull())
        .drop("event_timestamp_utc")
        .withColumnRenamed("_parsed_event_timestamp", "event_timestamp_utc")
        .drop(
            "_duplicate_rank",
            "_known_batch_id",
            "_known_site_id",
            "quarantine_reason",
        )
    )


@dp.table(
    name="quarantined_telemetry",
    comment="Telemetry retained with deterministic rejection reasons for diagnosis and replay.",
)
def quarantined_telemetry():
    return _telemetry_evaluated().filter(F.col("quarantine_reason").isNotNull()).drop(
        "_parsed_event_timestamp", "_duplicate_rank", "_known_batch_id", "_known_site_id"
    )
