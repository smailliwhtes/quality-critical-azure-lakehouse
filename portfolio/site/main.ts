import "./styles.css";
import content from "../content/project.json";
import evidence from "../../evidence/public/evidence_manifest.json";

type Status = "VERIFIED" | "DEMONSTRATED" | "PRODUCTION_BLUEPRINT";
type Journey = typeof content.engineering_journey[number];
type ArchitectureDecision = typeof content.architecture_decisions[number];
type EvidenceArtifact = typeof evidence.artifacts[number];

const root = document.querySelector<HTMLDivElement>("#app");
if (!root) throw new Error("Portfolio root was not found.");

const repo = content.project.repository;
const base = import.meta.env.BASE_URL;
const architecture = `${base}assets/architecture/quality-critical-lakehouse.png`;
const pdf = `${base}downloads/part4-azure-data-engineering-portfolio.pdf`;
const evidenceById = new Map(evidence.artifacts.map((artifact) => [artifact.artifact_id, artifact]));
const heroScreenshots: Record<string, string> = {
  architecture: "01-architecture.png",
  "pyspark-transformation": "02-pyspark-transformation.png",
  "lakeflow-jobs": "03-lakeflow-jobs-dag.png",
  "unity-catalog-lineage": "04-unity-catalog-lineage.png",
  "failure-repair": "05-failure-repair.png",
  "performance-comparison": "06-performance-comparison.png",
};
const evidenceLabels: Record<string, string> = {
  "architecture-deployment": "Azure deployment",
  "identity-security": "Identity and security",
  adls: "ADLS Gen2 layout",
  adf: "ADF batch ingestion",
  "event-hubs": "Event Hubs streaming",
  "unity-catalog": "Unity Catalog governance",
  bronze: "Bronze provenance",
  "quality-quarantine": "Quality and quarantine",
  silver: "Silver conformance",
  scd2: "AUTO CDC SCD2",
  gold: "Gold products",
  orchestration: "Lakeflow Jobs DAG",
  lineage: "Unity Catalog lineage",
  "failure-recovery": "Failure and repair",
  performance: "Spark performance",
  "monitoring-cost": "Monitoring and cost",
  cicd: "CI/CD validation",
  teardown: "Verified teardown",
  evidence: "Evidence methodology",
};
const decisionDocs: Record<string, string> = {
  "workload-shaped-ingestion": "docs/decisions/batch-and-streaming-ingestion.md",
  "source-fidelity-bronze": "docs/decisions/bronze-provenance.md",
  "risk-based-quality-policy": "docs/decisions/quality-policy-routing.md",
  "declarative-temporal-history": "docs/decisions/temporal-history-cdc.md",
  "governed-table-operations": "docs/decisions/governed-table-operations.md",
  "evidence-led-performance": "docs/decisions/evidence-led-performance.md",
};

function esc(value: string | number) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  })[character] ?? character);
}

function status(status: Status) {
  return `<span class="status status--${status.toLowerCase().replace("_", "-")}">${status.replace("_", " ")}</span>`;
}

function codeUrl(path: string) {
  return `${repo}/blob/main/${path}`;
}

function evidenceFor(item: Journey): EvidenceArtifact | undefined {
  return evidenceById.get(item.id);
}

function evidenceLink(artifactId: string) {
  const artifact = evidenceById.get(artifactId);
  const label = evidenceLabels[artifactId] ?? artifact?.claim ?? artifactId.replaceAll("-", " ");
  return `<a href="#evidence-${esc(artifactId)}">Evidence: ${esc(label)}</a>`;
}

const capabilityChips = content.capabilities.map((item) => `<li>${esc(item)}</li>`).join("");
const dataProfile = content.data_profile.map((item) => `
  <div class="metric"><strong>${esc(item.value)}</strong><span>${esc(item.label)}</span></div>`).join("");

const heroCards = content.hero_path.map((item, index) => `
  <article class="hero-card" id="hero-${esc(item.id)}">
    <div class="hero-card__index">${String(index + 1).padStart(2, "0")}</div>
    <p class="eyebrow">${esc(item.eyebrow)}</p>
    <h3>${esc(item.title)}</h3>
    <a class="hero-card__visual" href="${base}evidence/screenshots/${esc(heroScreenshots[item.id])}" aria-label="Open ${esc(item.title)} evidence at full resolution">
      <img src="${base}evidence/screenshots/${esc(heroScreenshots[item.id])}" alt="${esc(item.what)}" loading="lazy" />
    </a>
    <div class="hero-card__copy"><h4>What I did</h4><p>${esc(item.what)}</p></div>
    <div class="hero-card__copy"><h4>Why it matters</h4><p>${esc(item.why)}</p></div>
    <footer>${status(item.status as Status)}<a href="#evidence-explorer">Inspect evidence <span aria-hidden="true">→</span></a></footer>
  </article>`).join("");

