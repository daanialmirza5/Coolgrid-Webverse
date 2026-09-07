import { defineConfig, devices } from "@playwright/test";

/**
 * Separate config for the one-off docs/screenshots/ capture pass (see
 * tools-e2e/capture-screenshots.spec.ts). Kept out of playwright.config.ts's
 * testDir so a normal `pnpm exec playwright test` run of the real E2E suite
 * never generates an extra demo report or takes screenshots as a side effect.
 *
 * Run with: pnpm exec playwright test --config=playwright.screenshots.config.ts
 */
export default defineConfig({
  testDir: "./tools-e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 120_000,
  reporter: [["list"]],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "off",
    screenshot: "off",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1600, height: 1000 } } }],
});
