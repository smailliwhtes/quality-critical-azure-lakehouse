import copy
import json
from pathlib import Path

import pytest

from qcal.evidence import load_manifest, validate_manifest

REQUIRED_ARTIFACT_FIELDS = {
    "artifact_id",
    "claim",
    "status",
    "service",
    "captured_at_utc",
    "screenshot",
    "receipt",
    "code_path",
    "validation",
    "run_id",
    "commit_sha",
    "sha256",
    "notes",
    "limitation",
}


def test_public_manifest_uses_v1_contract_and_exact_status_vocabulary() -> None:
    manifest = load_manifest(Path("evidence/public/evidence_manifest.json"))
    content = json.loads(Path("portfolio/content/project.json").read_text(encoding="utf-8"))

    validate_manifest(manifest)
    assert manifest["schema"] == "part4-evidence-manifest/v1"
    assert manifest["status_vocabulary"] == [
        "VERIFIED",
        "DEMONSTRATED",
        "PRODUCTION_BLUEPRINT",
    ]
    assert manifest["artifacts"]
    assert len(manifest["artifacts"]) == 19
    assert [artifact["artifact_id"] for artifact in manifest["artifacts"]] == [
        item["id"] for item in content["engineering_journey"]
    ]
    assert all(artifact.keys() >= REQUIRED_ARTIFACT_FIELDS for artifact in manifest["artifacts"])


def test_manifest_rejects_unapproved_public_status() -> None:
    manifest = load_manifest(Path("evidence/public/evidence_manifest.json"))
    invalid = copy.deepcopy(manifest)
    invalid["artifacts"][0]["status"] = "COMPLETE"

    with pytest.raises(ValueError, match="status"):
        validate_manifest(invalid)


def test_verified_claim_requires_platform_code_receipt_validation_and_hash() -> None:
    manifest = load_manifest(Path("evidence/public/evidence_manifest.json"))
    invalid = copy.deepcopy(manifest)
    invalid["artifacts"][0]["status"] = "VERIFIED"
    invalid["artifacts"][0]["receipt"] = ""

    with pytest.raises(ValueError, match="receipt"):
        validate_manifest(invalid)
