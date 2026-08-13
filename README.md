# Quality-Critical Azure Lakehouse

From batch and streaming telemetry to governed data products. This is an evidence-led Azure Data Engineering case study in which infrastructure, transformations, orchestration, recovery, performance, governance, cost, and teardown are independently inspectable.

> I engineered a reproducible Azure lakehouse that makes ingestion, quality, history, orchestration, recovery, performance, governance, monitoring, cost, and teardown independently inspectable.

[View the recruiter case study](https://smailliwhtes.github.io/quality-critical-azure-lakehouse/) · [Download the 32-page portfolio document](https://smailliwhtes.github.io/quality-critical-azure-lakehouse/downloads/part4-azure-data-engineering-portfolio.pdf) · [Inspect the evidence manifest](evidence/public/evidence_manifest.json)

## Engineering scope

`Bicep infrastructure as code` · `ADLS Gen2 medallion storage` · `Azure Data Factory batch ingestion` · `Event Hubs bounded streaming` · `PySpark and Delta Lake transformations` · `Lakeflow pipelines and Jobs` · `Unity Catalog governance and lineage` · `CDC and SCD Type 2 history` · `Failure repair and idempotency proof` · `Spark performance measurement` · `Azure Monitor and Log Analytics` · `OIDC-based CI/CD and exact-scope teardown`

## Business problem

Operations leaders need one trustworthy path from batch quality observations and sensor telemetry to traceable decisions, without hiding rejected data, history, failures, or operating cost.

The implementation answers four operational questions:

- Did each batch remain within quality and environmental limits?
- Which records failed validation, and why?
- What changed during the batch lifecycle?
- Can every published KPI be traced to source data and an executed pipeline?

## Evidence contract

Public claims use exactly three states:

- `VERIFIED`: executed in the stated Azure or Databricks environment and paired with sanitized platform evidence.
- `DEMONSTRATED`: executed deterministically outside the claimed cloud environment or validated as an implementation artifact.
- `PRODUCTION_BLUEPRINT`: designed and documented but not executed in this bounded portfolio environment.

The source of truth is [`evidence/public/evidence_manifest.json`](evidence/public/evidence_manifest.json). Every major verified claim binds a platform capture, code path, machine receipt, validation result, UTC time, execution commit, and SHA-256 hash.

## Deterministic data product

Seed: `20260812`

| Domain | Rows |
| --- | ---: |
| Quality observations | 30,000 |
| Telemetry records | 50,000 |
| Stream messages | 20,000 |
| Batches | 600 |
| Sites | 12 |
| Products | 20 |
| CDC changes | 48 |
| Reserved hard failures | 1 |

The fixture includes controlled duplicates, null and unknown business keys, malformed timestamps, impossible temperatures, inconsistent units, out-of-order CDC, schema evolution, and one isolated hard contract failure. The complete file and hash contract is [`data/synthetic/manifest.json`](data/synthetic/manifest.json).

## Gold data products

| Object | Grain |
| --- | --- |
| `fact_batch_quality` | One quality measurement for one batch characteristic at one observation time |
| `fact_cold_chain_excursion` | One detected environmental excursion episode per batch and sensor interval |
| `dim_batch_history` | One effective-dated version of a batch lifecycle record |
| `dim_site` | One operating site |
| `dim_product` | One manufactured product |
| `kpi_quality_summary` | One site, product, and reporting date |

Every Gold object also declares keys, upstream lineage, and executable validation SQL in [`sql/gold/table_contracts.yml`](sql/gold/table_contracts.yml) and [`sql/gold/validate_gold.sql`](sql/gold/validate_gold.sql).

## Architecture

![Quality-Critical Azure Lakehouse architecture](portfolio/architecture/quality-critical-lakehouse.svg)

- Batch: deterministic files → Azure Data Factory → ADLS Gen2 landing → Bronze.
- Streaming: bounded producer → Event Hubs → Structured Streaming → checkpointed Bronze Delta.
- Processing: reusable PySpark → Silver validation and quarantine → CDC/SCD2 → Gold products.
- Control plane: managed identities, Access Connector, Unity Catalog, Key Vault, Monitor, Log Analytics, GitHub Actions, budgets, and teardown verification.

## Architecture decisions and trade-offs

| Architecture choice | Decision | Cost accepted |
| --- | --- | --- |
| [Split ingestion by workload shape](docs/decisions/batch-and-streaming-ingestion.md) | ADF owns bounded file movement while Event Hubs and Structured Streaming own event ingress; both paths converge in Bronze. | Two ingress control planes require more operational discipline than one, but they expose workload-appropriate metrics, offsets, file counts, row counts, and recovery state. |
| [Preserve source fidelity before conformance](docs/decisions/bronze-provenance.md) | Use an append-only, source-fidelity Bronze preservation contract with source identity, timestamps, run ID, record hash, and schema version. | More metadata and storage are retained, but audit, replay, incident diagnosis, and reproducibility become stronger. |
| [Apply risk-based quality policies](docs/decisions/quality-policy-routing.md) | Implement observe/allow, reason-coded quarantine, and hard fail as explicit business quality policies. | The policy needs more contract design and routing logic, but it avoids silent corruption and gratuitously brittle pipelines. |
| [Use declarative temporal history with an honest fallback](docs/decisions/temporal-history-cdc.md) | Use Lakeflow AUTO CDC for the executed SCD Type 2 path and keep deterministic Delta MERGE documented only as a fallback. | AUTO CDC reduces custom sequencing and SCD machinery, but it couples the executed history path to Databricks declarative semantics. |
| [Build governance into named table operations](docs/decisions/governed-table-operations.md) | Use catalog-qualified table operations, ownership, grants, comments, tags, masking, and Unity Catalog lineage for governed objects. | The design requires stronger namespace, ownership, and permission discipline, but it makes governance and lineage inspectable at runtime. |
| [Measure performance instead of assuming optimization](docs/decisions/evidence-led-performance.md) | Run a separate five-million-row fixture three times per implementation on the same compute and publish the median result. | Controlled benchmarking consumes time and may invalidate a design idea, but it prevents intuition from being presented as proof. |

The full decision dossier is [`docs/decisions/README.md`](docs/decisions/README.md). The public site renders the same six decisions immediately after the six-card recruiter path.

## Executed lifecycle

| # | Stage | Outcome | Evidence state |
| ---: | --- | --- | --- |
| 1 | Bound cost and identity | The build began with deterministic fixtures, cost stop rules, scoped identity, and fail-closed automation. | `VERIFIED` |
| 2 | Provision and reconcile Azure resources | Modular Bicep deployed the isolated Trial-only resource set and reconciled it against the expected inventory. | `VERIFIED` |
| 3 | Land batch files and stream telemetry | ADF landed six commit-pinned files while Event Hubs and Structured Streaming reconciled bounded telemetry. | `VERIFIED` |
| 4 | Preserve Bronze provenance and checkpoints | Source metadata, run identity, schema version, record hashes, streaming offsets, and checkpoints were retained before conformance. | `VERIFIED` |
| 5 | Conform, quarantine, and maintain history | Silver validation, reason-coded quarantine, fail-on-violation behavior, and AUTO CDC history created the analytical boundary. | `VERIFIED` |
| 6 | Publish governed Gold products and lineage | Six Gold products were published through catalog-qualified operations with grain, keys, validation SQL, and lineage. | `VERIFIED` |
| 7 | Inject failure, repair, and measure performance | A real hard quality failure was repaired with matching recovered hashes, and the proposed Spark optimization was rejected by measurement. | `VERIFIED` |
| 8 | Validate release and prove teardown | CI, Pages, evidence artifacts, PDF validation, and authoritative Azure absence closed the lifecycle. | `VERIFIED` |

## Production readiness

| Category | Executed proof | Production extension | Extension state |
| --- | --- | --- | --- |
| Network isolation | The bounded portfolio used isolated resource groups, scoped identities, disabled shared storage keys, and exact teardown scope. | Add private endpoints, firewall restrictions, VNet-integrated workspaces, environment separation, and policy enforcement. | `PRODUCTION_BLUEPRINT` |
| Compute and throughput scale | Trial compute processed the bounded workload and the separate five-million-row fixture under the same measured configuration. | Add representative concurrency, production node sizing, throughput SLAs, autoscaling policy, and regression thresholds. | `PRODUCTION_BLUEPRINT` |
| Observability and alerting | Diagnostics and the alert rule were configured before workloads; limitations for empty in-window logs and unfired alert state remain explicit. | Add routed alerting, operational dashboards, longer retention, error budgets, and on-call ownership. | `PRODUCTION_BLUEPRINT` |
| Resilience and disaster recovery | The real quality gate failed, the affected path was repaired, and recovered counts, invariants, aggregates, and hashes reconciled. | Define formal SLOs, RPO/RTO, backup/restore exercises, regional strategy, and recurring failure tests. | `PRODUCTION_BLUEPRINT` |
| Identity and access governance | Managed identities, Access Connector, scoped grants, ownership, comments, tags, masking, and lineage were exercised. | Add privileged-access processes, access reviews, enterprise policy assignments, customer-managed keys where required, and ownership workflow. | `PRODUCTION_BLUEPRINT` |
| FinOps and operating ownership | Budget notifications, engineering stop gates, ephemeral compute, CI/CD validation, and exact-scope teardown bounded the lifecycle. | Add chargeback tags, forecasting, anomaly response, promotion controls, and long-lived capacity planning. | `PRODUCTION_BLUEPRINT` |

This table intentionally does not say the torn-down Trial environment is enterprise production. It shows portfolio-grade production engineering proof beside explicit blueprint work.

## Gold-to-future-consumer boundary

Future AI Engineering Portfolio consumers enter through governed Gold data products; that future portfolio is not implemented in Part 4.

| Gold object | Grain | Keys | Quality boundary |
| --- | --- | --- | --- |
| `fact_batch_quality` | One quality measurement for one batch characteristic at one observation time | batch_id, product_id, site_id, characteristic, observation_timestamp | Only conformed Silver quality records enter; rejected records remain in reason-coded quarantine |
| `fact_cold_chain_excursion` | One detected environmental excursion episode per batch and sensor interval | batch_id, sensor_id, excursion_start_utc, excursion_end_utc | Telemetry must pass schema, timestamp, and temperature validity before episode publication |
| `dim_batch_history` | One effective-dated version of a batch lifecycle record | batch_id, effective_from_utc, effective_to_utc, is_current | AUTO CDC output must pass the one-current-version invariant |
| `dim_site` | One operating site | site_id | Unknown site keys are blocked before Gold publication |
| `dim_product` | One manufactured product | product_id | Unknown product keys are blocked before Gold publication |
| `kpi_quality_summary` | One site, product, and reporting date | site_id, product_id, reporting_date | Only validated Gold facts and dimensions feed KPI aggregation |

## Reproduce locally

Prerequisites are Python 3.12, JDK 17, Node 24, Azure CLI with Bicep, and the Databricks CLI.

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe --editable ".[dev]"
npm ci
.venv/Scripts/python.exe -m pytest tests/unit tests/integration -q
.venv/Scripts/python.exe -m ruff check src tests pipelines
az bicep build --file infra/main.bicep
npm run check
```

Live deployment intentionally fails closed unless `PART4_BUDGET_USD` is numeric and within the approved limit. The workflow supports only `deploy-run-collect` and `teardown` operations.

## Cost and security boundaries

- Target: $10 incremental.
- Stop new compute or retries: $15.
- Immediate teardown: $20.
- Azure Databricks: Trial only; no paid Premium fallback.
- Identity: managed identities and federated CI authentication; no long-lived cloud password or Databricks token.
- Public evidence excludes secrets, connection strings, storage keys, account identifiers, tenant and subscription identifiers, and personal email addresses.
- Teardown scope: Only the isolated Part 4 resource group, its Databricks-managed resource group, and the Part 4 budget.

## Technical documentation

- [Architecture](docs/architecture.md)
- [Architecture decisions](docs/architecture-decisions.md)
- [Decision dossier](docs/decisions/README.md)
- [Production readiness](docs/production-readiness.md)
- [Security](docs/security.md)
- [Data contracts](docs/data-contracts.md)
- [Quality rules](docs/quality-rules.md)
- [Runbook](docs/runbook.md)
- [Incident report](docs/incident-report.md)
- [Performance report](docs/performance-report.md)
- [Cost report](docs/cost-report.md)
- [Evidence methodology](docs/evidence-methodology.md)

## Current evidence boundary

Azure provisioning, scoped identity, ADF batch ingestion, Event Hubs streaming, Lakeflow orchestration and expectations, AUTO CDC, Unity Catalog governance and lineage, failure and focused repair, idempotent recovery, the six-run performance experiment, monitoring configuration, and OIDC-backed deployment validation are `VERIFIED` with sanitized artifacts. Cost remains `PENDING BILLING SETTLEMENT`; the administrative alert was enabled but did not fire; the Trial workspace exposed no Databricks ARM diagnostic category. Exact-scope teardown is `VERIFIED`: Azure authoritatively read back the isolated resource group, its Databricks-managed resource group, and the Part 4 budget as absent. No resource screenshot is treated as proof of workload execution.

The source planning document is private and is not included in this repository or its public metadata.
