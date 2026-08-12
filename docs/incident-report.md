# Incident report

## Scenario

The controlled incident introduces exactly one reserved source record whose `schema_version` is `99.0-reserved-failure`. A Lakeflow fail-on-violation expectation rejects the update so the project can prove diagnosis, focused repair, and idempotent recovery using the actual workload path.

## Clean baseline

The ten-task clean DAG completed successfully. Its receipt recorded all Bronze, Silver, SCD2, and Gold row counts; zero duplicate fact/KPI business keys; zero one-current-version violations; key aggregates; and six deterministic table content hashes.

## Observed symptom

The original incident attempt failed at `quality_gate`. Lakeflow identified `reserved_schema_contract`, the `part4_ops.silver.quality_observed` flow, and observation `HARD-FAIL-0001`. The real platform diagnostic is preserved in the public sanitized capture; presentation code did not simulate the failure.

## Root cause

The reserved input intentionally carries a schema version outside the accepted contract. The violation is isolated from ordinary invalid rows, which are expected to be measured or quarantined rather than fail the pipeline.

## Corrective action

The reserved incident file was removed from the active input and Lakeflow repair was invoked on the same job run. `bronze_batch` and its dependent quality, Silver/SCD2, Gold, validation, and receipt tasks ran a second attempt. Successful preflight, landing verification, and streaming Bronze work remained one-attempt tasks.

## Recovery validation

Recovery passed: expected and recovered row counts matched, duplicate business keys remained zero, the SCD2 current-version violation count remained zero, aggregates matched, and the clean and recovered canonical SHA-256 values were identical. This prevents a visually green repair from masking double processing.

## Evidence package

The final record pairs failed and repaired task captures with run receipts, UTC times, execution commit, diagnostic text, corrective action, validation output, and SHA-256 hashes. Raw platform captures remain private; only sanitized derivatives are public.

## Current evidence boundary

The deterministic incident fixture and local tests are `DEMONSTRATED`. The failed Lakeflow task, platform diagnostic, focused repair, attempt-count boundary, recovered row counts, duplicate checks, aggregate comparison, and clean-versus-recovered content hash are `VERIFIED`.

## Status

`VERIFIED`: the controlled failure and its recovery executed in the Trial workspace. Public run and receipt identifiers are sanitized; raw captures remain outside Git.