const decisionCards = content.architecture_decisions.map((item: ArchitectureDecision) => `
  <article class="decision-card" id="decision-${esc(item.id)}" data-status="${esc(item.status)}">
    <div class="decision-card__top"><span>${String(item.sequence).padStart(2, "0")}</span>${status(item.status as Status)}</div>
    <p class="decision-card__state">Decision state: ${esc(item.decision_state)}</p>
    <h3>${esc(item.title)}</h3>
    <div class="decision-card__grid">
      <div><h4>Decision</h4><p>${esc(item.decision)}</p></div>
      <div><h4>Why</h4><p>${esc(item.outcome)}</p></div>
      <div><h4>Rejected alternative</h4><p>${esc(item.rejected_alternative)}</p></div>
      <div><h4>Trade-off</h4><p>${esc(item.tradeoff)}</p></div>
    </div>
    <div class="decision-card__evidence">
      ${item.evidence_ids.map((artifactId) => evidenceLink(artifactId)).join("")}
      <a href="${esc(codeUrl(decisionDocs[item.id]))}">Full decision record</a>
    </div>
  </article>`).join("");

const timelineSteps = content.execution_timeline.map((item) => `
  <li class="timeline-step" data-status="${esc(item.status)}">
    <span class="timeline-step__number">${String(item.sequence).padStart(2, "0")}</span>
    <div>
      <h3>${esc(item.title)}</h3>
      <p>${esc(item.outcome)}</p>
      <div class="timeline-step__links">${status(item.status as Status)}${evidenceLink(item.evidence_id)}</div>
    </div>
  </li>`).join("");

const readinessRows = content.production_readiness.map((item) => `
  <tr class="readiness-row">
    <th scope="row">${esc(item.category)}</th>
    <td><span class="readiness-label">Executed proof</span><p>${esc(item.executed_proof)}</p>${status(item.proof_status as Status)}${evidenceLink(item.evidence_id)}</td>
    <td><span class="readiness-label">Production extension</span><p>${esc(item.production_extension)}</p>${status(item.hardening_status as Status)}</td>
  </tr>`).join("");

const futureBoundaryCards = content.future_consumer_boundary.gold_contracts.map((item) => `
  <article class="gold-boundary-card">
    <h3>${esc(item.gold_object)}</h3>
    <p><strong>Grain:</strong> ${esc(item.grain)}</p>
    <p><strong>Keys:</strong> ${esc(item.keys)}</p>
    <p><strong>Quality:</strong> ${esc(item.quality_boundary)}</p>
  </article>`).join("");

const journeyCards = content.engineering_journey.map((item, index) => `
  <article class="journey-card" data-status="${esc(item.status)}">
    <div class="journey-card__top"><span>${String(index + 1).padStart(2, "0")}</span>${status(item.status as Status)}</div>
    <h3>${esc(item.title)}</h3>
    <p>${esc(item.summary)}</p>
    <a href="${esc(codeUrl(item.code))}">View implementation: ${esc(item.code)}</a>
  </article>`).join("");

const evidenceRows = content.engineering_journey.map((item) => {
  const artifact = evidenceFor(item);
  const limitation = artifact?.limitation || (item.status === "PRODUCTION_BLUEPRINT" ? "Bounded Azure execution evidence is pending." : "No platform limitation applies to this deterministic artifact.");
  const receipt = artifact?.receipt ? `<a href="${base}${esc(artifact.receipt.replace("evidence/public/", "evidence/"))}">Receipt</a>` : `<span>Receipt pending</span>`;
  const screenshot = artifact?.screenshot ? `<a href="${base}${esc(artifact.screenshot.replace("evidence/public/", "evidence/"))}">Screenshot</a>` : `<span>Screenshot pending</span>`;
  const validation = artifact?.validation ? `<a href="${esc(codeUrl(artifact.validation))}">Validation</a>` : `<span>Validation pending</span>`;
  const commit = artifact?.commit_sha && artifact.commit_sha !== "PENDING" ? artifact.commit_sha.slice(0, 8) : "pending";
  const commitUrl = artifact?.commit_sha && artifact.commit_sha !== "PENDING" ? `${repo}/commit/${artifact.commit_sha}` : `${repo}/commits/main`;
  return `
    <article class="evidence-row" id="evidence-${esc(artifact?.artifact_id ?? item.id)}" data-search="${esc(`${artifact?.service ?? ""} ${item.title} ${item.summary} ${item.code} ${item.status} ${limitation}`.toLowerCase())}" data-status="${esc(item.status)}">
      <div class="evidence-row__claim"><span class="evidence-row__service">${esc(artifact?.service ?? item.id.replaceAll("-", " "))}</span><h3>${esc(item.title)}</h3><p>${esc(item.summary)}</p></div>
      <div class="evidence-row__state">${status(item.status as Status)}<p>${esc(limitation)}</p></div>
      <div class="evidence-row__links">${screenshot}${receipt}<a href="${esc(codeUrl(item.code))}">Code</a>${validation}<a href="${esc(commitUrl)}">Commit: ${esc(commit)}</a></div>
    </article>`;
}).join("");

