import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests/site",
  fullyParallel: false,
  forbidOnly: true,
  retries: process.env.CI ? 1 : 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:4173/quality-critical-azure-lakehouse/",
    browserName: "chromium",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm exec vite -- preview --host 127.0.0.1 --port 4173",
    url: "http://127.0.0.1:4173/quality-critical-azure-lakehouse/",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
