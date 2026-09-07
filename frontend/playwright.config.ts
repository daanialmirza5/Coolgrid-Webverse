import { defineConfig, devices } from "@playwright/test";

/**
 * E2E tests against a real running backend + PostgreSQL (docker compose up -d,
 * migrations applied, demo data seeded -- see README.md#setup) AND a Next.js
 * dev server you start yourself first:
 *
 *   pnpm dev
 *
 * (Deliberately not using Playwright's `webServer` option to manage this:
 * Next.js 16 refuses to start a second dev server in the same project
 * directory at all while one is already running, which made Playwright's
 * own server-management lifecycle unreliable in practice. Starting it
 * yourself and pointing Playwright at `baseURL` is the pattern that's
 * actually been verified working.)
 *
 * PLAYWRIGHT_BASE_URL overrides the default if `pnpm dev` fell back to a
 * different port (it prints which one it picked, e.g. when 3000 is busy).
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // tests share one seeded demo dataset (e.g. accumulating reports); avoid cross-test races
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [["list"]],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