root.innerHTML = `
  <header class="site-header">
    <a class="brand" href="#top" aria-label="Quality-Critical Azure Lakehouse home"><span>MSW</span><strong>Azure Data Engineering</strong></a>
    <nav aria-label="Primary navigation">
      <a href="#recruiter-path">90-second path</a>
      <a href="#architecture-decisions">Decisions</a>
      <a href="#engineering-journey">Deep dive</a>
      <a href="#evidence-explorer">Evidence</a>
      <a class="nav-cta" href="${pdf}">Download PDF</a>
    </nav>
  </header>
  <main id="main-content">
    <section class="project-hero" id="top" aria-labelledby="project-title">
      <div class="project-hero__copy">
        <p class="eyebrow">PART 4 / EVIDENCE-LED AZURE LAKEHOUSE</p>
        <h1 id="project-title">${esc(content.project.title)}</h1>
        <p class="project-hero__subtitle">${esc(content.project.subtitle)}</p>
        <p class="project-hero__problem">${esc(content.project.business_problem)}</p>
        <div class="project-hero__actions">
          <a class="button button--primary" href="#recruiter-path">Start the 90-second path</a>
          <a class="button button--secondary" href="${repo}">Inspect the repository</a>
        </div>
        <ul class="capability-chips" aria-label="Primary capabilities">${capabilityChips}</ul>
      </div>
      <figure class="architecture-frame">
        <a href="${architecture}" aria-label="Open the architecture diagram at full resolution"><img src="${architecture}" alt="Batch files pass through Data Factory and ADLS while telemetry passes through Event Hubs and Structured Streaming; both paths converge in a Databricks medallion lakehouse governed by identity, catalog, monitoring, delivery, and cost controls." /></a>
        <figcaption><strong>One architecture, two ingestion modes.</strong><span>Open full resolution</span></figcaption>
      </figure>
    </section>

    <section class="proof-strip" aria-label="Project scale">${dataProfile}</section>

    <section class="section recruiter" id="recruiter-path" aria-labelledby="recruiter-title">
      <div class="section-heading"><div><p class="eyebrow">DEPTH 01 / RECRUITER VIEW</p><h2 id="recruiter-title">The complete signal in six artifacts</h2></div><p>Architecture, transformation, orchestration, governance, recovery, and performance. Every card states what I did, why it matters, and what the current evidence can prove.</p></div>
      <div class="hero-grid">${heroCards}</div>
    </section>

    <section class="section decisions" id="architecture-decisions" aria-labelledby="decisions-title">
      <div class="section-heading"><div><p class="eyebrow">ARCHITECTURE JUDGMENT</p><h2 id="decisions-title">Architecture decisions and trade-offs</h2></div><p>These records explain why the executed Azure platform was built this way, which alternatives were rejected, what each choice cost, and which existing evidence supports it.</p></div>
      <div class="decision-grid">${decisionCards}</div>
    </section>

    <section class="section lifecycle" id="executed-lifecycle" aria-labelledby="lifecycle-title">
      <div class="section-heading"><div><p class="eyebrow">EXECUTED LIFECYCLE</p><h2 id="lifecycle-title">Eight stages from scope to teardown</h2></div><p>The timeline presents the data-platform lifecycle, not just an ETL path: cost/identity, provisioning, ingestion, Bronze, conformance, Gold, failure/repair/performance, and verified closeout.</p></div>
      <ol class="timeline-list">${timelineSteps}</ol>
    </section>

    <section class="section readiness" id="production-readiness" aria-labelledby="readiness-title">
      <div class="section-heading"><div><p class="eyebrow">PRODUCTION READINESS</p><h2 id="readiness-title">Bounded proof versus production extension</h2></div><p>The portfolio proves production engineering behaviors under a Trial boundary. Enterprise hardening remains explicit and labeled as blueprint work, not executed proof.</p></div>
      <div class="readiness-table-wrap">
        <table class="readiness-table">
          <thead><tr><th scope="col">Category</th><th scope="col">Executed portfolio proof</th><th scope="col">Production extension</th></tr></thead>
          <tbody>${readinessRows}</tbody>
        </table>
      </div>
    </section>

    <section class="section future-consumer-boundary" id="future-consumer-boundary" aria-labelledby="future-boundary-title">
      <div class="section-heading"><div><p class="eyebrow">GOLD CONSUMER BOUNDARY</p><h2 id="future-boundary-title">${esc(content.future_consumer_boundary.title)}</h2></div><p>${esc(content.future_consumer_boundary.statement)} ${esc(content.future_consumer_boundary.interface_rule)}</p></div>
      <div class="gold-boundary-grid">${futureBoundaryCards}</div>
    </section>

    <section class="section journey" id="engineering-journey" aria-labelledby="journey-title">
      <div class="section-heading"><div><p class="eyebrow">DEPTH 02 / TECHNICAL DEEP DIVE</p><h2 id="journey-title">Follow the engineering journey</h2></div><p>Each chapter has one responsibility, one implementation path, and an explicit evidence boundary. The sequence starts with deployment and ends with authoritative teardown.</p></div>
      <div class="journey-grid">${journeyCards}</div>
    </section>

    <section class="section evidence" id="evidence-explorer" aria-labelledby="evidence-title">
      <div class="section-heading"><div><p class="eyebrow">DEPTH 03 / CLAIM-LEVEL PROOF</p><h2 id="evidence-title">Search the evidence explorer</h2></div><p>Filter by status or search service, claim, implementation path, and limitation. Cloud claims remain visibly bounded until the corresponding sanitized platform artifact exists.</p></div>
      <div class="evidence-controls" role="search">
        <label for="evidence-search">Search evidence</label>
        <input id="evidence-search" type="search" placeholder="Try SCD2, Event Hubs, repair, cost…" autocomplete="off" />
        <div class="status-filters" aria-label="Filter evidence by status">
          <button type="button" class="is-active" data-filter="ALL" aria-pressed="true">All</button>
          <button type="button" data-filter="VERIFIED" aria-pressed="false">Verified</button>
          <button type="button" data-filter="DEMONSTRATED" aria-pressed="false">Demonstrated</button>
          <button type="button" data-filter="PRODUCTION_BLUEPRINT" aria-pressed="false">Production blueprint</button>
        </div>
      </div>
      <p class="evidence-count" aria-live="polite"><strong>${content.engineering_journey.length}</strong> claims shown</p>
      <div class="evidence-list">${evidenceRows}</div>
      <p class="no-results" hidden>No evidence records match this filter.</p>
    </section>

    <section class="section boundary" aria-labelledby="boundary-title">
      <div><p class="eyebrow">COST + TRUTHFULNESS BOUNDARY</p><h2 id="boundary-title">Fast build. Hard limits. No invented result.</h2><p>Trial-only Databricks, an under-$10 target, a $15 retry stop, and a $20 teardown gate keep the execution window focused. A platform limitation downgrades only that feature; it never becomes a fabricated run, metric, lineage edge, alert, cost, or screenshot.</p></div>
      <dl><div><dt>Target</dt><dd>${esc(content.boundaries.cost_target)}</dd></div><div><dt>Stop retries</dt><dd>${esc(content.boundaries.retry_stop)}</dd></div><div><dt>Teardown</dt><dd>${esc(content.boundaries.teardown_stop)}</dd></div><div><dt>Compute</dt><dd>4 vCPU job + 2 vCPU pipeline</dd></div></dl>
    </section>
  </main>
  <footer class="site-footer"><div><strong>${esc(content.project.author)}</strong><span>${esc(content.project.title)}</span></div><div><a href="${repo}">Repository</a><a href="${pdf}">32-page PDF</a><a href="#top">Back to top</a></div></footer>
`;

