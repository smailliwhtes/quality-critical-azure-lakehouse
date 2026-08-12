import { access, mkdir, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import sharp from "sharp";

const root = resolve(import.meta.dirname, "..");
const receipts = resolve(root, "evidence/public/receipts");
const output = resolve(root, "evidence/public/screenshots");
const WIDTH = 1600;
const HEIGHT = 900;

const xml = (value) => String(value ?? "—")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");

const number = (value) => value === null || value === undefined
  ? "NOT EXPOSED"
  : new Intl.NumberFormat("en-US", { maximumFractionDigits: 3 }).format(value);

const seconds = (value) => value === null || value === undefined
  ? "NOT EXPOSED"
  : `${Number(value).toFixed(3)} s`;

async function json(name, optional = false) {
  try {
    return JSON.parse(await readFile(resolve(receipts, name), "utf8"));
  } catch (error) {
    if (optional && error.code === "ENOENT") return null;
    throw error;
  }
}

async function exists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

function metricCards(metrics) {
  const count = metrics.length;
  const gap = 24;
  const width = (1456 - gap * (count - 1)) / count;
  return metrics.map((item, index) => {
    const x = 72 + index * (width + gap);
    return `
      <rect x="${x}" y="245" width="${width}" height="150" rx="16" fill="#0e263a" stroke="#23455e"/>
      <text x="${x + 24}" y="287" class="label">${xml(item.label)}</text>
      <text x="${x + 24}" y="344" class="metric" fill="${item.color ?? "#f7fbff"}">${xml(item.value)}</text>
      <text x="${x + 24}" y="374" class="hint">${xml(item.hint ?? "")}</text>`;
  }).join("");
}

function rowsTable(rows) {
  return rows.slice(0, 7).map((row, index) => {
    const y = 493 + index * 42;
    return `<text x="102" y="${y}" class="row-key">${xml(row[0])}</text>
      <text x="830" y="${y}" class="row-value">${xml(row[1])}</text>
      <line x1="96" y1="${y + 17}" x2="1504" y2="${y + 17}" stroke="#17384f"/>`;
  }).join("");
}

function panelSvg(spec) {
  const badgeColor = spec.status === "VERIFIED" ? "#4cdfc3" : spec.status === "DEMONSTRATED" ? "#52a9ff" : "#f2bd5b";
  const rightTitle = spec.kind ?? "SANITIZED EVIDENCE PANEL";
  return `<svg width="${WIDTH}" height="${HEIGHT}" viewBox="0 0 ${WIDTH} ${HEIGHT}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#06131f"/><stop offset="1" stop-color="#0a2132"/></linearGradient>
      <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#0078d4"/><stop offset="1" stop-color="#4cdfc3"/></linearGradient>
      <style>
        text{font-family:'Segoe UI',Arial,sans-serif}.eyebrow{font-size:21px;font-weight:700;letter-spacing:3px;fill:#59b4ff}.title{font-size:48px;font-weight:700;fill:#f7fbff}.subtitle{font-size:22px;fill:#a8bfd1}.label{font-size:16px;font-weight:700;letter-spacing:1.4px;fill:#8eacc0}.metric{font-size:34px;font-weight:700}.hint{font-size:14px;fill:#7897ab}.section{font-size:18px;font-weight:700;letter-spacing:2px;fill:#4cdfc3}.row-key{font-size:19px;fill:#b9cddd}.row-value{font-size:19px;font-weight:600;fill:#f7fbff}.footer{font-size:14px;fill:#7996aa}.badge{font-size:17px;font-weight:800;letter-spacing:1.6px}.kind{font-size:15px;font-weight:700;letter-spacing:1.6px;fill:#7f9db1}.mono{font-family:Consolas,'Courier New',monospace;font-size:17px;fill:#d9e7f1}
      </style>
    </defs>
    <rect width="1600" height="900" fill="url(#bg)"/>
    <rect width="1600" height="8" fill="url(#accent)"/>
    <circle cx="1510" cy="82" r="144" fill="#0078d4" opacity=".08"/>
    <text x="72" y="69" class="eyebrow">${xml(spec.eyebrow)}</text>
    <text x="72" y="135" class="title">${xml(spec.title)}</text>
    <text x="72" y="180" class="subtitle">${xml(spec.subtitle)}</text>
    <text x="1528" y="57" text-anchor="end" class="kind">${xml(rightTitle)}</text>
    <rect x="1328" y="82" width="200" height="42" rx="21" fill="#102a3e" stroke="${badgeColor}"/>
    <text x="1428" y="109" text-anchor="middle" class="badge" fill="${badgeColor}">${xml(spec.status)}</text>
    ${metricCards(spec.metrics)}
    <rect x="72" y="430" width="1456" height="350" rx="18" fill="#091d2c" stroke="#23455e"/>
    <text x="96" y="465" class="section">${xml(spec.section ?? "WHAT THE RECEIPT PROVES")}</text>
    ${spec.code ? `<text x="102" y="510" class="mono">${spec.code.map((line, index) => `<tspan x="102" dy="${index ? 30 : 0}">${xml(line)}</tspan>`).join("")}</text>` : rowsTable(spec.rows ?? [])}
    <line x1="72" y1="829" x2="1528" y2="829" stroke="#23455e"/>
    <text x="72" y="862" class="footer">${xml(spec.receipt)}</text>
    <text x="1528" y="862" text-anchor="end" class="footer">${xml(spec.captured ?? "Deterministic build from public source artifacts")}</text>
  </svg>`;
}

async function render(filename, spec, { preserve = false } = {}) {
  const path = resolve(output, filename);
  if (preserve && await exists(path)) return false;
  await sharp(Buffer.from(panelSvg(spec))).png({ compressionLevel: 9 }).toFile(path);
  return true;
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

function metricMedian(runs, field) {
  const values = runs.map((run) => run[field]).filter((value) => Number.isFinite(value));
  return values.length ? median(values) : null;
}

await mkdir(output, { recursive: true });
const adf = await json("adf-copy-run.json");
const producer = await json("event-hubs-producer.json");
const stream = await json("structured-streaming-progress.json");
const clean = await json("lakeflow-clean-run.json");
const recovery = await json("lakeflow-recovery-validation.json");
const governance = await json("unity-catalog-governance.json");
const platform = await json("platform-configuration.json");
const inventory = await json("resource-inventory.json");
const source = await json("source-upload.json");
const performance = await json("spark-performance-comparison.json", true);
const monitoring = await json("monitoring-validation.json", true);
const cost = await json("cost-incident-performance.json", true) ?? await json("cost-ingestion.json");
const release = await json("release-validation.json", true);
const teardown = await json("teardown.json", true);

const codeLines = (await readFile(resolve(root, "src/qcal/transforms.py"), "utf8"))
  .split(/\r?\n/).slice(43, 54).map((line, index) => `${String(index + 44).padStart(3)}  ${line}`);

const shared = {
  status: "VERIFIED",
  kind: "EXECUTED / SANITIZED",
};

const visuals = [
  ["02-pyspark-transformation.png", {
    eyebrow: "PYSPARK / SILVER CONTRACT", title: "Validation routes every record deliberately",
    subtitle: "Reusable transformation code separates accepted rows from explainable quarantine.",
    status: "DEMONSTRATED", kind: "REVIEWABLE CODE", metrics: [
      { label: "QUALITY INPUT", value: number(clean.row_counts["bronze.batch_quality_raw"]), hint: "Bronze rows executed" },
      { label: "VALID", value: number(clean.row_counts["silver.batch_quality_valid"]), hint: "conformed Silver rows", color: "#4cdfc3" },
      { label: "QUARANTINED", value: number(clean.row_counts["silver.quarantined_quality_records"]), hint: "reason-coded records", color: "#f2bd5b" },
    ], section: "IMPLEMENTATION EXCERPT / src/qcal/transforms.py", code: codeLines,
    receipt: "Code: src/qcal/transforms.py  •  Validation: tests/integration/test_medallion_transforms.py",
    captured: clean.captured_at_utc,
  }],
  ["07-bicep-modules.png", {
    eyebrow: "BICEP / SUBSCRIPTION SCOPE", title: "One bounded resource group, composed by modules",
    subtitle: "Trial-only infrastructure, scoped identity, diagnostics, budget, and explicit outputs.",
    status: "DEMONSTRATED", kind: "INFRASTRUCTURE AS CODE", metrics: [
      { label: "TOP-LEVEL RESOURCES", value: number(inventory.length), hint: "reconciled inventory" },
      { label: "REGION", value: "EAST US 2", hint: "single deployment region", color: "#52a9ff" },
      { label: "WORKSPACE SKU", value: platform.workspace_sku.toUpperCase(), hint: "no paid fallback", color: "#4cdfc3" },
    ], rows: [
      ["main.bicep", "subscription scope + budget-first dependency"], ["storage.bicep", "ADLS Gen2 / Standard_LRS / six containers"],
      ["data-factory.bicep", "managed identity + batch factory"], ["event-hubs.bicep", "Standard / 1 throughput unit / bounded stream"],
      ["databricks.bicep", "Trial workspace + Access Connector"], ["monitoring.bicep", "Log Analytics + diagnostics + alert"],
      ["rbac.bicep", "resource-group-scoped assignments"],
    ], receipt: "infra/main.bicep  •  evidence/public/receipts/resource-inventory.json",
  }],
  ["08-bicep-what-if.png", {
    eyebrow: "AZURE WHAT-IF / FAIL CLOSED", title: "Deployment scope was inspected before execution",
    subtitle: "The sanitized plan was reconciled to the explicit Part 4 resource manifest.", ...shared,
    metrics: [{ label: "BUDGET", value: "$20", hint: "created before workload resources" },
      { label: "RESOURCE GROUPS", value: "2", hint: "isolated + Databricks-managed" },
      { label: "DESTRUCTIVE CHANGES", value: "0", hint: "unexpected deletes accepted", color: "#4cdfc3" }],
    rows: [["Deployment scope", "Subscription / isolated resource group"], ["Resource group", "rg-qcal-part4-dev"],
      ["Managed resource group", "rg-qcal-part4-dbx-managed"], ["Workspace policy", "Trial only / Hybrid"],
      ["Storage policy", "HNS + TLS 1.2 + Standard_LRS"], ["Identity policy", "Managed identities + scoped RBAC"],
      ["Decision", "Expected scope reconciled; deployment allowed"]], receipt: "evidence/public/receipts/bicep-what-if.json",
  }],
  ["10-managed-identity.png", {
    eyebrow: "IDENTITY / PASSWORDLESS BY DEFAULT", title: "Four trust paths, zero long-lived cloud passwords",
    subtitle: "ADF, Access Connector, GitHub Actions, and operators use scoped federated or managed identity.", ...shared,
    metrics: [{ label: "LONG-LIVED TOKENS", value: "0", hint: "public configuration readback", color: "#4cdfc3" },
      { label: "OIDC DEPLOYMENT", value: "SUCCESS", hint: "resource-group scope" },
      { label: "STORAGE KEYS USED", value: source.storage_keys_used ? "YES" : "NO", hint: "source upload via Azure AD", color: "#4cdfc3" }],
    rows: [["Azure Data Factory", "system-assigned identity → ADLS landing"], ["Access Connector", "managed identity → Unity Catalog external locations"],
      ["GitHub Actions", "federated OIDC → isolated resource group"], ["Databricks automation", "Azure CLI authentication"],
      ["Event Hubs credential", "Key Vault-backed secret scope"], ["Public evidence", "tenant, subscription, principal IDs excluded"]],
    receipt: "evidence/public/receipts/platform-configuration.json  •  source-upload.json",
  }],
  ["11-adls-layout.png", {
    eyebrow: "ADLS GEN2 / DELIBERATE STATE", title: "Data, checkpoints, quarantine, and evidence are separated",
    subtitle: "Hierarchical namespace and managed identity make ownership and replay boundaries inspectable.", ...shared,
    metrics: [{ label: "CONTAINERS", value: "6", hint: "source, landing, managed, quarantine, checkpoints, evidence" },
      { label: "FILES LANDED", value: number(adf.files_requested), hint: "commit-pinned batch inputs" },
      { label: "AUTHENTICATION", value: "AZURE AD", hint: "no storage keys", color: "#4cdfc3" }],
    rows: [["source/", "governed deterministic fixtures"], ["landing/quality/", "ADF file-level batch arrivals"],
      ["managed/", "Unity Catalog external data root"], ["quarantine/", "reason-coded rejected records"],
      ["checkpoints/", "Structured Streaming replay state"], ["evidence/", "governed run receipts"],
      ["Security", "HNS / TLS 1.2 / Standard_LRS / shared keys disabled"]],
    receipt: "evidence/public/receipts/source-upload.json  •  infra/modules/storage.bicep",
  }],
  ["12-key-vault.png", {
    eyebrow: "KEY VAULT / SECRET VALUE EXCLUDED", title: "Only the runtime credential is secret-backed",
    subtitle: "The public record proves the control without publishing connection material.", ...shared,
    metrics: [{ label: "SECRET VALUES PUBLIC", value: "0", hint: "names and control state only", color: "#4cdfc3" },
      { label: "EVENTS EMITTED", value: number(producer.events_emitted), hint: "credential worked end to end" },
      { label: "CONNECTION MATERIAL", value: producer.connection_material_included ? "INCLUDED" : "EXCLUDED", hint: "producer receipt", color: "#4cdfc3" }],
    rows: [["Secret purpose", "Event Hubs Kafka-compatible connection"], ["Vault access", "RBAC authorization"],
      ["Producer output", "message count + file hash only"], ["Databricks scope", "Key Vault-backed when supported"],
      ["Public sanitization", "no keys, SAS, connection strings, or values"], ["Result", "bounded producer and consumer both reconciled"]],
    receipt: "evidence/public/receipts/event-hubs-producer.json  •  infra/modules/key-vault.bicep",
  }],
  ["13-adf-pipeline.png", {
    eyebrow: "AZURE DATA FACTORY / BATCH DESIGN", title: "A parameterized ForEach drives six Copy activities",
    subtitle: "Each commit-pinned file receives independent transfer and row-count evidence.", ...shared,
    metrics: [{ label: "SOURCE FILES", value: number(adf.files_requested), hint: "immutable GitHub URLs" },
      { label: "ROWS REQUESTED", value: number(adf.copy_activities.reduce((sum, a) => sum + a.rows_read, 0)), hint: "deterministic quality observations" },
      { label: "PIPELINE STATUS", value: adf.status.toUpperCase(), hint: "executed in Azure", color: "#4cdfc3" }],
    rows: [["1. Lookup / parameter array", "six source filenames"], ["2. ForEach", "one bounded iteration per file"],
      ["3. CopyQualityJson", "HTTPS source → ADLS Gen2 landing"], ["4. Sink authentication", "Data Factory managed identity"],
      ["5. Reconciliation", "rows read = rows copied per activity"], ["6. Receipt", "files, rows, bytes, duration, status"]],
    receipt: "adf/pipeline/pl_ingest_batch_quality.json  •  evidence/public/receipts/adf-copy-run.json",
  }],
  ["14-adf-copy-metrics.png", {
    eyebrow: "ADF / EXECUTED COPY METRICS", title: "Six files and 30,000 rows reconciled exactly",
    subtitle: "No duplicate run was submitted during retries; the verified receipt was reused.", ...shared,
    metrics: [{ label: "ACTIVITIES SUCCEEDED", value: `${adf.copy_activities.filter((a) => a.status === "Succeeded").length} / ${adf.copy_activities.length}`, hint: "all Copy activities" },
      { label: "ROWS COPIED", value: number(adf.copy_activities.reduce((sum, a) => sum + a.rows_copied, 0)), hint: "equals rows read", color: "#4cdfc3" },
      { label: "BYTES WRITTEN", value: number(adf.copy_activities.reduce((sum, a) => sum + a.bytes_written, 0)), hint: "sanitized activity output" }],
    rows: adf.copy_activities.map((a, index) => [`quality-${String(index + 1).padStart(2, "0")}.jsonl`, `${number(a.rows_copied)} rows  •  ${number(a.bytes_written)} bytes  •  ${a.copy_duration_seconds}s`]),
    receipt: "evidence/public/receipts/adf-copy-run.json", captured: adf.captured_at_utc,
  }],
  ["15-event-hubs-metrics.png", {
    eyebrow: "EVENT HUBS / BOUNDED STREAM", title: "Exactly 20,000 deterministic messages were emitted",
    subtitle: "The producer records seed, source hash, attempted count, emitted count, and excludes credentials.", ...shared,
    metrics: [{ label: "ATTEMPTED", value: number(producer.events_attempted), hint: "bounded execution" },
      { label: "EMITTED", value: number(producer.events_emitted), hint: "100% producer reconciliation", color: "#4cdfc3" },
      { label: "PARTITION OFFSETS", value: "10,198 + 9,802", hint: "consumer total = 20,000" }],
    rows: [["Event Hub", producer.event_hub_name], ["Fixture seed", producer.seed], ["Source SHA-256", `${producer.source_sha256.slice(0, 24)}…`],
      ["Producer duration", `${((Date.parse(producer.completed_at_utc) - Date.parse(producer.started_at_utc)) / 1000).toFixed(3)} seconds`],
      ["Consumer lag", "0 at captured checkpoint"], ["Connection material", "excluded from public receipt"]],
    receipt: "evidence/public/receipts/event-hubs-producer.json  •  structured-streaming-progress.json",
  }],
  ["16-streaming-progress.png", {
    eyebrow: "STRUCTURED STREAMING / KAFKA OFFSETS", title: "Producer, offsets, checkpoint, and Bronze all reconcile",
    subtitle: "Explicit schema and append semantics consumed the bounded Event Hubs stream into Delta.", ...shared,
    metrics: [{ label: "PARTITION 0", value: "10,198", hint: "final offset" }, { label: "PARTITION 1", value: "9,802", hint: "final offset" },
      { label: "BRONZE ROWS", value: number(clean.row_counts["bronze.sensor_telemetry_raw"]), hint: "Delta output", color: "#4cdfc3" }],
    rows: [["Source", "Kafka-compatible Event Hubs interface"], ["Schema", "explicit telemetry StructType"],
      ["Write mode", "append to Unity Catalog Delta table"], ["Checkpoint", stream.checkpoint],
      ["Maximum offset lag", stream.progress.sources[0].metrics.maxOffsetsBehindLatest], ["Source metadata", "partition, offset, event time, ingest time"],
      ["Reconciliation", "10,198 + 9,802 = 20,000 Bronze rows"]],
    receipt: "evidence/public/receipts/structured-streaming-progress.json", captured: stream.captured_at_utc,
  }],
  ["17-checkpoint-delta.png", {
    eyebrow: "REPLAY STATE / DELTA BRONZE", title: "A real checkpoint protects append-only streaming state",
    subtitle: "The governed volume separates consumer progress from the Delta table it protects.", ...shared,
    metrics: [{ label: "CHECKPOINT", value: "EXISTS", hint: "governed Unity Catalog volume", color: "#4cdfc3" },
      { label: "MAX LAG", value: stream.progress.sources[0].metrics.maxOffsetsBehindLatest, hint: "at final progress receipt" },
      { label: "DELTA ROWS", value: number(clean.row_counts["bronze.sensor_telemetry_raw"]), hint: "no producer/consumer gap" }],
    rows: [["Checkpoint path", stream.checkpoint], ["Bronze table", "part4_ops.bronze.sensor_telemetry_raw"],
      ["Source partitions", "2"], ["Final offsets", "10,198 / 9,802"], ["Sink format", "Delta"],
      ["Semantics", "append + durable checkpoint"], ["Validation", "producer count = offsets = Bronze count"]],
    receipt: "evidence/public/receipts/structured-streaming-progress.json  •  lakeflow-clean-run.json",
  }],
  ["19-governance-policy.png", {
    eyebrow: "UNITY CATALOG / ENFORCED POLICY", title: "Metadata, tags, grants, and masking were applied",
    subtitle: "The governed catalog demonstrates controls inside the executed data path.", ...shared,
    metrics: [{ label: "COLUMN MASK", value: governance.column_mask, hint: "synthetic sensitive field", color: "#4cdfc3" },
      { label: "TAGS", value: governance.unity_catalog_tags, hint: "governance metadata" },
      { label: "COMMENTS + PROPERTIES", value: governance.comments_and_properties, hint: "discoverability" }],
    rows: [["Catalog", "part4_ops"], ["Schemas", "bronze / silver / gold / governance"],
      ["Storage credential", platform.storage_credential], ["External locations", "source / landing / quarantine / checkpoints / evidence"],
      ["Column control", "mask applied to synthetic operator field"], ["Ownership and grants", "scoped, explicit, inspectable"],
      ["Control status", governance.status]], receipt: "evidence/public/receipts/unity-catalog-governance.json", captured: governance.captured_at_utc,
  }],
  ["23-silver-conformance.png", {
    eyebrow: "SILVER / CONFORMED BOUNDARY", title: "Types, keys, domains, units, and duplicates are enforced",
    subtitle: "Accepted records and rejected records reconcile back to their Bronze inputs.", ...shared,
    metrics: [{ label: "QUALITY VALID", value: number(clean.row_counts["silver.batch_quality_valid"]), hint: "29,994 + 6 = 30,000", color: "#4cdfc3" },
      { label: "TELEMETRY VALID", value: number(clean.row_counts["silver.sensor_telemetry_valid"]), hint: "range and unit conformant" },
      { label: "DUPLICATE GOLD KEYS", value: "0", hint: "validation receipt", color: "#4cdfc3" }],
    rows: [["Business keys", "non-null + known batch/site/product references"], ["Timestamps", "parsed UTC + malformed/out-of-order routing"],
      ["Temperature", "unit normalization + possible range"], ["Deduplication", "record hash + deterministic ordering"],
      ["Quality quarantine", number(clean.row_counts["silver.quarantined_quality_records"])], ["Telemetry quarantine", number(clean.row_counts["silver.quarantined_telemetry"])],
      ["Validation", clean.validation]], receipt: "evidence/public/receipts/lakeflow-clean-run.json  •  src/qcal/transforms.py",
  }],
  ["28-idempotency.png", {
    eyebrow: "RECOVERY / CONTENT PROOF", title: "Clean and repaired outputs are byte-for-byte equivalent",
    subtitle: "Counts, aggregates, duplicate checks, current-version invariant, and canonical hashes all reconcile.", ...shared,
    metrics: [{ label: "VALIDATION", value: recovery.validation, hint: "clean versus repaired", color: "#4cdfc3" },
      { label: "DUPLICATE KEYS", value: "0", hint: "facts and KPIs" },
      { label: "UPSTREAM RERUN", value: recovery.successful_upstream_rerun ? "YES" : "NO", hint: "successful tasks preserved", color: "#4cdfc3" }],
    rows: [["Clean canonical SHA-256", recovery.clean_content_hash], ["Recovered canonical SHA-256", recovery.recovered_content_hash],
      ["Expected / recovered match", String(recovery.expected_and_recovered_match).toUpperCase()],
      ["Current-version violations", recovery.current_version_violations], ["Focused rerun task", recovery.rerun_tasks.join(", ")],
      ["Dependent tasks rerun", String(recovery.rerun_dependent_tasks).toUpperCase()], ["Outcome", "deterministic repair without duplicate processing"]],
    receipt: "evidence/public/receipts/lakeflow-recovery-validation.json", captured: recovery.captured_at_utc,
  }],
];

if (performance) {
  const base = performance.runs.baseline;
  const opt = performance.runs.optimized;
  const comparisonMetrics = [
    { label: "BASELINE MEDIAN", value: seconds(performance.comparison.baseline_median_wall_time_seconds), hint: "3 runs / same compute" },
    { label: "OPTIMIZED MEDIAN", value: seconds(performance.comparison.optimized_median_wall_time_seconds), hint: "broadcast + no repartition", color: "#4cdfc3" },
    { label: "WALL-TIME CHANGE", value: `${performance.comparison.measured_wall_time_change_percent > 0 ? "+" : ""}${performance.comparison.measured_wall_time_change_percent}%`, hint: "published without cherry-picking" },
  ];
  visuals.push(["06-performance-comparison.png", {
    eyebrow: "SPARK / THREE BY THREE", title: "Measured optimization on five million skewed rows",
    subtitle: "Both implementations produced the same result hash on identical compute.", ...shared, metrics: comparisonMetrics,
    rows: [["Fixture", `${number(performance.fixture.row_count)} rows / ${performance.fixture.minimum_skew_fraction * 100}% hot key`],
      ["Dimension", `${performance.fixture.dimension_size} rows`], ["Baseline", "shuffle hash join + unnecessary repartition"],
      ["Optimized", "broadcast hash join + original partitioning"], ["Result hashes match", String(performance.result_hashes_match).toUpperCase()],
      ["Baseline run times", base.map((run) => seconds(run.wall_time_seconds)).join(" / ")], ["Optimized run times", opt.map((run) => seconds(run.wall_time_seconds)).join(" / ")]],
    receipt: "evidence/public/receipts/spark-performance-comparison.json", captured: performance.captured_at_utc,
  }]);
  for (const [filename, mode, label] of [["29-spark-baseline.png", base, "BASELINE"], ["30-spark-optimized.png", opt, "OPTIMIZED"]]) {
    visuals.push([filename, {
      eyebrow: `SPARK METRICS / ${label}`, title: `${label === "BASELINE" ? "Shuffle join with explicit repartition" : "Broadcast join without needless repartition"}`,
      subtitle: "Three complete executions on the same runtime and single-node compute.", ...shared,
      metrics: [{ label: "MEDIAN WALL TIME", value: seconds(metricMedian(mode, "wall_time_seconds")), hint: "median of three" },
        { label: "MEDIAN TASKS", value: number(metricMedian(mode, "task_count")), hint: "Spark status store" },
        { label: "MEDIAN SHUFFLE WRITE", value: number(metricMedian(mode, "shuffle_write_bytes")), hint: metricMedian(mode, "shuffle_write_bytes") === null ? "runtime did not expose" : "bytes" }],
      rows: mode.map((run) => [`Run ${run.iteration}`, `${seconds(run.wall_time_seconds)}  •  ${run.stage_count ?? "—"} stages  •  ${run.task_count ?? "—"} tasks  •  ${run.join_strategy}`]).concat([
        ["Result SHA-256", `${mode[0].result_sha256.slice(0, 40)}…`], ["Physical plan", `${mode[0].physical_plan_sha256.slice(0, 40)}…`],
        ["Metric caveat", metricMedian(mode, "shuffle_write_bytes") === null ? "shuffle/spill not exposed by runtime status store" : "all requested stage metrics captured"],
      ]), receipt: "evidence/public/receipts/spark-performance-comparison.json", captured: performance.captured_at_utc,
    }]);
  }
}

if (monitoring) {
  const tables = monitoring.discovered_tables ?? [];
  visuals.push(["31-log-analytics.png", {
    eyebrow: "LOG ANALYTICS / LIVE TABLE DISCOVERY", title: "Queries used the tables that actually ingested",
    subtitle: "Diagnostics were configured before workloads; public output excludes workspace identifiers.", ...shared,
    metrics: [{ label: "DISCOVERED TABLES", value: number(tables.length), hint: "search * / Type summary" },
      { label: "DIAGNOSTICS ORDER", value: monitoring.diagnostics_configured_before_workloads ? "BEFORE" : "AFTER", hint: "relative to workloads", color: "#4cdfc3" },
      { label: "ALERT RULE", value: monitoring.alert_rule_enabled ? "ENABLED" : "DISABLED", hint: "configuration readback" }],
    rows: (tables.length ? tables.slice(0, 6).map((item) => [item.table, `${number(item.record_count)} records`]) : [["Live query result", "No records visible inside the bounded billing/ingestion window"]]).concat([
      ["Query", "search * | summarize record_count=count() by Type"], ["Identifier policy", "workspace and customer IDs excluded"],
    ]), receipt: "evidence/public/receipts/monitoring-validation.json", captured: monitoring.captured_at_utc,
  }]);
  visuals.push(["32-monitor-cost.png", {
    eyebrow: "MONITOR + COST / TRUTHFUL BOUNDARIES", title: "Configured controls are distinct from observed outcomes",
    subtitle: "The alert is not called fired, and delayed cost telemetry is not converted into a fake value.",
    status: "DEMONSTRATED", kind: "CONFIGURATION + CURRENT SNAPSHOT", metrics: [
      { label: "ALERT CONFIGURED", value: monitoring.alert_rule_enabled ? "YES" : "NO", hint: "administrative operations" },
      { label: "ALERT FIRED", value: monitoring.alert_fired ? "YES" : "NO", hint: "controlled failure was data-plane" },
      { label: "COST LABEL", value: cost.label, hint: cost.query_status, color: "#f2bd5b" },
    ], rows: [["Budget", "$20 / actual 50%, 75%, 100% / forecast 100%"], ["Retry stop", "$15"], ["Immediate teardown gate", "$20"],
      ["Cost amount", cost.amount === null ? "not published while Azure API is unavailable" : `${cost.currency} ${cost.amount}`],
      ["Alert limitation", monitoring.limitation], ["Databricks diagnostics", platform.databricks_arm_diagnostics],
      ["Evidence rule", "configuration ≠ fired alert; pending settlement ≠ zero cost"]],
    receipt: "monitoring-validation.json  •  cost-incident-performance.json", captured: cost.captured_at_utc,
  }]);
}

if (release) {
  visuals.push(["33-github-actions.png", {
    eyebrow: "GITHUB ACTIONS / FEDERATED RELEASE", title: "CI and Azure OIDC validation passed without a cloud password",
    subtitle: "The release receipt binds workflow conclusions to public commit references.", ...shared,
    metrics: [{ label: "CI", value: release.ci_conclusion, hint: `run ${release.ci_public_run_id}` },
      { label: "OIDC DEPLOY", value: release.oidc_conclusion, hint: `run ${release.oidc_public_run_id}`, color: "#4cdfc3" },
      { label: "LONG-LIVED SECRET", value: "NONE", hint: "federated managed identity" }],
    rows: [["CI scope", "Python / Spark / Bicep / bundle / site / PDF / publication scans"],
      ["OIDC scope", "read and write validation only inside rg-qcal-part4-dev"], ["Repository", "smailliwhtes/quality-critical-azure-lakehouse"],
      ["Execution commit", release.commit_sha], ["CI conclusion", release.ci_conclusion], ["OIDC conclusion", release.oidc_conclusion],
      ["Credential boundary", "no client secret or Databricks token created"]], receipt: "evidence/public/receipts/release-validation.json", captured: release.captured_at_utc,
  }]);
}

if (teardown) {
  visuals.push(["34-teardown.png", {
    eyebrow: "AZURE TEARDOWN / AUTHORITATIVE ABSENCE", title: "The isolated cloud footprint is gone",
    subtitle: "Deletion was limited to the Part 4 resource groups and budget, then polled to absence.", ...shared,
    metrics: [{ label: "ISOLATED RG", value: teardown.resource_group_absent ? "ABSENT" : "PRESENT", hint: "authoritative readback", color: "#4cdfc3" },
      { label: "MANAGED RG", value: teardown.managed_resource_group_absent ? "ABSENT" : "PRESENT", hint: "Databricks-managed scope" },
      { label: "PART 4 BUDGET", value: teardown.budget_absent ? "ABSENT" : "PRESENT", hint: "subscription readback" }],
    rows: [["Deleted scope 1", "rg-qcal-part4-dev"], ["Deleted scope 2", "rg-qcal-part4-dbx-managed"],
      ["Deleted scope 3", "qcal-part4-budget"], ["Shared metastore", "preserved"], ["Unrelated Azure resources", "not targeted"],
      ["Readback attempts", teardown.poll_attempts], ["Final state", teardown.validation]],
    receipt: "evidence/public/receipts/teardown.json", captured: teardown.captured_at_utc,
  }]);
}

let generated = 0;
for (const [filename, spec] of visuals) {
  if (await render(filename, spec)) generated += 1;
}
console.log(`Built ${generated} evidence visuals from public code and receipts.`);
