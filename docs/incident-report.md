# Incident report

## Scenario

The controlled incident introduces exactly one reserved source record whose `schema_version` is `99.0-reserved-failure`. A Lakeflow fail-on-violation expectation rejects the update so the project can prove diagnosis, focused repair, and idempotent recovery using the actual workload path.

## Clean baseline

Before injection, the full DAG must complete and the validation task must record expected row counts, zero duplicate business keys, key aggregates, one-current-version SCD2 behavior, and deterministic content hashes.

## Expected symptom

The quality-gate update fails while previously successful landing and Bronze work remains identifiable. The platform diagnostic should name the violated hard schema contract and the affected component. No presentation artifact is accepted as a substitute for that diagnostic.

## Root cause

The reserved input intentionally carries a schema version outside the accepted contract. The violation is isolated from ordinary invalid rows, which are expected to be measured or quarantined rather than fail the pipeline.

## Corrective action

Remove or correct only the reserved incident input. Use Lakeflow repair to rerun the failed path without repeating successful upstream tasks when the Trial runtime exposes repair. If repair is unavailable, record that exact limitation and use the narrowest reproducible rerun.

## Recovery validation

Recovery passes only if expected and recovered row counts match, duplicate business keys equal zero, clean and recovered aggregates match, and deterministic content hashes reconcile. These checks prevent a visually green rerun from masking double processing.

## Evidence package

The final record pairs failed and repaired task captures with run receipts, UTC times, execution commit, diagnostic text, corrective action, validation output, and SHA-256 hashes. Raw platform captures remain private; only sanitized derivatives are public.

## Current evidence boundary

The reserved failure fixture, fail-on-violation code, baseline validation design, repair automation path, and idempotency tests are `DEMONSTRATED`. The failed and repaired platform runs remain `PRODUCTION_BLUEPRINT` until executed in the Trial workspace.

## Status

No failure, diagnostic, repair ID, or recovery metric is prefilled. The report is intentionally incomplete rather than fabricated before execution.
