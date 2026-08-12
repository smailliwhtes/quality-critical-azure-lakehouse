# Performance report

## Question

Does broadcasting a genuinely small dimension and removing unnecessary repartitioning improve the measured behavior of a deliberately skewed five-million-row Spark workload on fixed compute?

## Fixture

The benchmark is separate from the business dataset. It generates five million deterministic fact rows, a 25-row dimension, and at least 80 percent concentration on the hot key. This creates an honest performance surface without implying that the small portfolio business fixture is big data.

## Controlled comparison

Baseline and optimized paths use the same input, cache state, runtime, worker count, node type, and configuration. Each path runs exactly three times. The report compares medians and does not select the best individual run.

## Baseline

The baseline applies an unnecessary repartition and a non-broadcast join. Each run records wall time, jobs, stages, tasks, shuffle read and write, spill, partitions, maximum task duration, p75 task duration, physical-plan hash, and result hash.

## Optimization

The optimized path removes the needless repartition and explicitly broadcasts the 25-row dimension. Result hashes must match the baseline before any performance conclusion is accepted.

## Interpretation rule

No improvement percentage is written in advance. If wall time is unchanged or worse, the result is retained. If shuffle or task behavior improves without a wall-time improvement, the report states only that narrower outcome.

## Reproduction

`src/qcal/benchmark.py` contains fixture and measurement logic. `pipelines/jobs/performance_benchmark.py` runs it on the same `Standard_DS3_v2` driver plus one worker used by the bounded job configuration.

## Current evidence boundary

Fixture determinism, skew, equal result hashes, three-by-three execution logic, and local metric collection are `DEMONSTRATED`. The five-million-row Trial results and platform Spark UI evidence remain `PRODUCTION_BLUEPRINT` until executed.

## Measured result

`PENDING`: the final median table, percentage calculations, plan difference, and interpretation are generated only from the collected benchmark receipt.
