import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const content = JSON.parse(await readFile(resolve(root, "portfolio/content/project.json"), "utf8"));
const { project, capabilities, data_profile: dataProfile, gold_objects: goldObjects, boundaries } = content;
const teardownVerified = content.engineering_journey.find((item) => item.id === "teardown")?.status === "VERIFIED";
const teardownBoundary = teardownVerified
  ? "Exact-scope teardown is `VERIFIED`: Azure authoritatively read back the isolated resource group, its Databricks-managed resource group, and the Part 4 budget as absent."
  : "Exact-scope teardown remains `PRODUCTION_BLUEPRINT` until Azure authoritatively reads back the isolated resource group, its Databricks-managed resource group, and the Part 4 budget as absent.";

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

Azure provisioning, scoped identity, ADF batch ingestion, Event Hubs streaming, Lakeflow orchestration and expectations, AUTO CDC, Unity Catalog governance and lineage, failure and focused repair, idempotent recovery, the six-run performance experiment, monitoring configuration, and OIDC-backed deployment validation are \`VERIFIED\` with sanitized artifacts. Cost remains \`PENDING BILLING SETTLEMENT\`; the administrative alert was enabled but did not fire; the Trial workspace exposed no Databricks ARM diagnostic category. ${teardownBoundary} No resource screenshot is treated as proof of workload execution.

The source planning document is private and is not included in this repository or its public metadata.
`;

const linkedIn = `# LinkedIn Featured content

## Featured title

Azure Data Engineering Evidence Portfolio: Quality Critical Lakehouse

## Featured description

I built and executed a reproducible Azure lakehouse spanning Bicep, ADLS Gen2, Data Factory, Event Hubs, Azure Databricks, Unity Catalog, PySpark, Delta Lake, Lakeflow, Azure Monitor, CI/CD, failure recovery, performance measurement, governance, and cost control${teardownVerified ? ", with authoritative teardown verification" : ""}. The case study links every major claim to implementation, validation, execution status, and sanitized evidence.

## Featured link

${project.site}

## Post draft

I built Part 4 of my Azure Data Engineering portfolio around a question that matters in any quality critical operation: can a published KPI be traced all the way back to the batch record or sensor event that created it?

Azure Data Factory copied six commit pinned files and reconciled 30,000 batch quality rows. Event Hubs carried exactly 20,000 deterministic telemetry messages into checkpointed Structured Streaming. PySpark and Delta Lake then moved both paths through Bronze provenance, Silver validation and quarantine, Lakeflow AUTO CDC for SCD Type 2 history, and six documented Gold data products.

The ten task Lakeflow Jobs graph completed on Azure Databricks Trial. Unity Catalog recorded table and column lineage, applied managed storage and scoped grants, and demonstrated column masking. I then injected a reserved quality failure, captured the real failed task and diagnostic, repaired only the affected path, and proved the recovered content matched the clean baseline.

I also ran a separate five million row Spark experiment three times per implementation on the same compute. The broadcast plan produced the same result hash but was 39.009 percent slower by median wall time. I published that result because honest measurement is more useful than a predetermined optimization story.

Architecture, code, tests, platform captures, machine receipts, validation results, UTC timestamps, commit references, and SHA256 hashes are connected at the claim level. Cost telemetry remained pending settlement, so no zero or estimate is invented.${teardownVerified ? " Azure also confirmed the isolated resource groups and Part 4 budget were absent after exact scope teardown." : ""}

The full case study includes a 90 second recruiter path, a technical deep dive, a searchable evidence explorer, and a 32 page document.

Portfolio: ${project.site}

Repository: ${project.repository}

#Azure #AzureDatabricks #DataEngineering #PySpark #DeltaLake #DataFactory #EventHubs #Lakeflow #UnityCatalog

## Publication boundary

This file is a draft only. It is not uploaded or posted by project automation. Before publication, update any statement whose evidence status changed and verify that every cloud execution claim is marked consistently with the public evidence manifest.
`;

await mkdir(resolve(root, "portfolio/linkedin"), { recursive: true });
await writeFile(resolve(root, "README.md"), readme, "utf8");
await writeFile(resolve(root, "portfolio/linkedin/featured-and-post.md"), linkedIn, "utf8");
console.log("Synchronized README and LinkedIn copy from part4-content-model/v1.");
