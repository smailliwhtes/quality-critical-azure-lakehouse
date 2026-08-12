import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_subscription_bicep_is_modular_trial_only_and_budget_first() -> None:
    main = (ROOT / "infra/main.bicep").read_text(encoding="utf-8")
    expected_modules = {
        "budget.bicep",
        "identities.bicep",
        "storage.bicep",
        "data-factory.bicep",
        "event-hubs.bicep",
        "key-vault.bicep",
        "access-connector.bicep",
        "databricks.bicep",
        "monitoring.bicep",
        "rbac.bicep",
    }

    assert "targetScope = 'subscription'" in main
    assert "rg-qcal-part4-dev" in main
    assert "PART4_BUDGET_USD" in main
    assert "budgetModule" in main
    assert all((ROOT / "infra/modules" / module).exists() for module in expected_modules)
    assert "TRIAL_ONLY_NO_PAID_FALLBACK" in main


def test_storage_event_hubs_and_databricks_security_contracts() -> None:
    storage = (ROOT / "infra/modules/storage.bicep").read_text(encoding="utf-8")
    event_hubs = (ROOT / "infra/modules/event-hubs.bicep").read_text(encoding="utf-8")
    databricks = (ROOT / "infra/modules/databricks.bicep").read_text(encoding="utf-8")

    assert "Standard_LRS" in storage
    assert "isHnsEnabled: true" in storage
    assert "minimumTlsVersion: 'TLS1_2'" in storage
    assert "allowBlobPublicAccess: false" in storage
    assert "name: 'Standard'" in event_hubs
    assert "capacity: 1" in event_hubs
    assert "isAutoInflateEnabled: false" in event_hubs
    assert "name: 'trial'" in databricks
    assert "premium" not in databricks.lower()


def test_adf_pipeline_uses_parameterized_foreach_copy_and_pinned_public_commit() -> None:
    pipeline = json.loads((ROOT / "adf/pipeline/pl_ingest_batch_quality.json").read_text())
    activities = pipeline["properties"]["activities"]
    loop = next(activity for activity in activities if activity["type"] == "ForEach")
    copy = next(
        activity
        for activity in loop["typeProperties"]["activities"]
        if activity["type"] == "Copy"
    )
    source_files = pipeline["properties"]["parameters"]["sourceFiles"]["defaultValue"]
    source_link = json.loads((ROOT / "adf/linkedService/ls_github_http.json").read_text())

    assert len(source_files) == 6
    assert all(path.startswith("quality_observations_") for path in source_files)
    assert copy["typeProperties"]["source"]["type"] == "JsonSource"
    assert copy["typeProperties"]["sink"]["type"] == "JsonSink"
    assert "8369011" in source_link["properties"]["typeProperties"]["url"]


def test_bundle_defines_exact_professional_jobs_dag() -> None:
    bundle = yaml.safe_load((ROOT / "databricks.yml").read_text(encoding="utf-8"))
    job = bundle["resources"]["jobs"]["part4_lakehouse_job"]
    tasks = {task["task_key"]: task for task in job["tasks"]}
    expected = {
        "preflight",
        "verify_batch_landing",
        "bronze_batch",
        "bronze_stream",
        "quality_gate",
        "silver_transform",
        "scd2_history",
        "gold_publish",
        "validation",
        "evidence_receipt",
    }

    assert set(tasks) == expected
    assert {item["task_key"] for item in tasks["quality_gate"]["depends_on"]} == {
        "bronze_batch",
        "bronze_stream",
    }
    assert {item["task_key"] for item in tasks["gold_publish"]["depends_on"]} == {
        "silver_transform",
        "scd2_history",
    }
    assert job["job_clusters"][0]["new_cluster"]["num_workers"] == 1
    assert job["job_clusters"][0]["new_cluster"]["node_type_id"] == "${var.node_type_id}"
    assert bundle["variables"]["node_type_id"]["default"] == "Standard_E4as_v4"
    assert job["job_clusters"][0]["new_cluster"]["worker_node_type_flexibility"] == {
        "alternate_node_type_ids": ["Standard_E4ds_v4"]
    }


def test_bundle_has_same_compute_three_by_three_performance_job() -> None:
    bundle = yaml.safe_load((ROOT / "databricks.yml").read_text(encoding="utf-8"))
    job = bundle["resources"]["jobs"]["part4_performance_job"]
    cluster = job["job_clusters"][0]["new_cluster"]
    parameters = job["tasks"][0]["spark_python_task"]["parameters"]

    assert cluster["node_type_id"] == "${var.node_type_id}"
    assert bundle["variables"]["node_type_id"]["default"] == "Standard_E4as_v4"
    assert cluster["driver_node_type_flexibility"] == {
        "alternate_node_type_ids": ["Standard_E4ds_v4"]
    }
    assert cluster["num_workers"] == 1
    assert "5000000" in parameters
    assert "3" in parameters
    assert (ROOT / "pipelines/jobs/performance_benchmark.py").exists()


def test_lakeflow_assets_define_warning_drop_quarantine_and_hard_failure() -> None:
    quality_pipeline = (ROOT / "pipelines/lakeflow/quality_pipeline.py").read_text(
        encoding="utf-8"
    )
    scd2_pipeline = (ROOT / "pipelines/lakeflow/scd2_auto_cdc.py").read_text(encoding="utf-8")

    assert "@dp.expect(" in quality_pipeline
    assert "@dp.expect_or_drop(" in quality_pipeline
    assert "@dp.expect_or_fail(" in quality_pipeline
    assert "quarantined_quality_records" in quality_pipeline
    assert "quarantined_telemetry" in quality_pipeline
    assert "99.0-reserved-failure" in quality_pipeline
    assert "UNKNOWN_BATCH" in quality_pipeline
    assert "INCONSISTENT_UNIT" in quality_pipeline
    assert "create_auto_cdc_flow" in scd2_pipeline
    assert "stored_as_scd_type=2" in scd2_pipeline


def test_job_entrypoints_are_present_and_keep_logic_in_reusable_modules() -> None:
    task_files = {
        "preflight.py",
        "verify_batch_landing.py",
        "bronze_batch.py",
        "bronze_stream.py",
        "silver_transform.py",
        "scd2_history.py",
        "gold_publish.py",
        "validation.py",
        "evidence_receipt.py",
    }

    for task_file in task_files:
        path = ROOT / "pipelines/jobs" / task_file
        assert path.exists()
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 180

    receipt = (ROOT / "pipelines/jobs/evidence_receipt.py").read_text(encoding="utf-8")
    assert "content_hashes" in receipt
    assert "duplicate_business_keys" in receipt


def test_each_gold_object_has_grain_and_validation_sql() -> None:
    contract = (ROOT / "sql/gold/table_contracts.yml").read_text(encoding="utf-8")
    validation = (ROOT / "sql/gold/validate_gold.sql").read_text(encoding="utf-8")
    gold_objects = {
        "fact_batch_quality",
        "fact_cold_chain_excursion",
        "dim_batch_history",
        "dim_site",
        "dim_product",
        "kpi_quality_summary",
    }

    assert all(f"{name}:" in contract for name in gold_objects)
    assert contract.count("grain:") == 6
    assert all(f"part4_ops.gold.{name}" in validation for name in gold_objects)
