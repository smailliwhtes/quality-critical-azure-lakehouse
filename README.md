# Quality-Critical Azure Lakehouse

An end-to-end Azure Data Engineering evidence journey from scheduled batch files and bounded streaming telemetry to governed, testable data products.

The implementation is designed to answer four operational questions:

- Did each batch remain within quality and environmental limits?
- Which records failed validation, and why?
- What changed during the batch lifecycle?
- Can every published KPI be traced to source data and an executed pipeline?

## Engineering scope

`Bicep` · `ADLS Gen2` · `Azure Data Factory` · `Event Hubs` · `Azure Databricks` · `Unity Catalog` · `PySpark` · `Delta Lake` · `Lakeflow` · `Azure Monitor` · `GitHub Actions`

This repository uses one evidence manifest and one shared content model to drive the technical case study, architecture assets, execution receipts, tests, and LinkedIn document. Public claims use only three evidence states:

- `VERIFIED`: executed in the relevant Azure or Databricks environment and paired with sanitized evidence.
- `DEMONSTRATED`: executed deterministically outside the claimed cloud environment.
- `PRODUCTION_BLUEPRINT`: designed and documented but not executed in this portfolio environment.

## Current evidence boundary

Local deterministic generation, data contracts, cost gates, evidence-schema validation, and PySpark transformation contracts are implemented. Azure execution evidence will be promoted to `VERIFIED` only after the bounded Trial deployment, workload run, validation, capture, and teardown complete.

## Deterministic data product

Seed: `20260812`

| Domain | Rows |
| --- | ---: |
| Sites | 12 |
| Products | 20 |
| Batches | 600 |
| Sensors | 24 |
| Quality observations | 30,000 |
| Telemetry records | 50,000 |
| Bounded Event Hubs messages | 20,000 |
| CDC changes | 48 |
| Reserved hard failures | 1 |

The source fixture intentionally contains reproducible duplicates, null and unknown keys, malformed timestamps, impossible temperatures, inconsistent units, out-of-order CDC, one optional schema-evolution field, and one isolated hard-failure record. The complete row and file-hash contract is in [`data/synthetic/manifest.json`](data/synthetic/manifest.json).

## Lakehouse objects

| Layer | Objects |
| --- | --- |
| Bronze | `batch_quality_raw`, `batch_change_events`, `sensor_telemetry_raw` |
| Silver | `batch_quality_valid`, `sensor_telemetry_valid`, `batch_master_current`, `batch_history_scd2`, `quarantined_quality_records`, `quarantined_telemetry` |
| Gold | `fact_batch_quality`, `fact_cold_chain_excursion`, `dim_batch_history`, `dim_site`, `dim_product`, `kpi_quality_summary` |

Bronze preserves source fidelity and provenance. Silver applies explicit schema, validation, deduplication, quarantine, conformance, and temporal-history rules. Gold publishes documented business grains and validation queries.

## Cost and security gates

- Target incremental cost: under `$10`.
- Stop new compute and retries at `$15`.
- Tear down immediately at `$20`.
- Databricks policy: Trial only, with no paid Premium fallback.
- Authentication design: managed identities and federated CI identity; no long-lived cloud password or Databricks token.
- Public evidence excludes subscription IDs, tenant IDs, personal email addresses, secret values, connection strings, and storage keys.

## Local verification

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe --editable ".[dev]"
$env:PYTHONPATH = "src"
.venv/Scripts/python.exe -m pytest tests/unit -q
.venv/Scripts/python.exe -m pytest tests/integration -q
.venv/Scripts/ruff.exe check src tests
```

The final public release will add the recruiter-first site, searchable evidence explorer, 32-page LinkedIn document, cloud receipts, controlled failure and repair evidence, measured Spark comparison, monitoring and cost evidence, green CI, and authoritative teardown verification.

