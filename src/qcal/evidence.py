"""Validation helpers for the single public evidence manifest."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SCHEMA_ID = "part4-evidence-manifest/v1"
STATUS_VOCABULARY = ["VERIFIED", "DEMONSTRATED", "PRODUCTION_BLUEPRINT"]
ARTIFACT_FIELDS = {
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
VERIFIED_FIELDS = [
    "screenshot",
    "receipt",
    "code_path",
    "validation",
    "run_id",
    "commit_sha",
    "sha256",
    "captured_at_utc",
]


def load_manifest(path: Path) -> dict[str, Any]:
    """Load a UTF-8 evidence manifest."""

    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    """Reject incomplete evidence and any public status outside the contract."""

    if manifest.get("schema") != SCHEMA_ID:
        raise ValueError(f"schema must be {SCHEMA_ID}")
    if manifest.get("status_vocabulary") != STATUS_VOCABULARY:
        raise ValueError("status_vocabulary must match the exact public contract")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("artifacts must be a non-empty list")

    artifact_ids: set[str] = set()
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, Mapping):
            raise ValueError(f"artifact {index} must be an object")
        missing = ARTIFACT_FIELDS.difference(artifact)
        if missing:
            raise ValueError(f"artifact {index} missing fields: {sorted(missing)}")
        artifact_id = artifact["artifact_id"]
        if not isinstance(artifact_id, str) or not artifact_id:
            raise ValueError(f"artifact {index} has invalid artifact_id")
        if artifact_id in artifact_ids:
            raise ValueError(f"duplicate artifact_id: {artifact_id}")
        artifact_ids.add(artifact_id)
        if artifact["status"] not in STATUS_VOCABULARY:
            raise ValueError(f"artifact {artifact_id} has invalid status")
        if artifact["status"] == "VERIFIED":
            for field in VERIFIED_FIELDS:
                if not isinstance(artifact[field], str) or not artifact[field].strip():
                    raise ValueError(f"VERIFIED artifact {artifact_id} requires {field}")
        if artifact["status"] == "PRODUCTION_BLUEPRINT" and not artifact["limitation"]:
            raise ValueError(f"PRODUCTION_BLUEPRINT artifact {artifact_id} requires limitation")

