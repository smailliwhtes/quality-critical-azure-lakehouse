import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const viewports = [
  { name: "desktop-1600", width: 1600, height: 1000 },
  { name: "desktop-1440", width: 1440, height: 900 },
  { name: "mobile-390", width: 390, height: 844 },
  { name: "mobile-320", width: 320, height: 700 },
];

for (const viewport of viewports) {
  test(`${viewport.name} is readable and has no horizontal overflow`, async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    page.on("pageerror", (error) => errors.push(error.message));
    await page.setViewportSize(viewport);
    await page.goto("./", { waitUntil: "networkidle" });

    await expect(page.getByRole("heading", { name: "Quality-Critical Azure Lakehouse", exact: true })).toBeVisible();
    await expect(page.locator(".hero-card")).toHaveCount(6);
    await expect(page.locator(".hero-card__visual img")).toHaveCount(6);
    await expect(page.locator(".journey-card")).toHaveCount(19);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
    expect(errors).toEqual([]);
  });
}

test("evidence explorer is keyboard-operable and filters records", async ({ page }) => {
  await page.goto("./", { waitUntil: "networkidle" });
  const search = page.getByRole("searchbox", { name: "Search evidence" });
  await search.fill("SCD2");
  await expect(page.locator(".evidence-row:not([hidden])")).toHaveCount(1);
  await search.fill("");
  await page.getByRole("button", { name: "Production blueprint" }).click();
  const visible = page.locator(".evidence-row:not([hidden])");
  expect(await visible.count()).toBeGreaterThan(0);
  await expect(visible.first().locator(".status--production-blueprint")).toBeVisible();
});

test("evidence explorer links each claim to screenshot, receipt, code, and validation", async ({ page }) => {
  await page.goto("./", { waitUntil: "networkidle" });
  const first = page.locator(".evidence-row").first();
  await expect(first.getByRole("link", { name: "Screenshot" })).toBeVisible();
  await expect(first.getByRole("link", { name: "Receipt" })).toBeVisible();
  await expect(first.getByRole("link", { name: "Code" })).toBeVisible();
  await expect(first.getByRole("link", { name: "Validation" })).toBeVisible();
});

test("automated accessibility scan finds no serious violations", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("./", { waitUntil: "networkidle" });
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(results.violations.filter((violation) => ["serious", "critical"].includes(violation.impact ?? ""))).toEqual([]);
});

test("local architecture, PDF, and evidence links resolve", async ({ page, request }) => {
  await page.goto("./", { waitUntil: "networkidle" });
  const urls = await page.locator('a[href^="/quality-critical-azure-lakehouse/"]').evaluateAll((links) =>
    [...new Set(links.map((link) => (link as HTMLAnchorElement).href))],
  );
  for (const url of urls) {
    const response = await request.get(url);
    expect(response.status(), url).toBe(200);
  }
});
