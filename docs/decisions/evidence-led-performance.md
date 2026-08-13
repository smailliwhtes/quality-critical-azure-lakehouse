# Evidence-Led Performance

## Title

Measure performance instead of assuming optimization.

## Decision state

`ACCEPTED`

## Evidence state

`VERIFIED`

## Context

An optimization claim is useful only if the experiment could disprove it.

## Decision drivers / constraints

The benchmark needed a separate large fixture, identical compute, three runs per implementation, matching result hashes, and honest limitation handling.

## Options considered

Broadcast because the dimension is small, choose the fastest individual run, benchmark the small business dataset, or run a controlled comparison.

## Decision

Run a five-million-row fixture three times per implementation and publish the median comparison.

## Why this option won

It turns performance into a falsifiable claim.

## Trade-offs accepted

The test consumes time and can produce a negative result.

## Consequences

The broadcast plan was rejected because it was 39.009% slower on the executed workload, while result hashes matched.

## Executed evidence

The Spark performance receipt and comparison visual support this decision.

## Production extension

Add representative concurrency, task-level runtime telemetry, workload SLAs, and regression thresholds.

## Reconsider when

Reconsider whenever data size, skew, runtime, partitioning, topology, concurrency, or service objectives materially change.

## Current evidence boundary

The experiment establishes that the changed plan was slower here; it does not establish why because task-level metrics were unavailable.
