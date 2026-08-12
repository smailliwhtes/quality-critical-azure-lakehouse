import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOCS = {
    "architecture.md",
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


def test_site_and_pdf_build_contracts_are_declared() -> None:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    assert package["private"] is True
    assert package["scripts"]["build"] == (
        "npm run sync:content && npm run build:architecture "
        "&& npm run build:pdf && npm run build:site"
    )
    assert "sourcemap" in (ROOT / "vite.config.ts").read_text(encoding="utf-8")
    assert (ROOT / "scripts/build-pdf.mjs").exists()
    assert (ROOT / "portfolio/site/index.html").exists()
