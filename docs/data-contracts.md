# Data contracts

## Deterministic source contract

All fixtures use seed `20260812`. The business set contains 12 sites, 20 products, 600 batches, 24 sensors, 30,000 quality observations, 50,000 retained telemetry records, 20,000 bounded streaming messages, 48 CDC changes, and one reserved hard-failure row. `data/synthetic/manifest.json` records row counts and file hashes.

## Bronze contract

Bronze preserves the received payload and adds `source_file`, `source_system`, `ingested_at_utc`, `event_ts`, `pipeline_run_id`, `record_hash`, and `schema_version`. Bronze does not silently convert invalid records into business-ready data.

## Silver contract

Silver quality rows require valid event, batch, site, product, characteristic, value, unit, result, and observation time fields. Telemetry requires event, sensor, batch, site, timestamp, numeric value, and supported unit fields. Units are standardized, business keys are checked against reference data, duplicate event identities are prevented, and invalid records are routed with stable reason codes.

## Temporal contract

`batch_history_scd2` preserves effective start and end, ordered changes, and a boolean current marker. Every business key must have at most one current version. The current table selects the latest valid change without discarding history.

## Gold contracts

| Object | Grain | Business key |
| --- | --- | --- |
| `fact_batch_quality` | One batch-characteristic observation time | event identity |
| `fact_cold_chain_excursion` | One batch-sensor excursion interval | batch, sensor, interval start |
| `dim_batch_history` | One effective-dated batch version | batch, effective start |
| `dim_site` | One site | site ID |
| `dim_product` | One product | product ID |
| `kpi_quality_summary` | One site-product-reporting date | site, product, reporting date |

Executable key, grain, lineage, and aggregate checks live in `sql/gold/validate_gold.sql`. The YAML contract is the human-readable companion.

## Schema evolution

One optional field demonstrates additive evolution. Unknown or incompatible changes are not accepted silently. The reserved `schema_version = 99.0-reserved-failure` record exists only for the controlled fail-on-violation scenario.

## Current evidence boundary

Generation hashes, schemas, transformations, quarantine routing, temporal invariants, Gold grains, and local Spark integration behavior are `DEMONSTRATED`. Catalog table schemas and Azure execution counts remain `PRODUCTION_BLUEPRINT` until live validation receipts exist.
