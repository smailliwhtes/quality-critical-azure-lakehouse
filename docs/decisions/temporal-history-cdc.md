# Temporal History CDC

## Title

Use declarative temporal history with an honest fallback.

## Decision state

`ACCEPTED`

## Evidence state

`VERIFIED`

## Context

Batch lifecycle changes need effective-dated history rather than current-state overwrite or consumer-side reconstruction.

## Decision drivers / constraints

The executed path needed out-of-order change handling, SCD Type 2 output, and a truthful fallback boundary.

## Options considered

Lakeflow AUTO CDC, hand-coded Delta MERGE, overwrite current state, or append changes and make consumers rebuild history.

## Decision

Use Lakeflow AUTO CDC for the executed SCD Type 2 path and document deterministic Delta MERGE only as fallback.

## Why this option won

AUTO CDC reduced custom sequencing and history logic for the executed Databricks path.

## Trade-offs accepted

The executed path depends on Databricks declarative semantics.

## Consequences

The portfolio can claim 647 effective-dated SCD2 rows and the one-current-version invariant, while stating that MERGE was not executed.

## Executed evidence

The SCD2 screenshot, clean-run receipt, and integration tests support this decision.

## Production extension

Define portability, late-arriving change policy, retention, and fallback criteria.

## Reconsider when

Reconsider when portability away from Lakeflow becomes more important than reduced custom code.

## Current evidence boundary

This record does not claim that the Delta MERGE fallback was run.
