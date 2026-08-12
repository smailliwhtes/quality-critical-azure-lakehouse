import { createHash } from "node:crypto";
import { access, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { execFileSync } from "node:child_process";

const root = resolve(import.meta.dirname, "..");
const publicRoot = resolve(root, "evidence/public");
const content = JSON.parse(await readFile(resolve(root, "portfolio/content/project.json"), "utf8"));
const currentCommit = execFileSync("git", ["rev-parse", "HEAD"], { cwd: root, encoding: "utf8" }).trim();

const definitions = {
  "architecture-deployment": {
    service: "Azure Resource Manager and Azure Databricks",
    screenshot: "09-resource-group.png",
    receipt: "platform-configuration.json",
    validation: "tests/unit/test_iac_and_assets.py",
    runId: "azure-part4-deployment",
    notes: "Trial workspace, isolated resource group, modular Bicep deployment, and reconciled live inventory are represented together.",
  },
  "identity-security": {
    service: "Microsoft Entra ID, Azure RBAC, and Key Vault",
    screenshot: "10-managed-identity.png",
    receipt: "release-validation.json",
    validation: "tests/unit/test_iac_and_assets.py",
    runId: (receipt) => receipt.oidc_deployment_validation.public_run_id,
    commit: (receipt) => receipt.oidc_deployment_validation.commit_sha,
    notes: "Managed identities handled data access and GitHub OIDC completed a resource-group-scoped deployment validation without a cloud password.",
  },
  adls: {
    service: "Azure Data Lake Storage Gen2",
    screenshot: "11-adls-layout.png",
    receipt: "source-upload.json",
    validation: "tests/integration/test_medallion_transforms.py",
    runId: "adls-source-upload",
    notes: "Six deterministic files were uploaded through Azure AD RBAC without storage keys; governed landing and checkpoint paths were exercised.",
  },
  adf: {
    service: "Azure Data Factory",
    screenshot: "14-adf-copy-metrics.png",
    receipt: "adf-copy-run.json",
    validation: "tests/unit/test_iac_and_assets.py",
    notes: "The successful ForEach run reconciles six Copy activities and 30,000 rows from immutable public source URLs.",
  },
  "event-hubs": {
    service: "Azure Event Hubs and Structured Streaming",
    screenshot: "15-event-hubs-metrics.png",
    receipt: "structured-streaming-progress.json",
    validation: "tests/unit/test_telemetry_producer.py",
    commit: () => "0a689155ad6dd97c5e6b9718c00b44245a7d8e46",
    notes: "Producer, Azure Monitor, final partition offsets, zero lag, checkpoint state, and Bronze Delta count reconcile to 20,000 messages.",
  },
  "unity-catalog": {
    service: "Databricks Unity Catalog",
    screenshot: "18-catalog-hierarchy.png",
    receipt: "unity-catalog-governance.json",
    validation: "tests/unit/test_iac_and_assets.py",
    notes: "Managed storage, external locations, ownership, grants, comments, tags, and a column mask were applied in the live catalog.",
  },
  bronze: {
    service: "Azure Databricks and Delta Lake",
    screenshot: "20-bronze-provenance.png",
    receipt: "lakeflow-clean-run.json",
    validation: "tests/integration/test_medallion_transforms.py",
    notes: "The executed Bronze tables retain source identity, ingestion and event timestamps, pipeline run, record hash, and schema version.",
  },
  "quality-quarantine": {
    service: "Lakeflow Declarative Pipelines",
    screenshot: "21-quality-expectations.png",
    receipt: "lakeflow-controlled-incident.json",
    validation: "tests/integration/test_medallion_transforms.py",
    notes: "Warning metrics, quarantine routing, and the reserved fail-on-violation contract were all exercised on the live pipeline.",
  },
  silver: {
    service: "PySpark and Delta Lake",
    screenshot: "23-silver-conformance.png",
    receipt: "lakeflow-clean-run.json",
    validation: "tests/integration/test_medallion_transforms.py",
    notes: "Silver outputs reconcile deterministic validation, conformance, deduplication, unit normalization, and quarantine counts.",
  },
  scd2: {
    service: "Lakeflow AUTO CDC",
    screenshot: "24-scd2-history.png",
    receipt: "lakeflow-clean-run.json",
    validation: "tests/integration/test_medallion_transforms.py",
    notes: "The live CHANGE flow produced 647 effective-dated versions with zero current-version invariant violations; the fallback was not used.",
  },
  gold: {
    service: "Databricks SQL and Delta Lake",
    screenshot: "25-gold-products.png",
    receipt: "lakeflow-clean-run.json",
    validation: "sql/gold/validate_gold.sql",
    notes: "Two facts, three dimensions, and one KPI table were published at documented grains and passed count, key, and aggregate validation.",
  },
  orchestration: {
    service: "Lakeflow Jobs",
    screenshot: "03-lakeflow-jobs-dag.png",
    receipt: "lakeflow-clean-run.json",
    validation: "tests/unit/test_automation_contracts.py",
    notes: "The ten-task DAG completed successfully with parallel Bronze paths and dependency-gated quality, Silver, history, Gold, validation, and receipt tasks.",
  },
  lineage: {
    service: "Databricks Unity Catalog",
    screenshot: "04-unity-catalog-lineage.png",
    receipt: "lakeflow-clean-run.json",
    validation: "sql/gold/validate_gold.sql",
    notes: "Live table and column lineage connects the conformed Silver quality data to the Gold fact and derived quality flag.",
  },
  "failure-recovery": {
    service: "Lakeflow Jobs and Declarative Pipelines",
    screenshot: "05-failure-repair.png",
    receipt: "lakeflow-recovery-validation.json",
    validation: "tests/integration/test_medallion_transforms.py",
    runId: (receipt) => `repair-${receipt.repair_id}`,
    notes: "A real expectation failure was diagnosed and repaired on the same run; completed upstream work remained intact and recovered content matched the clean baseline.",
  },
  performance: {
    service: "Apache Spark on Azure Databricks",
    screenshot: "06-performance-comparison.png",
    receipt: "spark-performance-comparison.json",
    validation: "tests/integration/test_performance_fixture.py",
    notes: "Three baseline and three broadcast runs used the same five-million-row fixture and compute; all result hashes matched.",
    limitation: "The broadcast median was 39.009% slower, and Spark Connect did not expose classic status-store task, stage, shuffle, spill, partition, maximum-task, or p75 metrics.",
  },
  "monitoring-cost": {
    service: "Azure Monitor, Log Analytics, and Cost Management",
    screenshot: "31-log-analytics.png",
    receipt: "monitoring-validation.json",
    validation: "tests/unit/test_iac_and_assets.py",
    runId: "monitoring-window-20260812",
    notes: "Diagnostics preceded workloads and the alert rule was enabled; cost snapshots retained the exact pending-settlement label.",
    limitation: "No Log Analytics rows were visible in the bounded window, the data-plane quality incident did not fire the administrative alert, and Cost Management returned no settled amount.",
  },
  cicd: {
    service: "GitHub Actions and GitHub Pages",
    screenshot: "33-github-actions.png",
    receipt: "release-validation.json",
    validation: "tests/site/portfolio.spec.ts",
    runId: (receipt) => receipt.ci.public_run_id,
    commit: (receipt) => receipt.ci.commit_sha,
    notes: "A green CI run and a separate successful OIDC-backed Azure deployment validation are linked by public workflow receipts.",
  },
  teardown: {
    service: "Azure Resource Manager and Cost Management",
    screenshot: "34-teardown.png",
    receipt: "teardown.json",
    validation: "tests/unit/test_automation_contracts.py",
    runId: (receipt) => receipt?.public_run_id ?? "pending-authoritative-readback",
    notes: "Deletion is intentionally deferred until the pre-teardown evidence release is durable.",
    limitation: "Authoritative resource-group, Databricks-managed-resource-group, and Part 4 budget absence readback is pending.",
  },
  evidence: {
    service: "Public evidence system",
    screenshot: "01-architecture.png",
    receipt: "preflight.json",
    validation: "tests/unit/test_evidence_manifest.py",
    runId: "deterministic-publication-build",
    notes: "A single validated content model and generated manifest drive the README, site, evidence explorer, and 32-page document.",
    limitation: "Generated explanatory panels are labeled as generated artifacts and are not represented as platform screenshots.",
  },
};

async function fileExists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

async function sha256(path) {
  return createHash("sha256").update(await readFile(path)).digest("hex");
}

function valueFrom(definition, key, receipt, fallback) {
  const value = definition[key];
  if (typeof value === "function") return value(receipt);
  return value ?? fallback;
}

const artifacts = [];
for (const chapter of content.engineering_journey) {
  const definition = definitions[chapter.id];
  if (!definition) throw new Error(`Missing evidence definition for ${chapter.id}.`);

  const screenshotRelative = `evidence/public/screenshots/${definition.screenshot}`;
  const receiptRelative = `evidence/public/receipts/${definition.receipt}`;
  const screenshotPath = resolve(root, screenshotRelative);
  const receiptPath = resolve(root, receiptRelative);
  const screenshotPresent = await fileExists(screenshotPath);
  const receiptPresent = await fileExists(receiptPath);
  const required = chapter.status !== "PRODUCTION_BLUEPRINT";

  if (required && !screenshotPresent) throw new Error(`${chapter.id} requires ${screenshotRelative}.`);
  if (required && !receiptPresent) throw new Error(`${chapter.id} requires ${receiptRelative}.`);
  if (required) {
    for (const path of [chapter.code, definition.validation]) {
      if (!await fileExists(resolve(root, path))) throw new Error(`${chapter.id} references missing ${path}.`);
    }
  }

  const receipt = receiptPresent ? JSON.parse(await readFile(receiptPath, "utf8")) : null;
  const capturedAt = receipt?.captured_at_utc
    ?? receipt?.completed_at_utc
    ?? receipt?.properties?.timestamp
    ?? "PENDING";
  const runId = valueFrom(
    definition,
    "runId",
    receipt,
    receipt?.public_run_id ?? receipt?.run_id ?? receipt?.name ?? chapter.id,
  );
  const commitSha = valueFrom(
    definition,
    "commit",
    receipt,
    receipt?.execution_commit ?? receipt?.ci?.commit_sha ?? currentCommit,
  );

  artifacts.push({
    artifact_id: chapter.id,
    claim: chapter.summary,
    status: chapter.status,
    service: definition.service,
    captured_at_utc: capturedAt,
    screenshot: screenshotPresent ? screenshotRelative : "",
    receipt: receiptPresent ? receiptRelative : "",
    code_path: chapter.code,
    validation: definition.validation,
    run_id: String(runId),
    commit_sha: String(commitSha),
    sha256: screenshotPresent ? await sha256(screenshotPath) : "",
    notes: definition.notes,
    limitation: definition.limitation ?? "",
  });
}

const manifest = {
  schema: "part4-evidence-manifest/v1",
  status_vocabulary: ["VERIFIED", "DEMONSTRATED", "PRODUCTION_BLUEPRINT"],
  artifacts,
};

await writeFile(
  resolve(publicRoot, "evidence_manifest.json"),
  `${JSON.stringify(manifest, null, 2)}\n`,
  "utf8",
);

console.log(`Generated ${artifacts.length} evidence artifacts from the public execution record.`);
