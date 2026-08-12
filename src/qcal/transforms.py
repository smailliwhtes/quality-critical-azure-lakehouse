"""Reusable PySpark transformations for Bronze, Silver, SCD2, and Gold."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Accepted and quarantined records produced by a quality gate."""

    valid: DataFrame
    quarantine: DataFrame


def add_bronze_provenance(
    dataframe: DataFrame,
    *,
    source_file: str,
    pipeline_run_id: str,
    ingest_timestamp_utc: str,
    raw_event_timestamp_column: str,
) -> DataFrame:
    """Add technical provenance without cleansing source values."""

    source_columns = sorted(dataframe.columns)
    canonical_record = F.to_json(
        F.struct(*[F.col(column) for column in source_columns]),
        options={"ignoreNullFields": "false"},
    )
    return (
        dataframe.withColumn("source_file", F.lit(source_file))
        .withColumn("ingest_timestamp_utc", F.to_timestamp(F.lit(ingest_timestamp_utc)))
        .withColumn("event_timestamp_utc", F.col(raw_event_timestamp_column))
        .withColumn("pipeline_run_id", F.lit(pipeline_run_id))
        .withColumn("record_hash", F.sha2(canonical_record, 256))
    )


def validate_quality(bronze: DataFrame, batch_master: DataFrame) -> ValidationResult:
    """Apply explicit quality rules and route every invalid record to quarantine."""

    known_batches = batch_master.select(F.col("batch_id").alias("_known_batch_id")).distinct()
    duplicate_window = Window.partitionBy("record_hash").orderBy(
        "source_file", "pipeline_run_id", "ingest_timestamp_utc"
    )
    expected_unit = (
        F.when(F.col("test_type").isin("assay", "purity", "moisture"), F.lit("%"))
        .when(F.col("test_type") == "bioburden", F.lit("CFU/g"))
        .otherwise(F.lit(None).cast("string"))
    )
    enriched = (
        bronze.join(known_batches, bronze.batch_id == known_batches._known_batch_id, "left")
        .withColumn("_parsed_event_timestamp", F.try_to_timestamp("event_timestamp_utc"))
        .withColumn("_duplicate_rank", F.row_number().over(duplicate_window))
        .withColumn("_expected_unit", expected_unit)
    )
    quarantine_reason = (
        F.when(F.col("observation_id").isNull(), F.lit("NULL_BUSINESS_KEY"))
        .when(F.col("_known_batch_id").isNull(), F.lit("UNKNOWN_BATCH"))
        .when(F.col("_parsed_event_timestamp").isNull(), F.lit("MALFORMED_TIMESTAMP"))
        .when(
            ~F.col("sample_temperature_c").between(-80.0, 80.0),
            F.lit("IMPOSSIBLE_TEMPERATURE"),
        )
        .when(
            F.col("_expected_unit").isNull() | (F.col("unit") != F.col("_expected_unit")),
            F.lit("INCONSISTENT_UNIT"),
        )
        .when(
            F.col("result_value").isNull()
            | F.col("spec_lower").isNull()
            | F.col("spec_upper").isNull(),
            F.lit("INVALID_QUALITY_RESULT"),
        )
        .when(F.col("_duplicate_rank") > 1, F.lit("DUPLICATE_RECORD"))
    )
    evaluated = enriched.withColumn("quarantine_reason", quarantine_reason)
    helper_columns = ["_known_batch_id", "_duplicate_rank", "_expected_unit"]
    valid = (
        evaluated.filter(F.col("quarantine_reason").isNull())
        .drop("event_timestamp_utc")
        .withColumnRenamed("_parsed_event_timestamp", "event_timestamp_utc")
        .drop("quarantine_reason", *helper_columns)
    )
    quarantine = evaluated.filter(F.col("quarantine_reason").isNotNull()).drop(
        "_parsed_event_timestamp", *helper_columns
    )
    return ValidationResult(valid=valid, quarantine=quarantine)


