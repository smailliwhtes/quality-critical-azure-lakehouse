from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def spark():
    project_root = Path(__file__).resolve().parents[1]
    configured_java_home = os.environ.get("JAVA_HOME")
    java_home = Path(configured_java_home) if configured_java_home else next(
        (project_root / ".tools" / "java").glob("jdk-17*"), None
    )
    if java_home is None or not (java_home / "bin").is_dir():
        raise RuntimeError("JDK 17 is required through JAVA_HOME or .tools/java/jdk-17*")
    os.environ["JAVA_HOME"] = str(java_home)
    os.environ["PATH"] = f"{java_home / 'bin'}{os.pathsep}{os.environ['PATH']}"
    worker_python = Path(sys.executable)
    if os.name == "nt" and " " in str(worker_python) and hasattr(ctypes, "windll"):
        short_path = ctypes.create_unicode_buffer(4096)
        if ctypes.windll.kernel32.GetShortPathNameW(  # type: ignore[attr-defined]
            str(worker_python), short_path, len(short_path)
        ):
            worker_python = Path(short_path.value)
    os.environ["PYSPARK_PYTHON"] = str(worker_python)

    from pyspark.sql import SparkSession

    session = (
        SparkSession.builder.master("local[2]")
        .appName("quality-critical-azure-lakehouse-tests")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()
