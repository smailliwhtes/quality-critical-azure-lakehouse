from qcal.benchmark import (
    DEFAULT_PERFORMANCE_ROWS,
    build_performance_fixture,
    build_performance_queries,
    run_benchmark_comparison,
)
from qcal.transforms import dataframe_content_hash


def test_performance_fixture_is_separate_five_million_row_contract() -> None:
    assert DEFAULT_PERFORMANCE_ROWS == 5_000_000


def test_fixture_is_deterministic_skewed_and_has_small_dimension(spark) -> None:
    fact, dimension = build_performance_fixture(spark, row_count=10_000, dimension_size=25)
    first_skew = fact.filter("join_key = 0").count() / fact.count()
    second_fact, _ = build_performance_fixture(spark, row_count=10_000, dimension_size=25)

    assert fact.count() == 10_000
    assert dimension.count() == 25
    assert first_skew >= 0.80
    assert dataframe_content_hash(fact.limit(100), ["record_id"]) == dataframe_content_hash(
        second_fact.limit(100), ["record_id"]
    )


def test_baseline_and_optimized_queries_return_identical_results(spark) -> None:
    fact, dimension = build_performance_fixture(spark, row_count=20_000, dimension_size=25)
    baseline, optimized = build_performance_queries(fact, dimension, partition_count=8)

    assert dataframe_content_hash(baseline, ["join_key"]) == dataframe_content_hash(
        optimized, ["join_key"]
    )
    optimized.collect()
    assert "BroadcastHashJoin" in optimized._jdf.queryExecution().executedPlan().toString()


def test_benchmark_records_three_runs_per_mode_and_median_metrics(spark) -> None:
    receipt = run_benchmark_comparison(
        spark,
        row_count=20_000,
        dimension_size=25,
        partition_count=8,
        iterations=3,
    )

    assert len(receipt["runs"]["baseline"]) == 3
    assert len(receipt["runs"]["optimized"]) == 3
    assert receipt["result_hashes_match"] is True
    assert receipt["comparison"]["baseline_median_wall_time_seconds"] > 0
    assert receipt["comparison"]["optimized_median_wall_time_seconds"] > 0
    assert all("shuffle_read_bytes" in run for run in receipt["runs"]["baseline"])
    assert all("p75_task_duration_ms" in run for run in receipt["runs"]["optimized"])
