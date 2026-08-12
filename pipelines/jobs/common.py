"""Small shared helpers used by the Lakeflow Jobs entrypoints."""

from __future__ import annotations

import json
import sys
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

from pyspark.sql import SparkSession

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from qcal.benchmark import run_benchmark_comparison  # noqa: E402, F401
from qcal.schemas import (  # noqa: E402, F401
    BATCH_MASTER_SCHEMA,
    CDC_EVENT_SCHEMA,
    PRODUCT_SCHEMA,
    QUALITY_SOURCE_SCHEMA,
    SITE_SCHEMA,
)
from qcal.transforms import build_gold_tables, build_scd2_history  # noqa: E402, F401

spark = SparkSession.builder.getOrCreate()
try:
    from pyspark.dbutils import DBUtils

    dbutils = DBUtils(spark)
except ImportError:
    dbutils = None


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def volume_path(catalog: str, volume: str, relative: str = "") -> str:
    base = f"/Volumes/{catalog}/governance/{volume}"
    return f"{base}/{relative.lstrip('/')}" if relative else base


def task_run_id() -> str:
    if dbutils is None:
        return "unknown-run"
    try:
        context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        return context.currentRunId().getOrElse("unknown-run")
    except Exception:
        return "unknown-run"


def set_task_value(key: str, value) -> None:
    if dbutils is None:
        return
    with suppress(Exception):
        dbutils.jobs.taskValues.set(key=key, value=value)


def put_json(path: str, payload: dict) -> None:
    if dbutils is None:
        raise RuntimeError("Databricks utilities are required to persist governed evidence")
    dbutils.fs.put(path, json.dumps(payload, indent=2, sort_keys=True), True)
