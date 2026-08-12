"""Command-line entrypoints for local generation and release gates."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qcal.evidence import load_manifest, validate_manifest
from qcal.gates import evaluate_cost_gate
from qcal.producer import emit_bounded_telemetry
from qcal.synthetic import SyntheticDataConfig, generate_synthetic_dataset


def _command_output(command: list[str], *, cwd: Path) -> tuple[bool, str]:
    resolved_command = list(command)
    if os.name == "nt":
        command_script = shutil.which(f"{command[0]}.cmd")
        if command_script:
            resolved_command = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", command_script]
            resolved_command.extend(command[1:])
    try:
        completed = subprocess.run(
            resolved_command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "unavailable"
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return completed.returncode == 0, output[0].strip() if output else "available"


def _portable_executable(root: Path, relative_glob: str, fallback: str) -> str:
    matches = sorted(root.glob(relative_glob))
    return str(matches[0]) if matches else fallback


def build_preflight_receipt(root: Path) -> dict[str, Any]:
    """Collect a sanitized tool and authentication readiness receipt."""

    java = _portable_executable(root, ".tools/java/jdk-17*/bin/java.exe", "java")
    databricks = _portable_executable(root, ".tools/databricks/databricks.exe", "databricks")
    commands = {
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
        "python": [sys.executable, "--version"],
        "java": [java, "-version"],
        "azure_cli": ["az", "--version"],
        "bicep": ["az", "bicep", "version"],
        "databricks_cli": [databricks, "version"],
        "git": ["git", "--version"],
        "github_cli": ["gh", "--version"],
    }
    tools = {}
    for name, command in commands.items():
        available, version = _command_output(command, cwd=root)
        tools[name] = {"available": available, "version": version}

    azure_ready, _ = _command_output(
        ["az", "account", "show", "--query", "state", "-o", "tsv"], cwd=root
    )
    github_ready, _ = _command_output(["gh", "auth", "status"], cwd=root)
    git_identity_ready, _ = _command_output(["git", "config", "user.name"], cwd=root)
    return {
        "schema": "part4-preflight-receipt/v1",
        "captured_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "project": "quality-critical-azure-lakehouse",
        "region": "eastus2",
        "trial_policy": "TRIAL_ONLY_NO_PAID_FALLBACK",
        "cost_policy_usd": {"target": 10, "retry_stop": 15, "teardown": 20},
        "tools": tools,
        "authentication": {
            "azure_cli_ready": azure_ready,
            "github_cli_ready": github_ready,
            "configured_git_identity_present": git_identity_ready,
            "long_lived_cloud_secret_required": False,
        },
        "sanitization": {
            "subscription_id_included": False,
            "tenant_id_included": False,
            "email_included": False,
            "token_or_secret_included": False,
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qcal")
    subcommands = parser.add_subparsers(dest="command", required=True)

    generate = subcommands.add_parser("generate-data")
    generate.add_argument("--output", type=Path, default=Path("data/synthetic"))

    gate = subcommands.add_parser("cost-gate")
    gate.add_argument("--current-cost", required=True)
    gate.add_argument("--budget", default=None)

    validate = subcommands.add_parser("validate-evidence")
    validate.add_argument(
        "--manifest", type=Path, default=Path("evidence/public/evidence_manifest.json")
    )

    preflight = subcommands.add_parser("preflight")
    preflight.add_argument(
        "--output", type=Path, default=Path("evidence/public/receipts/preflight.json")
    )

    produce = subcommands.add_parser("send-telemetry")
    produce.add_argument(
        "--source", type=Path, default=Path("data/synthetic/event_hubs/sensor_messages.jsonl")
    )
    produce.add_argument("--event-hub-name", default="quality-telemetry")
    produce.add_argument("--message-limit", type=int, default=20_000)
    produce.add_argument(
        "--receipt", type=Path, default=Path("evidence/private/streaming-producer.json")
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path.cwd()
    if args.command == "generate-data":
        manifest = generate_synthetic_dataset(args.output, SyntheticDataConfig())
        print(json.dumps({"output": str(args.output), "summary": manifest["row_counts"]}, indent=2))
        return 0
    if args.command == "cost-gate":
        budget = args.budget if args.budget is not None else os.getenv("PART4_BUDGET_USD")
        decision = evaluate_cost_gate(
            raw_budget=budget, current_cost=args.current_cost, allow_default=budget is None
        )
        print(json.dumps(asdict(decision), default=str, indent=2))
        return 0 if decision.allowed else 2
    if args.command == "validate-evidence":
        validate_manifest(load_manifest(args.manifest))
        print(f"Validated {args.manifest}")
        return 0
    if args.command == "preflight":
        receipt = build_preflight_receipt(root)
        _write_json(args.output, receipt)
        print(f"Wrote {args.output}")
        return 0
    if args.command == "send-telemetry":
        connection_string = os.getenv("EVENT_HUB_CONNECTION_STRING", "")
        receipt = emit_bounded_telemetry(
            connection_string=connection_string,
            event_hub_name=args.event_hub_name,
            source_path=args.source,
            message_limit=args.message_limit,
            receipt_path=args.receipt,
        )
        print(
            json.dumps(
                {
                    "events_emitted": receipt["events_emitted"],
                    "receipt": str(args.receipt),
                },
                indent=2,
            )
        )
        return 0
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