def validate_telemetry(bronze: DataFrame) -> ValidationResult:
    """Validate streaming telemetry using a bounded, explicit contract."""

    duplicate_window = Window.partitionBy("event_id").orderBy(
        "source_file", "pipeline_run_id", "ingest_timestamp_utc"
    )
    evaluated = (
        bronze.withColumn("_parsed_event_timestamp", F.try_to_timestamp("event_timestamp_utc"))
        .withColumn("_duplicate_rank", F.row_number().over(duplicate_window))
        .withColumn(
            "quarantine_reason",
            F.when(F.col("event_id").isNull(), F.lit("NULL_EVENT_ID"))
            .when(F.col("batch_id").isNull(), F.lit("NULL_BATCH_ID"))
            .when(F.col("site_id").isNull(), F.lit("NULL_SITE_ID"))
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
    valid = (
        evaluated.filter(F.col("quarantine_reason").isNull())
        .drop("event_timestamp_utc")
        .withColumnRenamed("_parsed_event_timestamp", "event_timestamp_utc")
        .drop("quarantine_reason", "_duplicate_rank")
    )
    quarantine = evaluated.filter(F.col("quarantine_reason").isNotNull()).drop(
        "_parsed_event_timestamp", "_duplicate_rank"
    )
    return ValidationResult(valid=valid, quarantine=quarantine)


def build_scd2_history(batch_master: DataFrame, change_events: DataFrame) -> DataFrame:
    """Build deterministic SCD Type 2 history from baseline and out-of-order CDC events."""

    baseline = batch_master.select(
        "batch_id",
        "site_id",
        "product_id",
        "lot_number",
        "release_status",
        "sequence_number",
        F.to_timestamp("effective_at").alias("effective_start_utc"),
        "schema_version",
    )
    changes = change_events.alias("change").join(batch_master.alias("base"), "batch_id", "inner")
    change_versions = changes.select(
        F.col("batch_id"),
        F.col("base.site_id").alias("site_id"),
        F.col("base.product_id").alias("product_id"),
        F.col("base.lot_number").alias("lot_number"),
        F.col("change.release_status").alias("release_status"),
        F.col("change.sequence_number").alias("sequence_number"),
        F.to_timestamp(F.col("change.effective_at")).alias("effective_start_utc"),
        F.col("change.schema_version").alias("schema_version"),
    )
    versions = baseline.unionByName(change_versions).dropDuplicates(
        ["batch_id", "sequence_number", "effective_start_utc"]
    )
    history_window = Window.partitionBy("batch_id").orderBy(
        F.col("effective_start_utc"), F.col("sequence_number")
    )
    next_start = F.lead("effective_start_utc").over(history_window)
    return (
        versions.withColumn("effective_end_utc", next_start)
        .withColumn("is_current", F.col("effective_end_utc").isNull())
        .withColumn("is_current_int", F.when(F.col("is_current"), 1).otherwise(0))
        .select(
            "batch_id",
            "site_id",
            "product_id",
            "lot_number",
            "release_status",
            "sequence_number",
            "effective_start_utc",
            "effective_end_utc",
            "is_current",
            "is_current_int",
            "schema_version",
        )
    )


def dataframe_content_hash(dataframe: DataFrame, key_columns: list[str]) -> str:
    """Hash canonical ordered JSON rows for deterministic recovery checks."""

    payload = "\n".join(dataframe.orderBy(*key_columns).toJSON().collect()) + "\n"
    return hashlib.sha256(payload.encode()).hexdigest()


def build_gold_tables(
    *,
    quality_valid: DataFrame,
    telemetry_valid: DataFrame,
    batch_history: DataFrame,
    sites: DataFrame,
    products: DataFrame,
    quarantined_quality: DataFrame,
) -> dict[str, DataFrame]:
    """Build the six documented Gold facts, dimensions, and KPI outputs."""

    fact_batch_quality = (
        quality_valid.withColumn("reporting_date", F.to_date("event_timestamp_utc"))
        .withColumn(
            "quality_pass",
            F.col("result_value").between(F.col("spec_lower"), F.col("spec_upper")),
        )
        .select(
            "observation_id",
            "batch_id",
            "site_id",
            "product_id",
            "test_type",
            "result_value",
            "spec_lower",
            "spec_upper",
            "event_timestamp_utc",
            "reporting_date",
            "quality_pass",
        )
    )

    current_batch = batch_history.filter(F.col("is_current")).select(
        "batch_id", "product_id", "site_id"
    )
    telemetry_with_limits = (
        telemetry_valid.alias("telemetry")
        .join(current_batch.alias("batch"), "batch_id", "left")
        .select(
            F.col("telemetry.event_id").alias("event_id"),
            F.col("telemetry.sensor_id").alias("sensor_id"),
            F.col("batch_id"),
            F.coalesce(F.col("telemetry.site_id"), F.col("batch.site_id")).alias("site_id"),
            F.col("batch.product_id").alias("product_id"),
            F.col("telemetry.metric_name").alias("metric_name"),
            F.col("telemetry.value").alias("value"),
            F.col("telemetry.unit").alias("unit"),
            F.col("telemetry.event_timestamp_utc").alias("event_timestamp_utc"),
        )
        .join(products.select("product_id", "temperature_limit_c"), "product_id", "left")
    )
    excursions = telemetry_with_limits.filter(
        (F.col("metric_name") == "temperature_c")
        & (F.col("value") > F.col("temperature_limit_c"))
    ).withColumn("excursion_window", F.window("event_timestamp_utc", "15 minutes"))
    fact_cold_chain_excursion = (
        excursions.groupBy(
            "batch_id", "sensor_id", "site_id", "product_id", "excursion_window"
        )
        .agg(
            F.min("event_timestamp_utc").alias("excursion_start_utc"),
            F.max("event_timestamp_utc").alias("excursion_end_utc"),
            F.max("value").alias("maximum_temperature_c"),
            F.count("event_id").alias("event_count"),
        )
        .withColumn(
            "excursion_duration_minutes",
            (
                F.unix_timestamp("excursion_end_utc") - F.unix_timestamp("excursion_start_utc")
            )
            / 60.0,
        )
        .withColumn(
            "excursion_id",
            F.sha2(
                F.concat_ws(
                    "|", "batch_id", "sensor_id", F.col("excursion_window.start").cast("string")
                ),
                256,
            ),
        )
        .select(
            "excursion_id",
            "batch_id",
            "sensor_id",
            "site_id",
            "product_id",
            "excursion_start_utc",
            "excursion_end_utc",
            "excursion_duration_minutes",
            "maximum_temperature_c",
            "event_count",
        )
    )

    quality_kpi = fact_batch_quality.groupBy("site_id", "product_id", "reporting_date").agg(
        F.countDistinct("batch_id").alias("batches_processed"),
        F.count("observation_id").alias("quality_record_count"),
        F.avg(F.col("quality_pass").cast("double")).alias("quality_pass_rate"),
    )
    quarantine_kpi = (
        quarantined_quality.withColumn("reporting_date", F.to_date("event_timestamp_utc"))
        .groupBy("site_id", "product_id", "reporting_date")
        .agg(F.count(F.lit(1)).alias("records_quarantined"))
    )
    excursion_kpi = (
        fact_cold_chain_excursion.withColumn("reporting_date", F.to_date("excursion_start_utc"))
        .groupBy("site_id", "product_id", "reporting_date")
        .agg(
            F.countDistinct("batch_id").alias("batches_with_excursions"),
            F.avg("excursion_duration_minutes").alias("mean_excursion_duration_minutes"),
            F.percentile_approx("maximum_temperature_c", 0.95).alias("p95_temperature_c"),
        )
    )
    kpi_quality_summary = (
        quality_kpi.join(
            quarantine_kpi, ["site_id", "product_id", "reporting_date"], "left"
        )
        .join(excursion_kpi, ["site_id", "product_id", "reporting_date"], "left")
        .fillna(
            {
                "records_quarantined": 0,
                "batches_with_excursions": 0,
                "mean_excursion_duration_minutes": 0.0,
                "p95_temperature_c": 0.0,
            }
        )
        .withColumn(
            "invalid_record_rate",
            F.col("records_quarantined")
            / (F.col("quality_record_count") + F.col("records_quarantined")),
        )
        .withColumn(
            "excursion_rate", F.col("batches_with_excursions") / F.col("batches_processed")
        )
        .select(
            "site_id",
            "product_id",
            "reporting_date",
            "batches_processed",
            "batches_with_excursions",
            "excursion_rate",
            "invalid_record_rate",
            "quality_pass_rate",
            "mean_excursion_duration_minutes",
            "p95_temperature_c",
            "records_quarantined",
        )
    )

    return {
        "fact_batch_quality": fact_batch_quality,
        "fact_cold_chain_excursion": fact_cold_chain_excursion,
        "dim_batch_history": batch_history,
        "dim_site": sites,
        "dim_product": products,
        "kpi_quality_summary": kpi_quality_summary,
    }
