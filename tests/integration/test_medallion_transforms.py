from __future__ import annotations

from datetime import UTC, datetime

from pyspark.sql import Row

from qcal.schemas import (
    BATCH_MASTER_SCHEMA,
    CDC_EVENT_SCHEMA,
    QUALITY_SOURCE_SCHEMA,
    TELEMETRY_SOURCE_SCHEMA,
)
from qcal.transforms import (
    add_bronze_provenance,
    build_gold_tables,
    build_scd2_history,
    dataframe_content_hash,
    validate_quality,
    validate_telemetry,
)


def _batch_rows():
    return [
        (
            "BATCH-00001",
            "SITE-001",
            "PROD-001",
            "LOT-202600001",
            "2026-07-01T00:00:00Z",
            "REVIEW",
            "2026-07-01T00:00:00Z",
            1,
            "1.0",
        ),
        (
            "BATCH-00002",
            "SITE-002",
            "PROD-002",
            "LOT-202600002",
            "2026-07-01T01:30:00Z",
            "RELEASED",
            "2026-07-01T01:30:00Z",
            1,
            "1.0",
        ),
    ]


def test_bronze_preserves_rows_and_adds_required_provenance(spark) -> None:
    source = spark.createDataFrame(
        [
            (
                "OBS-0000001",
                "BATCH-00001",
                "SITE-001",
                "PROD-001",
                "assay",
                99.2,
                "%",
                95.0,
                102.0,
                5.0,
                "2026-07-01T00:03:00Z",
                "quality_lims_synthetic",
                "1.0",
                None,
            )
        ],
        QUALITY_SOURCE_SCHEMA,
    )

    bronze = add_bronze_provenance(
        source,
        source_file="quality/quality_observations_01.jsonl",
        pipeline_run_id="local-test-run",
        ingest_timestamp_utc="2026-08-12T12:00:00Z",
        raw_event_timestamp_column="event_timestamp",
    )
    row = bronze.first().asDict()

    assert bronze.count() == source.count()
    assert {
        "source_file",
        "source_system",
        "ingest_timestamp_utc",
        "event_timestamp_utc",
        "pipeline_run_id",
        "record_hash",
        "schema_version",
    } <= set(bronze.columns)
    assert row["event_timestamp_utc"] == "2026-07-01T00:03:00Z"
    assert row["pipeline_run_id"] == "local-test-run"
    assert len(row["record_hash"]) == 64


def test_quality_rules_route_each_defect_and_keep_one_duplicate(spark) -> None:
    valid = (
        "OBS-0000001",
        "BATCH-00001",
        "SITE-001",
        "PROD-001",
        "assay",
        99.2,
        "%",
        95.0,
        102.0,
        5.0,
        "2026-07-01T00:03:00Z",
        "quality_lims_synthetic",
        "1.0",
        None,
    )
    records = [
        valid,
        valid,
        (None, *valid[1:]),
        ("OBS-0000002", "BATCH-UNKNOWN", *valid[2:]),
        ("OBS-0000003", *valid[1:10], "not-a-timestamp", *valid[11:]),
        ("OBS-0000004", *valid[1:9], 145.0, *valid[10:]),
        ("OBS-0000005", *valid[1:6], "degF", *valid[7:]),
    ]
    source = spark.createDataFrame(records, QUALITY_SOURCE_SCHEMA)
    bronze = add_bronze_provenance(
        source,
        source_file="quality/quality_observations_01.jsonl",
        pipeline_run_id="local-test-run",
        ingest_timestamp_utc="2026-08-12T12:00:00Z",
        raw_event_timestamp_column="event_timestamp",
    )
    batches = spark.createDataFrame(_batch_rows(), BATCH_MASTER_SCHEMA)

    result = validate_quality(bronze, batches)
    reasons = {
        row.quarantine_reason
        for row in result.quarantine.select("quarantine_reason").collect()
    }

    assert result.valid.count() == 1
    assert result.quarantine.count() == 6
    assert reasons == {
        "DUPLICATE_RECORD",
        "NULL_BUSINESS_KEY",
        "UNKNOWN_BATCH",
        "MALFORMED_TIMESTAMP",
        "IMPOSSIBLE_TEMPERATURE",
        "INCONSISTENT_UNIT",
    }
    assert result.valid.schema["event_timestamp_utc"].dataType.typeName() == "timestamp"


def test_telemetry_validation_uses_explicit_schema_and_quarantine(spark) -> None:
    rows = [
        (
            "EVT-000001",
            "SENSOR-001",
            "BATCH-00001",
            "SITE-001",
            "temperature_c",
            5.6,
            "C",
            "2026-07-01T00:03:00Z",
            1,
            "3.2.1",
            "plant_sensor_synthetic",
            "1.0",
        ),
        (
            None,
            "SENSOR-001",
            "BATCH-00001",
            "SITE-001",
            "temperature_c",
            5.7,
            "C",
            "2026-07-01T00:04:00Z",
            2,
            "3.2.1",
            "plant_sensor_synthetic",
            "1.0",
        ),
        (
            "EVT-000003",
            "SENSOR-001",
            "BATCH-00001",
            "SITE-001",
            "temperature_c",
            145.0,
            "C",
            "2026-07-01T00:05:00Z",
            3,
            "3.2.1",
            "plant_sensor_synthetic",
            "1.0",
        ),
    ]
    source = spark.createDataFrame(rows, TELEMETRY_SOURCE_SCHEMA)
    bronze = add_bronze_provenance(
        source,
        source_file="eventhubs://part4-telemetry/partition-0",
        pipeline_run_id="local-stream-run",
        ingest_timestamp_utc="2026-08-12T12:00:00Z",
        raw_event_timestamp_column="event_ts",
    )

    result = validate_telemetry(bronze)

    assert result.valid.count() == 1
    assert result.quarantine.count() == 2
    assert {row.quarantine_reason for row in result.quarantine.collect()} == {
        "NULL_EVENT_ID",
        "IMPOSSIBLE_TEMPERATURE",
    }


