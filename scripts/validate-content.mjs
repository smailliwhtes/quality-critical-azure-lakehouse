import { access, readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const content = JSON.parse(await readFile(resolve(root, "portfolio/content/project.json"), "utf8"));
const screenshots = JSON.parse(await readFile(resolve(root, "evidence/public/screenshot_manifest.json"), "utf8"));
const evidence = JSON.parse(await readFile(resolve(root, "evidence/public/evidence_manifest.json"), "utf8"));
const allowed = ["VERIFIED", "DEMONSTRATED", "PRODUCTION_BLUEPRINT"];

if (content.schema !== "part4-content-model/v1") throw new Error("Unexpected content schema.");
if (content.project.author !== "Michael Seth Williams") throw new Error("Unexpected author.");
if (content.hero_path.length !== 6) throw new Error("Recruiter path must contain exactly six cards.");
if (content.engineering_journey.length !== 19) throw new Error("Engineering journey must contain 19 chapters.");
if (content.pdf_pages.length !== 32) throw new Error("LinkedIn document must contain exactly 32 pages.");
if (screenshots.screenshots.length !== 34) throw new Error("Screenshot manifest must contain exactly 34 slots.");
if (new Set(screenshots.screenshots.map((item) => item.id)).size !== 34) throw new Error("Screenshot IDs must be unique.");
if (JSON.stringify(evidence.status_vocabulary) !== JSON.stringify(allowed)) throw new Error("Evidence status vocabulary drifted.");

for (const item of [...content.hero_path, ...content.engineering_journey, ...content.pdf_pages, ...screenshots.screenshots, ...evidence.artifacts]) {
  if (!allowed.includes(item.status)) throw new Error(`Unapproved evidence status: ${item.status}`);
}

for (const filename of ["architecture.md", "security.md", "data-contracts.md", "quality-rules.md", "runbook.md", "incident-report.md", "performance-report.md", "cost-report.md", "evidence-methodology.md"]) {
  await access(resolve(root, "docs", filename));
}

console.log("Validated content model, 32-page sequence, 34 screenshot slots, documentation, and status vocabulary.");
