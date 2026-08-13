import { access, readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const content = JSON.parse(await readFile(resolve(root, "portfolio/content/project.json"), "utf8"));
const screenshots = JSON.parse(await readFile(resolve(root, "evidence/public/screenshot_manifest.json"), "utf8"));
const evidence = JSON.parse(await readFile(resolve(root, "evidence/public/evidence_manifest.json"), "utf8"));
const allowed = ["VERIFIED", "DEMONSTRATED", "PRODUCTION_BLUEPRINT"];
const evidenceIds = new Set(evidence.artifacts.map((item) => item.artifact_id));
const decisionIds = new Set(content.architecture_decisions?.map((item) => item.id) ?? []);
const goldNames = new Set(content.gold_objects.map((item) => item.name));

if (content.schema !== "part4-content-model/v1") throw new Error("Unexpected content schema.");
if (content.project.author !== "Michael Seth Williams") throw new Error("Unexpected author.");
if (content.hero_path.length !== 6) throw new Error("Recruiter path must contain exactly six cards.");
if (content.engineering_journey.length !== 19) throw new Error("Engineering journey must contain 19 chapters.");
if (content.pdf_pages.length !== 32) throw new Error("LinkedIn document must contain exactly 32 pages.");
if (content.architecture_decisions?.length !== 6) throw new Error("Architecture decision dossier must contain exactly six records.");
if (content.execution_timeline?.length !== 8) throw new Error("Execution timeline must contain exactly eight stages.");
if (content.production_readiness?.length !== 6) throw new Error("Production readiness matrix must contain exactly six rows.");
if (screenshots.screenshots.length !== 34) throw new Error("Screenshot manifest must contain exactly 34 slots.");
if (new Set(screenshots.screenshots.map((item) => item.id)).size !== 34) throw new Error("Screenshot IDs must be unique.");
if (JSON.stringify(evidence.status_vocabulary) !== JSON.stringify(allowed)) throw new Error("Evidence status vocabulary drifted.");

for (const item of [...content.hero_path, ...content.engineering_journey, ...content.pdf_pages, ...content.architecture_decisions, ...screenshots.screenshots, ...evidence.artifacts]) {
  if (!allowed.includes(item.status)) throw new Error(`Unapproved evidence status: ${item.status}`);
}

for (const [index, item] of content.architecture_decisions.entries()) {
  if (item.sequence !== index + 1) throw new Error("Architecture decisions must be numbered 1 through 6.");
  if (item.decision_state !== "ACCEPTED") throw new Error(`Architecture decision ${item.id} has an unexpected decision state.`);
  for (const field of ["title", "context", "decision", "rejected_alternative", "tradeoff", "outcome", "production_extension", "reconsider_when"]) {
    if (!item[field]?.trim()) throw new Error(`Architecture decision ${item.id} is missing ${field}.`);
  }
  for (const evidenceId of item.evidence_ids ?? []) {
    if (!evidenceIds.has(evidenceId)) throw new Error(`Architecture decision ${item.id} references unknown evidence ${evidenceId}.`);
  }
  if (!item.code_paths?.length) throw new Error(`Architecture decision ${item.id} must list implementation paths.`);
}

for (const [index, item] of content.execution_timeline.entries()) {
  if (item.sequence !== index + 1) throw new Error("Execution timeline must be numbered 1 through 8.");
  if (!evidenceIds.has(item.evidence_id)) throw new Error(`Timeline stage ${item.id ?? item.sequence} references unknown evidence.`);
  for (const decisionId of item.decision_ids ?? []) {
    if (!decisionIds.has(decisionId)) throw new Error(`Timeline stage ${item.sequence} references unknown decision ${decisionId}.`);
  }
  if (!allowed.includes(item.status)) throw new Error(`Timeline stage ${item.sequence} has unapproved status ${item.status}.`);
}

for (const item of content.production_readiness) {
  if (!evidenceIds.has(item.evidence_id)) throw new Error(`Readiness row ${item.id} references unknown evidence.`);
  if (!allowed.includes(item.proof_status)) throw new Error(`Readiness row ${item.id} has unapproved proof status.`);
  if (item.hardening_status !== "PRODUCTION_BLUEPRINT") throw new Error(`Readiness row ${item.id} must keep production hardening as blueprint.`);
  if (!item.executed_proof?.trim() || !item.production_extension?.trim()) throw new Error(`Readiness row ${item.id} is incomplete.`);
}

if (content.future_consumer_boundary?.status !== "PRODUCTION_BLUEPRINT") throw new Error("Future consumer boundary must remain a production blueprint.");
if (content.future_consumer_boundary?.implements_ai !== false) throw new Error("Future consumer boundary must not claim an AI implementation.");
if (new Set(content.future_consumer_boundary.gold_contracts.map((item) => item.gold_object)).size !== goldNames.size) throw new Error("Future consumer boundary must cover every Gold object exactly once.");
for (const item of content.future_consumer_boundary.gold_contracts) {
  if (!goldNames.has(item.gold_object)) throw new Error(`Future consumer boundary references unknown Gold object ${item.gold_object}.`);
}

for (const filename of ["architecture.md", "architecture-decisions.md", "security.md", "data-contracts.md", "quality-rules.md", "runbook.md", "incident-report.md", "performance-report.md", "cost-report.md", "evidence-methodology.md", "production-readiness.md"]) {
  await access(resolve(root, "docs", filename));
}
for (const filename of ["README.md", "batch-and-streaming-ingestion.md", "bronze-provenance.md", "quality-policy-routing.md", "temporal-history-cdc.md", "governed-table-operations.md", "evidence-led-performance.md"]) {
  await access(resolve(root, "docs/decisions", filename));
}

console.log("Validated content model, decision dossier, 32-page sequence, 34 screenshot slots, documentation, and status vocabulary.");