const search = document.querySelector<HTMLInputElement>("#evidence-search");
const filterButtons = [...document.querySelectorAll<HTMLButtonElement>("[data-filter]")];
const rows = [...document.querySelectorAll<HTMLElement>(".evidence-row")];
const count = document.querySelector<HTMLElement>(".evidence-count");
const noResults = document.querySelector<HTMLElement>(".no-results");
let activeFilter = "ALL";

function applyEvidenceFilter() {
  const query = search?.value.trim().toLowerCase() ?? "";
  let visible = 0;
  rows.forEach((row) => {
    const matchesStatus = activeFilter === "ALL" || row.dataset.status === activeFilter;
    const matchesQuery = !query || row.dataset.search?.includes(query);
    row.hidden = !(matchesStatus && matchesQuery);
    if (!row.hidden) visible += 1;
  });
  if (count) count.innerHTML = `<strong>${visible}</strong> ${visible === 1 ? "claim" : "claims"} shown`;
  if (noResults) noResults.hidden = visible !== 0;
}

search?.addEventListener("input", applyEvidenceFilter);
filterButtons.forEach((button) => button.addEventListener("click", () => {
  activeFilter = button.dataset.filter ?? "ALL";
  filterButtons.forEach((candidate) => {
    const selected = candidate === button;
    candidate.classList.toggle("is-active", selected);
    candidate.setAttribute("aria-pressed", String(selected));
  });
  applyEvidenceFilter();
}));
