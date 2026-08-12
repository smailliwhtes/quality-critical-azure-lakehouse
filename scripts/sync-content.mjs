import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const content = JSON.parse(await readFile(resolve(root, "portfolio/content/project.json"), "utf8"));
const { project, capabilities, data_profile: dataProfile, gold_objects: goldObjects, boundaries } = content;

const capabilityLine = capabilities.map((item) => `\`${item}\``).join(" · ");
const profileRows = dataProfile.map((item) => `| ${item.label} | ${item.value} |`).join("\n");
const goldRows = goldObjects.map((item) => `| \`${item.name}\` | ${item.grain} |`).join("\n");

const readme = `# ${project.title}

${project.subtitle}. This is an evidence-led Azure Data Engineering case study in which infrastructure, transformations, orchestration, recovery, performance, governance, cost, and teardown are independently inspectable.

> ${project.recruiter_takeaway}

[View the recruiter case study](${project.site}) · [Download the 32-page portfolio document](${project.site}downloads/part4-azure-data-engineering-portfolio.pdf) · [Inspect the evidence manifest](evidence/public/evidence_manifest.json)

## Engineering scope

${capabilityLine}

## Business problem

${project.business_problem}

The implementation answers four operational questions:

- Did each batch remain within quality and environmental limits?
- Which records failed validation, and why?
- What changed during the batch lifecycle?
- Can every published KPI be traced to source data and an executed pipeline?

## Evidence contract

Public claims use exactly three states:

- \`VERIFIED\`: executed in the stated Azure or Databricks environment and paired with sanitized platform evidence.
- \`DEMONSTRATED\`: executed deterministically outside the claimed cloud environment or validated as an implementation artifact.
- \`PRODUCTION_BLUEPRINT\`: designed and documented but not executed in this bounded portfolio environment.

The source of truth is [\`evidence/public/evidence_manifest.json\`](evidence/public/evidence_manifest.json). Every major verified claim binds a platform capture, code path, machine receipt, validation result, UTC time, execution commit, and SHA-256 hash.

## Deterministic data product

Seed: \`${project.seed}\`

| Domain | Rows |
| --- | ---: |
${profileRows}
| CDC changes | 48 |
| Reserved hard failures | 1 |

The fixture includes controlled duplicates, null and unknown business keys, malformed timestamps, impossible temperatures, inconsistent units, out-of-order CDC, schema evolution, and one isolated hard contract failure. The complete file and hash contract is [\`data/synthetic/manifest.json\`](data/synthetic/manifest.json).

## Gold data products

| Object | Grain |
| --- | --- |
${goldRows}

Every Gold object also declares keys, upstream lineage, and executable validation SQL in [\`sql/gold/table_contracts.yml\`](sql/gold/table_contracts.yml) and [\`sql/gold/validate_gold.sql\`](sql/gold/validate_gold.sql).

## Architecture

![${project.title} architecture](portfolio/architecture/quality-critical-lakehouse.svg)

- Batch: deterministic files → Azure Data Factory → ADLS Gen2 landing → Bronze.
- Streaming: bounded producer → Event Hubs → Structured Streaming → checkpointed Bronze Delta.
- Processing: reusable PySpark → Silver validation and quarantine → CDC/SCD2 → Gold products.
- Control plane: managed identities, Access Connector, Unity Catalog, Key Vault, Monitor, Log Analytics, GitHub Actions, budgets, and teardown verification.

## Reproduce locally

Prerequisites are Python 3.12, JDK 17, Node 24, Azure CLI with Bicep, and the Databricks CLI.

\`\`\`powershell
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe --editable ".[dev]"
npm ci
.venv/Scripts/python.exe -m pytest tests/unit tests/integration -q
.venv/Scripts/python.exe -m ruff check src tests pipelines
az bicep build --file infra/main.bicep
npm run check
\`\`\`

Live deployment intentionally fails closed unless \`PART4_BUDGET_USD\` is numeric and within the approved limit. The workflow supports only \`deploy-run-collect\` and \`teardown\` operations.

## Cost and security boundaries

- Target: ${boundaries.cost_target}.
- Stop new compute or retries: ${boundaries.retry_stop}.
- Immediate teardown: ${boundaries.teardown_stop}.
- Azure Databricks: ${boundaries.databricks}.
- Identity: managed identities and federated CI authentication; no long-lived cloud password or Databricks token.
- Public evidence excludes secrets, connection strings, storage keys, account identifiers, tenant and subscription identifiers, and personal email addresses.
- Teardown scope: ${boundaries.teardown}.

## Technical documentation

- [Architecture](docs/architecture.md)
- [Security](docs/security.md)
- [Data contracts](docs/data-contracts.md)
- [Quality rules](docs/quality-rules.md)
- [Runbook](docs/runbook.md)
- [Incident report](docs/incident-report.md)
- [Performance report](docs/performance-report.md)
- [Cost report](docs/cost-report.md)
- [Evidence methodology](docs/evidence-methodology.md)

## Current evidence boundary

Local implementation and deterministic tests are represented as \`DEMONSTRATED\`. Azure workload, lineage, incident, monitoring, cost, CI deployment, and teardown claims remain \`PRODUCTION_BLUEPRINT\` until their real sanitized artifacts are present. No resource screenshot is treated as proof of workload execution.

The source planning document is private and is not included in this repository or its public metadata.
`;

const linkedIn = `# LinkedIn Featured content

## Featured title

Azure Data Engineering Evidence Portfolio: Quality-Critical Lakehouse

## Featured description

I built a reproducible Azure lakehouse implementation spanning Bicep, ADLS Gen2, Data Factory, Event Hubs, Azure Databricks, Unity Catalog, PySpark, Delta Lake, Lakeflow, Azure Monitor, CI/CD, failure recovery, Spark performance measurement, governance, cost control, and verified teardown. The case study links every major claim to its implementation, validation, execution status, and sanitized evidence.

## Featured link

${project.site}

## Post draft

I built Part 4 of my Azure Data Engineering portfolio around a question that matters in any quality-critical operation: can a published KPI be traced all the way back to the batch record or sensor event that created it?

The project combines scheduled batch ingestion through Azure Data Factory with bounded streaming telemetry through Event Hubs. PySpark and Delta Lake carry both paths through Bronze provenance, Silver validation and quarantine, CDC and SCD Type 2 history, and six documented Gold data products.

The strongest part is the evidence model. Architecture, code, tests, platform receipts, validation results, timestamps, commit references, and SHA-256 hashes are connected at the claim level. A resource existing is not treated as proof that a workload ran.

I also designed the operational story into the build: a controlled quality failure, focused Lakeflow repair, idempotency checks, a three by three Spark benchmark, monitoring, explicit cost gates, and authoritative teardown verification.

The full case study includes a 90-second recruiter path, a technical deep dive, a searchable evidence explorer, and a 32-page document.

Portfolio: ${project.site}

Repository: ${project.repository}

#Azure #AzureDatabricks #DataEngineering #PySpark #DeltaLake #DataFactory #EventHubs #Lakeflow #UnityCatalog

## Publication boundary

This file is a draft only. It is not uploaded or posted by project automation. Before publication, update any statement whose evidence status changed and verify that every cloud-execution claim is marked consistently with the public evidence manifest.
`;

await mkdir(resolve(root, "portfolio/linkedin"), { recursive: true });
await writeFile(resolve(root, "README.md"), readme, "utf8");
await writeFile(resolve(root, "portfolio/linkedin/featured-and-post.md"), linkedIn, "utf8");
console.log("Synchronized README and LinkedIn copy from part4-content-model/v1.");
