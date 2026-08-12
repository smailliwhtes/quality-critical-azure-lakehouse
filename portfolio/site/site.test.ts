import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import content from "../content/project.json";

const root = resolve(import.meta.dirname, "../..");
const html = readFileSync(resolve(root, "portfolio/site/index.html"), "utf8");
const source = readFileSync(resolve(root, "portfolio/site/main.ts"), "utf8");
const css = readFileSync(resolve(root, "portfolio/site/styles.css"), "utf8");

describe("recruiter portfolio contract", () => {
  it("keeps one six-card recruiter path and 19 deep-dive chapters", () => {
    expect(content.hero_path).toHaveLength(6);
    expect(content.engineering_journey).toHaveLength(19);
  });

  it("declares semantic navigation and accessibility affordances", () => {
    expect(html).toContain("Skip to project");
    expect(source).toContain('aria-label="Primary navigation"');
    expect(source).toContain('aria-live="polite"');
    expect(source).toContain("alt=\"Batch files pass through Data Factory");
    expect(css).toContain(":focus-visible");
    expect(css).toContain("prefers-reduced-motion");
  });

  it("supports 320-pixel layouts without a fixed content width", () => {
    expect(css).toContain("min-width: 320px");
    expect(css).toContain("@media (max-width: 520px)");
    expect(css).not.toMatch(/width:\s*1600px/);
  });

  it("exposes all three evidence statuses and searchable evidence", () => {
    expect(source).toContain("VERIFIED");
    expect(source).toContain("DEMONSTRATED");
    expect(source).toContain("PRODUCTION_BLUEPRINT");
    expect(source).toContain("evidence-search");
    expect(source).toContain("applyEvidenceFilter");
  });
});
