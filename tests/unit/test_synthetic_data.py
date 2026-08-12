from dataclasses import replace
from pathlib import Path

from qcal.synthetic import SyntheticDataConfig, generate_synthetic_dataset, summarize_dataset


def test_default_dataset_contract_matches_portfolio_specification() -> None:
    config = SyntheticDataConfig()

    assert config.seed == 20260812
    assert config.site_count == 12
    assert config.product_count == 20
    assert config.batch_count == 600
    assert config.sensor_count == 24
    assert config.quality_observation_count == 30_000
    assert config.telemetry_count == 50_000
    assert config.event_hubs_count == 20_000


def test_generator_is_byte_deterministic_and_includes_required_defects(tmp_path: Path) -> None:
    config = replace(
        SyntheticDataConfig(),
        site_count=3,
        product_count=4,
        batch_count=24,
        sensor_count=6,
        quality_observation_count=240,
        telemetry_count=300,
        event_hubs_count=120,
    )
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_manifest = generate_synthetic_dataset(first, config)
    second_manifest = generate_synthetic_dataset(second, config)

    assert first_manifest["dataset_sha256"] == second_manifest["dataset_sha256"]
    assert summarize_dataset(first) == summarize_dataset(second)
    assert set(first_manifest["intentional_defects"]) == {
        "duplicate_business_record",
        "duplicate_event_id",
        "null_business_key",
        "missing_batch_id",
        "unknown_foreign_key",
        "unknown_site_id",
        "malformed_timestamp",
        "impossible_temperature",
        "inconsistent_unit",
        "out_of_order_cdc",
        "schema_evolution_field",
        "reserved_hard_failure",
    }
    assert first_manifest["intentional_defects"]["reserved_hard_failure"] == 1
    assert first_manifest["intentional_defects"]["malformed_timestamp"] == 2


def test_generator_writes_multiple_adf_source_files_and_bounded_cdc(tmp_path: Path) -> None:
    config = replace(
        SyntheticDataConfig(),
        batch_count=40,
        quality_observation_count=400,
        telemetry_count=500,
        event_hubs_count=200,
        quality_file_count=4,
    )

    manifest = generate_synthetic_dataset(tmp_path, config)

    quality_files = sorted((tmp_path / "quality").glob("*.jsonl"))
    assert len(quality_files) == 4
    assert manifest["row_counts"]["quality_observations"] == 400
    assert 1 <= manifest["row_counts"]["cdc_changes"] <= 40
    assert manifest["row_counts"]["event_hubs_messages"] == 200
