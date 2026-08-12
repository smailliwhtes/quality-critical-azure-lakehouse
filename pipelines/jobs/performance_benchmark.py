"""Run three baseline and three optimized Spark executions on identical compute."""

import argparse

from common import (
    put_json,
    run_benchmark_comparison,
    spark,
    task_run_id,
    utc_now,
    volume_path,
)

parser = argparse.ArgumentParser()
parser.add_argument("--catalog", required=True)
parser.add_argument("--row-count", type=int, required=True)
parser.add_argument("--iterations", type=int, choices=[3], required=True)
parser.add_argument("--partition-count", type=int, required=True)
parser.add_argument("--execution-commit", required=True)
args = parser.parse_args()

receipt = run_benchmark_comparison(
    spark,
    row_count=args.row_count,
    dimension_size=25,
    partition_count=args.partition_count,
    iterations=args.iterations,
)
receipt["run_id"] = task_run_id()
receipt["execution_commit"] = args.execution_commit
receipt["runtime"] = spark.conf.get(
    "spark.databricks.clusterUsageTags.sparkVersion", spark.version
)
receipt["persisted_at_utc"] = utc_now()
put_json(
    volume_path(args.catalog, "evidence", f"performance/{receipt['run_id']}.json"),
    receipt,
)