def test_scd2_preserves_history_handles_out_of_order_cdc_and_is_idempotent(spark) -> None:
    batches = spark.createDataFrame(_batch_rows(), BATCH_MASTER_SCHEMA)
    changes = spark.createDataFrame(
        [
            (
                "CDC-00002",
                "BATCH-00001",
                "UPDATE",
                3,
                "2026-07-03T00:00:00Z",
                "RELEASED",
                "batch_erp_synthetic",
                "1.0",
            ),
            (
                "CDC-00001",
                "BATCH-00001",
                "UPDATE",
                2,
                "2026-07-02T00:00:00Z",
                "HOLD",
                "batch_erp_synthetic",
                "1.0",
            ),
        ],
        CDC_EVENT_SCHEMA,
    )

    first = build_scd2_history(batches, changes)
    second = build_scd2_history(batches, changes)
    batch_one = first.filter("batch_id = 'BATCH-00001'").orderBy("effective_start_utc").collect()

    assert len(batch_one) == 3
    assert [row.release_status for row in batch_one] == ["REVIEW", "HOLD", "RELEASED"]
    assert [row.is_current for row in batch_one] == [False, False, True]
    invalid_current_counts = (
        first.groupBy("batch_id").sum("is_current_int").filter("sum(is_current_int) != 1").count()
    )
    assert invalid_current_counts == 0
    assert dataframe_content_hash(first, ["batch_id", "sequence_number"]) == dataframe_content_hash(
        second, ["batch_id", "sequence_number"]
    )


def test_gold_tables_have_documented_grains_and_correct_quality_kpi(spark) -> None:
    quality_valid = spark.createDataFrame(
        [
            Row(
                observation_id="OBS-1",
                batch_id="BATCH-00001",
                site_id="SITE-001",
                product_id="PROD-001",
                test_type="assay",
                result_value=99.0,
                spec_lower=95.0,
                spec_upper=102.0,
                event_timestamp_utc=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
            ),
            Row(
                observation_id="OBS-2",
                batch_id="BATCH-00001",
                site_id="SITE-001",
                product_id="PROD-001",
                test_type="assay",
                result_value=104.0,
                spec_lower=95.0,
                spec_upper=102.0,
                event_timestamp_utc=datetime(2026, 7, 1, 13, 0, tzinfo=UTC),
            ),
        ]
    )
    telemetry_valid = spark.createDataFrame(
        [
            Row(
                event_id="EVT-1",
                sensor_id="SENSOR-001",
                batch_id="BATCH-00001",
                site_id="SITE-001",
                metric_name="temperature_c",
                value=10.0,
                unit="C",
                event_timestamp_utc=datetime(2026, 7, 1, 12, 5, tzinfo=UTC),
            )
        ]
    )
    history = spark.createDataFrame(
        [
            Row(
                batch_id="BATCH-00001",
                site_id="SITE-001",
                product_id="PROD-001",
                lot_number="LOT-1",
                release_status="RELEASED",
                sequence_number=1,
                effective_start_utc=datetime(2026, 7, 1, tzinfo=UTC),
                effective_end_utc=None,
                is_current=True,
                is_current_int=1,
            )
        ],
        """
        batch_id string,
        site_id string,
        product_id string,
        lot_number string,
        release_status string,
        sequence_number long,
        effective_start_utc timestamp,
        effective_end_utc timestamp,
        is_current boolean,
        is_current_int integer
        """,
    )
    sites = spark.createDataFrame(
        [Row(site_id="SITE-001", site_name="Site 1", region="Northeast", active=True)]
    )
    products = spark.createDataFrame(
        [
            Row(
                product_id="PROD-001",
                product_name="Product 1",
                target_assay_pct=99.0,
                temperature_limit_c=8.0,
            )
        ]
    )
    quarantine = spark.createDataFrame(
        [
            Row(
                site_id="SITE-001",
                product_id="PROD-001",
                event_timestamp_utc=datetime(2026, 7, 1, 14, 0, tzinfo=UTC),
            )
        ]
    )

    gold = build_gold_tables(
        quality_valid=quality_valid,
        telemetry_valid=telemetry_valid,
        batch_history=history,
        sites=sites,
        products=products,
        quarantined_quality=quarantine,
    )
    kpi = gold["kpi_quality_summary"].first().asDict()

    assert set(gold) == {
        "fact_batch_quality",
        "fact_cold_chain_excursion",
        "dim_batch_history",
        "dim_site",
        "dim_product",
        "kpi_quality_summary",
    }
    assert gold["fact_batch_quality"].count() == 2
    assert gold["fact_cold_chain_excursion"].count() == 1
    assert kpi["batches_processed"] == 1
    assert kpi["quality_pass_rate"] == 0.5
    assert kpi["records_quarantined"] == 1
    assert kpi["batches_with_excursions"] == 1
