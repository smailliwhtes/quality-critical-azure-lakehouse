"""Deterministic Spark fixture for an honest skew and broadcast comparison."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import time
from contextlib import suppress
from datetime import UTC, datetime

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

DEFAULT_PERFORMANCE_ROWS = 5_000_000
DEFAULT_DIMENSION_SIZE = 25


def build_performance_fixture(
    spark: SparkSession,
    *,
    row_count: int = DEFAULT_PERFORMANCE_ROWS,
    dimension_size: int = DEFAULT_DIMENSION_SIZE,
    partition_count: int = 32,
) -> tuple[DataFrame, DataFrame]:
    """Create a reproducible fact-like DataFrame with an intentionally skewed key."""

    if row_count <= 0 or dimension_size <= 1 or partition_count <= 0:
        raise ValueError("row_count, dimension_size, and partition_count must be positive")
    skew_boundary = int(row_count * 0.80)
    fact = (
        spark.range(0, row_count, 1, partition_count)
        .withColumnRenamed("id", "record_id")
        .withColumn(
            "join_key",
            F.when(F.col("record_id") < skew_boundary, F.lit(0)).otherwise(
                F.pmod(F.col("record_id"), F.lit(dimension_size))
            ),
        )
        .withColumn("measure_units", F.pmod(F.xxhash64("record_id"), F.lit(10_000)))
        .withColumn(
            "reporting_date",
            F.date_add(
                F.lit("2026-07-01").cast("date"),
                F.pmod("record_id", F.lit(30)).cast("int"),
            ),
        )
    )
    dimension = spark.range(dimension_size).select(
        F.col("id").cast("long").alias("join_key"),
        F.concat(F.lit("Product line "), F.lpad((F.col("id") + 1).cast("string"), 2, "0")).alias(
            "product_line"
        ),
        F.when(F.col("id") == 0, F.lit("dominant")).otherwise(F.lit("standard")).alias(
            "distribution_class"
        ),
    )
    return fact, dimension


def _aggregate(joined: DataFrame) -> DataFrame:
    return joined.groupBy("join_key", "product_line", "distribution_class").agg(
        F.count("record_id").alias("record_count"),
        F.sum("measure_units").alias("measure_units_total"),
        F.min("reporting_date").alias("first_reporting_date"),
        F.max("reporting_date").alias("last_reporting_date"),
    )


def build_performance_queries(
    fact: DataFrame, dimension: DataFrame, *, partition_count: int = 64
) -> tuple[DataFrame, DataFrame]:
    """Return equivalent baseline and justified broadcast implementations."""

    baseline_join = fact.repartition(partition_count, "join_key").join(
        dimension.hint("shuffle_hash"), "join_key"
    )
    optimized_join = fact.join(F.broadcast(dimension), "join_key")
    return _aggregate(baseline_join), _aggregate(optimized_join)


def _canonical_result_hash(rows: list) -> str:
    records = [row.asDict(recursive=True) for row in rows]
    records.sort(key=lambda record: (record["join_key"], record["product_line"]))
    payload = json.dumps(records, default=str, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _nearest_rank(values: list[int], quantile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[index]


def _runtime_conf_value(spark: SparkSession, key: str, default: str) -> str:
    """Read a SQL setting through both classic Spark and Spark Connect."""

    return spark.conf.get(key, default)


def _query_plan_text(query: DataFrame) -> str:
    """Return a physical-plan representation without requiring a JVM handle."""

    try:
        return query._jdf.queryExecution().executedPlan().toString()
    except Exception:
        try:
            return query._explain_string(mode="formatted")
        except Exception:
            return "PLAN_NOT_EXPOSED_BY_RUNTIME"


def _query_partition_count(query: DataFrame) -> int | None:
    """Return output partitions when the runtime exposes the classic RDD bridge."""

    try:
        return query.rdd.getNumPartitions()
    except Exception:
        return None


def _spark_stage_metrics(spark: SparkSession, job_group: str) -> dict[str, int | None]:
    metrics: dict[str, int | None] = {
        "job_count": None,
        "stage_count": None,
        "task_count": None,
        "shuffle_read_bytes": None,
        "shuffle_write_bytes": None,
        "memory_bytes_spilled": None,
        "disk_bytes_spilled": None,
        "maximum_task_duration_ms": None,
        "p75_task_duration_ms": None,
    }
    task_durations: list[int] = []
    try:
        context = spark.sparkContext
        tracker = context.statusTracker()
        job_ids = tracker.getJobIdsForGroup(job_group)
        stage_ids = sorted(
            {
                stage_id
                for job_id in job_ids
                for stage_id in list(tracker.getJobInfo(job_id).stageIds)
            }
        )
        metrics.update(
            {
                "job_count": len(job_ids),
                "stage_count": 0,
                "task_count": 0,
                "shuffle_read_bytes": 0,
                "shuffle_write_bytes": 0,
                "memory_bytes_spilled": 0,
                "disk_bytes_spilled": 0,
            }
        )
        store = context._jsc.sc().statusStore()
        empty_statuses = context._jvm.java.util.Collections.emptyList()
        empty_quantiles = context._gateway.new_array(context._jvm.double, 0)
        for stage_id in stage_ids:
            stage_sequence = store.stageData(
                stage_id, False, empty_statuses, False, empty_quantiles
            )
            if stage_sequence.size() == 0:
                continue
            stage = stage_sequence.apply(stage_sequence.size() - 1)
            attempt_id = int(stage.attemptId())
            metrics["stage_count"] = int(metrics["stage_count"] or 0) + 1
            metrics["task_count"] = int(metrics["task_count"] or 0) + int(stage.numTasks())
            for field, method in [
                ("shuffle_read_bytes", "shuffleReadBytes"),
                ("shuffle_write_bytes", "shuffleWriteBytes"),
                ("memory_bytes_spilled", "memoryBytesSpilled"),
                ("disk_bytes_spilled", "diskBytesSpilled"),
            ]:
                metrics[field] = int(metrics[field] or 0) + int(getattr(stage, method)())
            tasks = store.taskList(stage_id, attempt_id, 1_000_000)
            for index in range(tasks.size()):
                duration = tasks.apply(index).duration()
                if duration is not None:
                    task_durations.append(int(duration))
    except Exception:
        return metrics
    metrics["maximum_task_duration_ms"] = max(task_durations) if task_durations else None
    metrics["p75_task_duration_ms"] = _nearest_rank(task_durations, 0.75)
    return metrics


def _execute_measured_query(
    spark: SparkSession, query: DataFrame, *, mode: str, iteration: int
) -> dict[str, object]:
    job_group = f"part4-benchmark-{mode}-{iteration}-{time.time_ns()}"
    with suppress(Exception):
        spark.sparkContext.setJobGroup(job_group, job_group, interruptOnCancel=True)
    started = time.perf_counter()
    rows = query.collect()
    wall_time = time.perf_counter() - started
    plan = _query_plan_text(query)
    stage_metrics = _spark_stage_metrics(spark, job_group)
    return {
        "mode": mode,
        "iteration": iteration,
        "wall_time_seconds": round(wall_time, 6),
        "partition_count": _query_partition_count(query),
        "result_row_count": len(rows),
        "result_sha256": _canonical_result_hash(rows),
        "physical_plan_sha256": hashlib.sha256(plan.encode()).hexdigest(),
        "join_strategy": "BROADCAST" if "BroadcastHashJoin" in plan else "SHUFFLE",
        **stage_metrics,
    }


def run_benchmark_comparison(
    spark: SparkSession,
    *,
    row_count: int = DEFAULT_PERFORMANCE_ROWS,
    dimension_size: int = DEFAULT_DIMENSION_SIZE,
    partition_count: int = 64,
    iterations: int = 3,
) -> dict[str, object]:
    """Run three baseline and three optimized executions on the same cached fixture."""

    if iterations != 3:
        raise ValueError("benchmark contract requires exactly three executions per mode")
    original_aqe = _runtime_conf_value(spark, "spark.sql.adaptive.enabled", "true")
    original_broadcast = _runtime_conf_value(
        spark, "spark.sql.autoBroadcastJoinThreshold", "10485760"
    )
    spark.conf.set("spark.sql.adaptive.enabled", "false")
    spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
    fact, dimension = build_performance_fixture(
        spark,
        row_count=row_count,
        dimension_size=dimension_size,
        partition_count=partition_count,
    )
    fact = fact.cache()
    dimension = dimension.cache()
    fact.count()
    dimension.count()
    runs: dict[str, list[dict[str, object]]] = {"baseline": [], "optimized": []}
    try:
        for mode in ["baseline", "optimized"]:
            for iteration in range(1, iterations + 1):
                baseline, optimized = build_performance_queries(
                    fact, dimension, partition_count=partition_count
                )
                query = baseline if mode == "baseline" else optimized
                runs[mode].append(
                    _execute_measured_query(spark, query, mode=mode, iteration=iteration)
                )
    finally:
        fact.unpersist()
        dimension.unpersist()
        spark.conf.set("spark.sql.adaptive.enabled", original_aqe)
        spark.conf.set("spark.sql.autoBroadcastJoinThreshold", original_broadcast)

    baseline_wall = [float(run["wall_time_seconds"]) for run in runs["baseline"]]
    optimized_wall = [float(run["wall_time_seconds"]) for run in runs["optimized"]]
    result_hashes = {
        str(run["result_sha256"]) for mode_runs in runs.values() for run in mode_runs
    }
    baseline_median = statistics.median(baseline_wall)
    optimized_median = statistics.median(optimized_wall)
    return {
        "schema": "part4-spark-performance-comparison/v1",
        "captured_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "fixture": {
            "row_count": row_count,
            "dimension_size": dimension_size,
            "deliberately_skewed_key": 0,
            "minimum_skew_fraction": 0.80,
            "partition_count": partition_count,
        },
        "runs": runs,
        "result_hashes_match": len(result_hashes) == 1,
        "comparison": {
            "baseline_median_wall_time_seconds": baseline_median,
            "optimized_median_wall_time_seconds": optimized_median,
            "measured_wall_time_change_percent": round(
                ((optimized_median - baseline_median) / baseline_median) * 100.0, 3
            ),
            "interpretation": "MEASURED_WITHOUT_PREDETERMINED_OUTCOME",
        },
    }
