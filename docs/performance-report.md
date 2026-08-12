# Performance report

## Question

Does broadcasting a genuinely small dimension and removing unnecessary repartitioning improve the measured behavior of a deliberately skewed five-million-row Spark workload on fixed compute?

## Fixture

The benchmark is separate from the business dataset. It generates five million deterministic fact rows, a 25-row dimension, and at least 80 percent concentration on the hot key. This creates an honest performance surface without implying that the small portfolio business fixture is big data.

## Controlled comparison

Baseline and optimized paths use the same input, cache state, runtime, worker count, node type, and configuration. Each path runs exactly three times. The report compares medians and does not select the best individual run.

## Baseline

The baseline applies an unnecessary 64-way repartition and a shuffle-hash join. Its three wall times were 5.124889, 2.323782, and 2.239244 seconds. The median was 2.323782 seconds.

## Optimization

The optimized path removes the needless repartition and explicitly broadcasts the 25-row dimension. Its three wall times were 3.525856, 3.126520, and 3.230257 seconds. The median was 3.230257 seconds. All six executions produced the same result SHA-256.

## Interpretation rule

No improvement percentage is written in advance. If wall time is unchanged or worse, the result is retained. If shuffle or task behavior improves without a wall-time improvement, the report states only that narrower outcome.

## Reproduction

`src/qcal/benchmark.py` contains fixture and measurement logic. `pipelines/jobs/performance_benchmark.py` ran all six comparisons on the same single-node `Standard_D4ads_v6` cluster with Databricks Runtime `17.3.x-scala2.13`.

## Metric availability

Databricks Runtime 17.3 executed Python tasks through Spark Connect in this access mode. The classic Spark status store was not exposed, so jobs, stages, tasks, shuffle read/write, spill, partition count, maximum task duration, and p75 task duration are `null` in the receipt and labeled `NOT EXPOSED` in the visuals. They are not estimated. Wall time, join strategy, physical-plan hashes, output row count, and result hash were available for every run.

## Current evidence boundary

Fixture determinism and local compatibility tests are `DEMONSTRATED`. The five-million-row Trial executions, three-by-three medians, shuffle-versus-broadcast plan distinction, and result-hash equality are `VERIFIED`. Classic status-store metrics are explicitly unavailable under the executed Spark Connect runtime.

## Measured result

The broadcast implementation was **39.009 percent slower** by median wall time than the shuffle-hash baseline on this bounded single-node workload. The intended optimization therefore did not improve runtime. The result is published because the experiment was controlled and the outputs matched, not because it produced a favorable number.
