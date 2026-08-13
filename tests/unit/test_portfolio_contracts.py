import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOCS = {
    "architecture.md",
    "architecture-decisions.md",
    "security.md",
    "data-contracts.md",
    "quality-rules.md",
    "runbook.md",
    "incident-report.md",
    "performance-report.md",
    "cost-report.md",
    "evidence-methodology.md",
}

HERO_IDS = {
    "architecture",
    "pyspark-transformation",
    "lakeflow-jobs",
    "unity-catalog-lineage",
    "failure-repair",
    "performance-comparison",
}

DECISION_IDS = {
    "workload-shaped-ingestion",
    "source-fidelity-bronze",
    "risk-based-quality-policy",
    "declarative-temporal-history",
    "governed-table-operations",
    "evidence-led-performance",
}

READINESS_IDS = {
    "network-isolation",
    "compute-throughput-scale",
    "observability-alerting",
    "resilience-disaster-recovery",
    "identity-access-governance",
    "finops-operating-ownership",
}


def load_content() -> dict:
    return json.loads((ROOT / "portfolio/content/project.json").read_text(encoding="utf-8"))


def test_one_content_model_drives_all_public_formats() -> None:
    content = load_content()

    assert content["schema"] == "part4-content-model/v1"
    assert content["project"]["author"] == "Michael Seth Williams"
    assert content["project"]["repository"] == (
        "https://github.com/smailliwhtes/quality-critical-azure-lakehouse"
    )
    assert len(content["hero_path"]) == 6
    assert {item["id"] for item in content["hero_path"]} == HERO_IDS
    assert all(item["status"] in {"VERIFIED", "DEMONSTRATED", "PRODUCTION_BLUEPRINT"}
               for item in content["hero_path"])
    assert len(content["engineering_journey"]) == 19
    assert len(content["pdf_pages"]) == 32


def test_exactly_34_meaningful_public_screenshot_slots_are_declared() -> None:
    screenshots = json.loads(
        (ROOT / "evidence/public/screenshot_manifest.json").read_text(encoding="utf-8")
    )

    assert screenshots["schema"] == "part4-screenshot-manifest/v1"
    assert len(screenshots["screenshots"]) == 34
    assert len({item["id"] for item in screenshots["screenshots"]}) == 34
    assert all(item["purpose"].strip() for item in screenshots["screenshots"])
    assert all(item["source"] in {"PLATFORM", "CODE", "GENERATED_ARTIFACT"}
               for item in screenshots["screenshots"])
    assert all(item["status"] in {"VERIFIED", "DEMONSTRATED", "PRODUCTION_BLUEPRINT"}
               for item in screenshots["screenshots"])


def test_required_technical_documents_and_linkedin_copy_exist() -> None:
    docs = ROOT / "docs"

    assert {path.name for path in docs.glob("*.md")} >= REQUIRED_DOCS
    for filename in REQUIRED_DOCS:
        text = (docs / filename).read_text(encoding="utf-8")
        assert len(text.splitlines()) >= 12
        assert "Current evidence boundary" in text

    linkedin = (ROOT / "portfolio/linkedin/featured-and-post.md").read_text(encoding="utf-8")
    assert "Azure Data Engineering Evidence Portfolio" in linkedin
    assert "Featured description" in linkedin
    assert "Post draft" in linkedin


def test_architecture_decisions_are_complete_and_evidence_linked() -> None:
    content = load_content()
    evidence = json.loads(
        (ROOT / "evidence/public/evidence_manifest.json").read_text(encoding="utf-8")
    )
    evidence_ids = {item["artifact_id"] for item in evidence["artifacts"]}

    decisions = content["architecture_decisions"]

    assert len(decisions) == 6
    assert {item["id"] for item in decisions} == DECISION_IDS
    assert [item["sequence"] for item in decisions] == [1, 2, 3, 4, 5, 6]
    for item in decisions:
        assert item["decision_state"] == "ACCEPTED"
        assert item["status"] in {"VERIFIED", "DEMONSTRATED", "PRODUCTION_BLUEPRINT"}
        assert item["title"].strip()
        assert item["context"].strip()
        assert item["decision"].strip()
        assert item["rejected_alternative"].strip()
        assert item["tradeoff"].strip()
        assert item["outcome"].strip()
        assert item["production_extension"].strip()
        assert item["reconsider_when"].strip()
        assert set(item["evidence_ids"]) <= evidence_ids
        assert item["code_paths"]


