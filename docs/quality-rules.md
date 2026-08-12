# Quality rules

## Quality policy

Quality behavior is explicit at the rule level. A violation may produce a metric, route a record to quarantine, remove it from a trusted output, or fail the task. These outcomes are not interchangeable.

## Core rules

| Rule | Scope | Action |
| --- | --- | --- |
| `batch_id_not_null` | Quality and telemetry | Quarantine invalid record |
| `site_id_not_null` | Quality and telemetry | Quarantine invalid record |
| `event_ts_valid` | All events | Quarantine malformed timestamp |
| `business_key_known` | Quality and telemetry | Quarantine unknown reference |
| `temperature_range_valid` | Telemetry | Metric and quarantine impossible value |
| `unit_supported` | Quality and telemetry | Standardize supported units; quarantine otherwise |
| `event_identity_unique` | Events | Retain one deterministic winner and record duplicate |
| `quality_result_domain` | Quality | Quarantine result outside the supported domain |
| `hard_schema_contract` | Reserved incident input | Fail the real Lakeflow update |

## Defect coverage

The deterministic fixture contains duplicates, null business keys, unknown foreign keys, malformed timestamps, impossible temperatures, inconsistent units, out-of-order CDC, additive schema evolution, and one isolated hard failure. Tests assert the intentional defect counts so data generation cannot drift unnoticed.

## Quarantine contract

Quarantine retains the original payload, provenance, violated rules, stable reason codes, and ingestion context. Trusted Silver tables exclude quarantined records. Reruns must not create duplicate valid rows or duplicate quarantine identities.

## Lakeflow expectations

The pipeline definition includes warning metrics through `expect`, removal behavior through `expect_or_drop`, and the reserved incident through `expect_or_fail`. Quarantine tables preserve details independently of the trusted outputs.

## Validation

Local tests cover routing, types, keys, duplicate prevention, temporal invariants, Gold formulas, and rerun idempotency. Live validation will reconcile expected, accepted, rejected, and recovered counts with the Lakeflow event log.

## Current evidence boundary

Rule logic, deterministic defect counts, local Spark routing, and the Lakeflow expectation definitions are `DEMONSTRATED`. Actual expectation metrics and the real failed Trial update remain `PRODUCTION_BLUEPRINT` until captured from the platform.
