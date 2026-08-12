"""Deterministic synthetic batch-quality and sensor-telemetry data."""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class SyntheticDataConfig:
    seed: int = 20260812
    site_count: int = 12
    product_count: int = 20
    batch_count: int = 600
    sensor_count: int = 24
    quality_observation_count: int = 30_000
    telemetry_count: int = 50_000
    event_hubs_count: int = 20_000
    quality_file_count: int = 6


def _json_line(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        for record in records:
            handle.write(_json_line(record))


def _timestamp(base: datetime, minutes: int) -> str:
    return (base + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def _validate_config(config: SyntheticDataConfig) -> None:
    positive_fields = asdict(config)
    if any(not isinstance(value, int) or value <= 0 for value in positive_fields.values()):
        raise ValueError("all synthetic dataset configuration values must be positive integers")
    if config.batch_count < 2:
        raise ValueError("batch_count must be at least two for bounded CDC changes")
    if config.quality_observation_count < 8:
        raise ValueError("quality_observation_count must be at least eight for defect injection")
    if config.telemetry_count < config.event_hubs_count:
        raise ValueError("telemetry_count must be greater than or equal to event_hubs_count")
    if config.quality_file_count > config.quality_observation_count:
        raise ValueError("quality_file_count cannot exceed quality_observation_count")


def _hash_files(root: Path) -> tuple[str, dict[str, str]]:
    digest = hashlib.sha256()
    file_hashes: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.name == "manifest.json":
            continue
        relative = path.relative_to(root).as_posix()
        content = path.read_bytes()
        file_hashes[relative] = hashlib.sha256(content).hexdigest()
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(content)
    return digest.hexdigest(), file_hashes


def generate_synthetic_dataset(root: Path, config: SyntheticDataConfig) -> dict[str, Any]:
    """Generate a deterministic, bounded dataset and its integrity manifest."""

    _validate_config(config)
    root.mkdir(parents=True, exist_ok=True)
    randomizer = random.Random(config.seed)
    base = datetime(2026, 7, 1, tzinfo=UTC)

    sites = [
        {
            "site_id": f"SITE-{index + 1:03d}",
            "site_name": f"Quality Manufacturing Site {index + 1:02d}",
            "region": ["Northeast", "Southeast", "Midwest", "West"][index % 4],
            "active": True,
        }
        for index in range(config.site_count)
    ]
    products = [
        {
            "product_id": f"PROD-{index + 1:03d}",
            "product_name": f"Critical Product {index + 1:02d}",
            "target_assay_pct": round(96.0 + (index % 8) * 0.5, 2),
            "temperature_limit_c": 8.0 if index % 3 else 25.0,
        }
        for index in range(config.product_count)
    ]
    batches = []
    for index in range(config.batch_count):
        manufactured_at = _timestamp(base, index * 90)
        batches.append(
            {
                "batch_id": f"BATCH-{index + 1:05d}",
                "site_id": sites[index % len(sites)]["site_id"],
                "product_id": products[index % len(products)]["product_id"],
                "lot_number": f"LOT-{2026}{index + 1:05d}",
                "manufactured_at": manufactured_at,
                "release_status": "RELEASED" if index % 11 else "REVIEW",
                "effective_at": manufactured_at,
                "sequence_number": 1,
                "schema_version": "1.0",
            }
        )

    sensors = [
        {
            "sensor_id": f"SENSOR-{index + 1:03d}",
            "site_id": sites[index % len(sites)]["site_id"],
            "sensor_type": "temperature" if index % 2 == 0 else "vibration",
            "unit": "C" if index % 2 == 0 else "mm/s",
        }
        for index in range(config.sensor_count)
    ]

    _write_jsonl(root / "reference" / "sites.jsonl", sites)
    _write_jsonl(root / "reference" / "products.jsonl", products)
    _write_jsonl(root / "reference" / "sensors.jsonl", sensors)
    _write_jsonl(root / "batch" / "batch_master.jsonl", batches)

    quality_records: list[dict[str, Any]] = []
    base_quality_count = config.quality_observation_count - 1
    test_types = ["assay", "purity", "moisture", "bioburden"]
    for index in range(base_quality_count):
        batch = batches[index % len(batches)]
        test_type = test_types[index % len(test_types)]
        expected_unit = "%" if test_type in {"assay", "purity", "moisture"} else "CFU/g"
        result = round(95.0 + randomizer.random() * 7.0, 4)
        record: dict[str, Any] = {
            "observation_id": f"OBS-{index + 1:07d}",
            "batch_id": batch["batch_id"],
            "site_id": batch["site_id"],
            "product_id": batch["product_id"],
            "test_type": test_type,
            "result_value": result,
            "unit": expected_unit,
            "spec_lower": 95.0,
            "spec_upper": 102.0,
            "sample_temperature_c": round(2.0 + randomizer.random() * 22.0, 3),
            "event_timestamp": _timestamp(base, index * 3),
            "source_system": "quality_lims_synthetic",
            "schema_version": "1.0",
        }
        if index == 0:
            record["observation_id"] = None
        elif index == 1:
            record["batch_id"] = "BATCH-UNKNOWN"
            record["site_id"] = "SITE-UNKNOWN"
        elif index == 2:
            record["event_timestamp"] = "2026-99-77T25:61:00Z"
        elif index == 3:
            record["sample_temperature_c"] = 145.0
        elif index == 4:
            record["unit"] = "degF"
        elif index == 5:
            record["analyst_shift"] = "night"
        quality_records.append(record)
    quality_records.append(dict(quality_records[6]))

    base_size, remainder = divmod(len(quality_records), config.quality_file_count)
    offset = 0
    for file_index in range(config.quality_file_count):
        size = base_size + (1 if file_index < remainder else 0)
        _write_jsonl(
            root / "quality" / f"quality_observations_{file_index + 1:02d}.jsonl",
            quality_records[offset : offset + size],
        )
        offset += size

    telemetry_records: list[dict[str, Any]] = []
    for index in range(config.telemetry_count - 1):
        sensor = sensors[index % len(sensors)]
        batch = batches[(index // 7) % len(batches)]
        is_temperature = index % 2 == 0
        record = {
            "event_id": f"EVT-{index + 1:08d}",
            "sensor_id": sensor["sensor_id"],
            "batch_id": batch["batch_id"],
            "site_id": sensor["site_id"],
            "metric_name": "temperature_c" if is_temperature else "vibration_mm_s",
            "value": round(
                3.0 + randomizer.random() * 24.0
                if is_temperature
                else 0.05 + randomizer.random() * 2.2,
                4,
            ),
            "unit": "C" if is_temperature else "mm/s",
            "event_ts": _timestamp(base, index),
            "sequence_number": index + 1,
            "firmware_version": f"3.2.{index % 4}",
            "source_system": "plant_sensor_synthetic",
            "schema_version": "1.0",
        }
        if index == 0:
            record["event_id"] = None
        elif index == 1:
            record["batch_id"] = None
        elif index == 2:
            record["site_id"] = "SITE-UNKNOWN"
        elif index == 3:
            record["event_ts"] = "2026-99-77T25:61:00Z"
        elif index == 4:
            record["value"] = 145.0
        elif index == 5:
            record["unit"] = "C"
        telemetry_records.append(record)
    telemetry_records.insert(7, dict(telemetry_records[6]))
    _write_jsonl(root / "telemetry" / "sensor_telemetry.jsonl", telemetry_records)
    _write_jsonl(
        root / "event_hubs" / "sensor_messages.jsonl",
        telemetry_records[: config.event_hubs_count],
    )

    cdc_count = max(2, min(config.batch_count, round(config.batch_count * 0.08)))
    cdc_records: list[dict[str, Any]] = []
    for index in range(cdc_count):
        batch = batches[index % len(batches)]
        cdc_records.append(
            {
                "event_id": f"CDC-{index + 1:05d}",
                "batch_id": batch["batch_id"],
                "operation": "UPDATE",
                "sequence_number": 2,
                "effective_at": _timestamp(base, 50_000 + index),
                "release_status": "RELEASED" if batch["release_status"] == "REVIEW" else "REVIEW",
                "source_system": "batch_erp_synthetic",
                "schema_version": "1.0",
            }
        )
    cdc_records[0]["sequence_number"] = 3
    cdc_records[0]["effective_at"] = _timestamp(base, 60_000)
    cdc_records[1]["batch_id"] = cdc_records[0]["batch_id"]
    cdc_records[1]["sequence_number"] = 2
    cdc_records[1]["effective_at"] = _timestamp(base, 55_000)
    _write_jsonl(root / "cdc" / "batch_change_events.jsonl", cdc_records)

    hard_failure = [
        {
            "observation_id": "HARD-FAIL-0001",
            "batch_id": batches[0]["batch_id"],
            "result_value": {"unexpected": "object_instead_of_number"},
            "event_timestamp": _timestamp(base, 70_000),
            "schema_version": "99.0-reserved-failure",
        }
    ]
    _write_jsonl(root / "hard_failure" / "reserved_schema_failure.jsonl", hard_failure)

    dataset_sha256, file_hashes = _hash_files(root)
    manifest: dict[str, Any] = {
        "schema": "part4-synthetic-dataset/v1",
        "seed": config.seed,
        "generated_at_utc": "2026-08-12T00:00:00Z",
        "config": asdict(config),
        "row_counts": {
            "sites": len(sites),
            "products": len(products),
            "batches": len(batches),
            "sensors": len(sensors),
            "quality_observations": len(quality_records),
            "telemetry": len(telemetry_records),
            "event_hubs_messages": config.event_hubs_count,
            "cdc_changes": len(cdc_records),
            "reserved_hard_failures": len(hard_failure),
        },
        "intentional_defects": {
            "duplicate_business_record": 1,
            "duplicate_event_id": 1,
            "null_business_key": 1,
            "missing_batch_id": 1,
            "unknown_foreign_key": 1,
            "unknown_site_id": 1,
            "malformed_timestamp": 2,
            "impossible_temperature": 2,
            "inconsistent_unit": 2,
            "out_of_order_cdc": 1,
            "schema_evolution_field": 1,
            "reserved_hard_failure": 1,
        },
        "dataset_sha256": dataset_sha256,
        "files": file_hashes,
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def summarize_dataset(root: Path) -> dict[str, Any]:
    """Return the stable summary used for test and run reconciliation."""

    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    return {
        "schema": manifest["schema"],
        "seed": manifest["seed"],
        "row_counts": manifest["row_counts"],
        "intentional_defects": manifest["intentional_defects"],
        "dataset_sha256": manifest["dataset_sha256"],
        "files": manifest["files"],
    }