def test_execution_timeline_and_production_readiness_are_bounded() -> None:
    content = load_content()
    evidence = json.loads(
        (ROOT / "evidence/public/evidence_manifest.json").read_text(encoding="utf-8")
    )
    evidence_ids = {item["artifact_id"] for item in evidence["artifacts"]}

    timeline = content["execution_timeline"]
    readiness = content["production_readiness"]

    assert len(timeline) == 8
    assert [item["sequence"] for item in timeline] == list(range(1, 9))
    for item in timeline:
        assert item["title"].strip()
        assert item["outcome"].strip()
        assert set(item["decision_ids"]) <= DECISION_IDS
        assert item["evidence_id"] in evidence_ids
        assert item["status"] in {"VERIFIED", "DEMONSTRATED", "PRODUCTION_BLUEPRINT"}

    assert len(readiness) == 6
    assert {item["id"] for item in readiness} == READINESS_IDS
    for item in readiness:
        assert item["executed_proof"].strip()
        assert item["proof_status"] in {"VERIFIED", "DEMONSTRATED", "PRODUCTION_BLUEPRINT"}
        assert item["production_extension"].strip()
        assert item["hardening_status"] == "PRODUCTION_BLUEPRINT"
        assert item["evidence_id"] in evidence_ids


def test_future_consumer_boundary_references_gold_without_ai_execution_claims() -> None:
    content = load_content()
    boundary = content["future_consumer_boundary"]
    gold_names = {item["name"] for item in content["gold_objects"]}
    forbidden_claims = {
        "model training",
        "feature store",
        "embeddings",
        "vector database",
        "rag",
        "model serving",
        "mlflow",
        "azure ai services",
    }
    public_text = json.dumps(boundary, sort_keys=True).lower()

    assert boundary["status"] == "PRODUCTION_BLUEPRINT"
    assert boundary["implements_ai"] is False
    assert {item["gold_object"] for item in boundary["gold_contracts"]} == gold_names
    assert all(term not in public_text for term in forbidden_claims)
    for item in boundary["gold_contracts"]:
        assert item["grain"].strip()
        assert item["keys"].strip()
        assert item["time_semantics"].strip()
        assert item["quality_boundary"].strip()
        assert item["lineage"].strip()


def test_decision_dossier_documents_exist() -> None:
    decision_docs = {
        "README.md",
        "batch-and-streaming-ingestion.md",
        "bronze-provenance.md",
        "quality-policy-routing.md",
        "temporal-history-cdc.md",
        "governed-table-operations.md",
        "evidence-led-performance.md",
    }
    docs_dir = ROOT / "docs" / "decisions"

    assert {path.name for path in docs_dir.glob("*.md")} >= decision_docs
    assert (ROOT / "docs" / "production-readiness.md").exists()
    for filename in decision_docs:
        text = (docs_dir / filename).read_text(encoding="utf-8")
        assert "Decision state" in text
        assert "Evidence state" in text
        assert "Reconsider when" in text


def test_architecture_assets_use_official_unmodified_icons() -> None:
    svg = ROOT / "portfolio/architecture/quality-critical-lakehouse.svg"
    png = ROOT / "portfolio/architecture/quality-critical-lakehouse.png"
    source = json.loads(
        (ROOT / "portfolio/architecture/icon-source.json").read_text(encoding="utf-8")
    )

    assert svg.exists()
    assert png.exists()
    assert png.stat().st_size > 100_000
    assert len(list((ROOT / "portfolio/architecture/icons").glob("*.svg"))) >= 8
    assert source["publisher"] == "Microsoft"
    assert source["icons_modified"] is False
    assert "Azure_Public_Service_Icons_V24.zip" in source["archive"]


def test_architecture_png_build_does_not_embed_metadata() -> None:
    builder = (ROOT / "scripts/build-architecture.mjs").read_text(encoding="utf-8")

    assert ".withMetadata" not in builder


def test_site_and_pdf_build_contracts_are_declared() -> None:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    assert package["private"] is True
    assert package["scripts"]["build"] == (
        "npm run sync:content && npm run build:architecture "
        "&& npm run build:evidence-visuals && npm run build:manifest "
        "&& npm run build:pdf && npm run build:site"
    )
    assert package["scripts"]["build:evidence-visuals"] == (
        "node scripts/build-evidence-visuals.mjs"
    )
    assert package["scripts"]["build:manifest"] == (
        "node scripts/build-evidence-manifest.mjs"
    )
    assert "sourcemap" in (ROOT / "vite.config.ts").read_text(encoding="utf-8")
    assert (ROOT / "scripts/build-pdf.mjs").exists()
    assert (ROOT / "scripts/build-evidence-visuals.mjs").exists()
    assert (ROOT / "scripts/build-evidence-manifest.mjs").exists()
    assert (ROOT / "portfolio/site/index.html").exists()


def test_pdf_builder_detects_jpeg_content_in_screenshot_files() -> None:
    builder = (ROOT / "scripts/build-pdf.mjs").read_text(encoding="utf-8")

    assert "const isJpeg" in builder
    assert "bytes[0] === 0xff" in builder
    assert "pdf.embedJpg(bytes)" in builder
