import { test } from "@playwright/test";
import path from "path";
import fs from "fs";
import { login, DEMO_USER } from "../e2e/fixtures";

/**
 * Captures real browser screenshots of the live app into docs/screenshots/
 * for the README. Not a real test (no assertions) -- see
 * playwright.screenshots.config.ts for why this runs separately from the
 * main E2E suite.
 */
const OUT_DIR = path.join(__dirname, "..", "..", "docs", "screenshots");
fs.mkdirSync(OUT_DIR, { recursive: true });

test("capture full-journey screenshots", async ({ page }) => {
  test.setTimeout(120_000);

  async function shot(name: string) {
    await page.screenshot({ path: path.join(OUT_DIR, name) });
    console.log("captured", name);
  }

  // Turbopack's dev server compiles each route on first request, which can
  // take several seconds -- long enough to catch a loading spinner mid-shot.
  // Warm every route once before the real capture pass so every screenshot
  // below hits an already-compiled route.
  await login(page);
  await page.waitForTimeout(1000);
  const topHotspotCardWarm = page.locator("main button", { hasText: "°C" }).first();
  await topHotspotCardWarm.waitFor({ state: "visible", timeout: 15000 });
  await topHotspotCardWarm.click();
  await page.waitForURL("**/hotspots/**");
  const warmWardId = page.url().split("/hotspots/")[1];
  for (const p of ["map", "drivers", "predictions", "simulation", "optimization", "recommendations", "reports"]) {
    await page.goto(`/${p}?ward=${warmWardId}`);
    await page.waitForTimeout(500);
  }

  // 01 - Landing page
  await page.goto("/");
  await page.waitForTimeout(500);
  await shot("01-landing-page.png");

  // 02 - Login
  await page.goto("/login");
  await page.waitForTimeout(500);
  await shot("02-login.png");

  // Log in for real
  await page.fill("#email", DEMO_USER.email);
  await page.fill("#password", DEMO_USER.password);
  await page.click('button[type="submit"]');
  await page.waitForURL("**/dashboard");
  await page.getByText("City Heat Overview").waitFor({ timeout: 10000 });
  await page.locator("canvas").first().waitFor({ timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(1500);

  // 03 - Dashboard
  await shot("03-dashboard.png");

  // 04 - Heat map
  await page.goto("/map");
  await page.getByRole("heading", { name: "Heat Map" }).waitFor({ timeout: 10000 });
  await page.locator("canvas").first().waitFor({ timeout: 10000 });
  await page.waitForTimeout(1200);
  await shot("04-heat-map.png");

  // Select the top hotspot from the dashboard to drive the rest of the journey
  await page.goto("/dashboard");
  await page.waitForTimeout(1000);
  const topHotspotCard = page.locator("main button", { hasText: "°C" }).first();
  await topHotspotCard.waitFor({ state: "visible", timeout: 15000 });
  await topHotspotCard.click();
  await page.waitForURL("**/hotspots/**");
  await page.getByText("Top heat drivers").waitFor({ timeout: 10000 });
  // The driver mini-chart (Recharts) grows its bars in with a mount
  // animation after the surrounding text is already visible; wait for that
  // to settle so the screenshot doesn't catch empty/zero-height bars.
  await page.waitForTimeout(1500);
  const wardId = page.url().split("/hotspots/")[1];

  // 05 - Hotspot details
  await shot("05-hotspot-details.png");

  // 06 - Driver analysis
  await page.click('button:has-text("Driver analysis")');
  await page.waitForURL("**/drivers?ward=**");
  await page.getByText("Driver contributions").waitFor({ timeout: 15000 });
  await page.waitForTimeout(500);
  await shot("06-driver-analysis.png");

  // 07 - Prediction
  await page.goto(`/predictions?ward=${wardId}`);
  await page.getByText("Predicted land surface temperature").waitFor({ timeout: 15000 });
  await page.waitForTimeout(500);
  await shot("07-prediction.png");

  // 08 - Simulation (before running)
  await page.goto(`/simulation?ward=${wardId}`);
  await page.getByText("Intervention coverage").waitFor({ timeout: 15000 });
  const sliders = page.locator('input[type="range"]');
  await sliders.nth(0).fill("30");
  await sliders.nth(1).fill("40");
  await page.waitForTimeout(300);
  await shot("08-simulation.png");

  // 09 - Simulation results
  await page.click('button:has-text("Run simulation")');
  await page.getByText("Expected cooling").waitFor({ timeout: 20000 });
  await page.waitForTimeout(500);
  await shot("09-simulation-results.png");

  // 10 - Optimization
  await page.goto(`/optimization?ward=${wardId}`);
  await page.getByRole("heading", { name: "Constraints" }).waitFor({ timeout: 15000 });
  await page.click('button:has-text("Run optimization")');
  await page.getByText("Score").first().waitFor({ timeout: 30000 });
  await page.waitForTimeout(500);
  await shot("10-optimization.png");

  // 11 - Recommendations
  await page.click('button:has-text("View recommendations")');
  await page.waitForURL("**/recommendations?ward=**");
  await page.getByText("Rank 1").first().waitFor({ timeout: 15000 });
  await page.waitForTimeout(500);
  await shot("11-recommendations.png");

  // 12 - Report: count existing "ready" rows first so we wait for a NEW one
  // (the report list accumulates history across runs, so a generic "ready"
  // text match could resolve against an older row while this run's row
  // still says "generating").
  await page.goto("/reports");
  await page.getByText("Generate a new report").waitFor({ timeout: 15000 });
  // Wait for the initial report list fetch to finish before taking the
  // baseline count -- otherwise the count below can capture a mid-fetch
  // snapshot, and the wait after clicking resolves as soon as that same
  // initial fetch finishes populating the list, not because of the new report.
  await page.waitForLoadState("networkidle");
  const readyCountBefore = await page.getByText("ready", { exact: true }).count();
  await page.click('button:has-text("Generate report")');
  await page.getByRole("button", { name: "Generate report" }).waitFor({ timeout: 30000 });
  await page.waitForFunction(
    (before) => document.body.innerText.split("ready").length - 1 > before,
    readyCountBefore,
    { timeout: 10000 }
  );
  await page.waitForTimeout(500);
  await shot("12-report.png");
});
