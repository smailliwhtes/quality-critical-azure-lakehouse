from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_deploy_script_enforces_cost_gate_and_full_iac_sequence() -> None:
    script = (ROOT / "scripts/azure/deploy.ps1").read_text(encoding="utf-8")

    assert "PART4_BUDGET_USD" in script
    assert "cost-gate" in script
    assert "az provider register" in script
    assert "az deployment sub validate" in script
    assert "az deployment sub what-if" in script
    assert "az deployment sub create" in script
    assert "TRIAL_ONLY_NO_PAID_FALLBACK" in script


def test_teardown_script_is_exact_scoped_and_polls_authoritative_absence() -> None:
    script = (ROOT / "scripts/azure/teardown.ps1").read_text(encoding="utf-8")

    assert "rg-qcal-part4-dev" in script
    assert "rg-qcal-part4-dbx-managed" in script
    assert "az group delete" in script
    assert "az consumption budget delete" in script
    assert "while" in script
    assert "Get-Az" not in script
    assert "*part4*" not in script


def test_deploy_workflow_exposes_only_approved_operations() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8"))
    inputs = workflow[True]["workflow_dispatch"]["inputs"]

    assert inputs["operation"]["options"] == ["deploy-run-collect", "teardown"]
    assert workflow["permissions"] == {"contents": "read", "id-token": "write"}
    assert "databricks/setup-cli@v1.11.0" in str(workflow)
    assert "actions/upload-artifact@v4" in str(workflow)


def test_cost_snapshot_fails_truthfully_when_cost_api_is_unavailable() -> None:
    script = (ROOT / "scripts/azure/cost-snapshot.ps1").read_text(encoding="utf-8")

    assert "2025-03-01" in script
    assert "$LASTEXITCODE" in script
    assert "CURRENT COST SNAPSHOT" in script
    assert "PENDING BILLING SETTLEMENT" in script
    assert "ResourceGroupName" in script
    assert "identifiers_included" in script


def test_cloud_runner_configures_and_executes_every_required_path() -> None:
    script = (ROOT / "scripts/azure/configure-and-run.ps1").read_text(encoding="utf-8")

    required_fragments = {
        "Standard_DS3_v2",
        "LTS",
        "DATABRICKS_AZURE_RESOURCE_ID",
        "storage-credentials create",
        "external-locations create",
        "volumes create",
        "secrets create-scope",
        "pipeline create-run",
        "send-telemetry",
        "20000",
        "bundle validate",
        "bundle deploy",
        "part4_lakehouse_job",
        "jobs repair-run",
        "part4_performance_job",
        "cost-snapshot.ps1",
    }

    assert all(fragment in script for fragment in required_fragments)
    assert "EVENT_HUB_CONNECTION_STRING" in script
    assert "primaryConnectionString" in script
    assert "Write-Host $connection" not in script


def test_pages_workflow_publishes_only_validated_dist_artifact() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8"))
    jobs = workflow["jobs"]

    assert "build" in jobs and "deploy" in jobs
    assert "npm run check" in str(jobs["build"])
    assert "portfolio/site/dist" in str(jobs["build"])
