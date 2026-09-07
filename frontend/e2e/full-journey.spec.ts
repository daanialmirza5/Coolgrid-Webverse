import { test, expect } from "@playwright/test";
import { login, trackPageErrors } from "./fixtures";

/**
 * The complete demo/judging flow:
 * LOGIN -> DASHBOARD -> SELECT AREA -> HOTSPOT -> DRIVER ANALYSIS ->
 * PREDICTION -> SIMULATION -> OPTIMIZATION -> REPORT -> LOGOUT
 *
 * One long test rather than several small ones because each step depends on
 * state produced by the previous one (the selected ward ID flows through
 * every subsequent page).
 */
test("complete user journey: login through report generation to logout", async ({ page }) => {
  const errors = trackPageErrors(page);

  // LOGIN
  await login(page);
  await expect(page.getByText("City Heat Overview")).toBeVisible();

  // DASHBOARD -> SELECT AREA (top hotspot card)
  await page.waitForTimeout(1000); // let the hotspot list finish loading
  const topHotspotCard = page.locator("main button", { hasText: "°C" }).first();
  await expect(topHotspotCard).toBeVisible({ timeout: 15_000 });
  await topHotspotCard.click();

  // HOTSPOT detail
  await page.waitForURL("**/hotspots/**");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const wardId = page.url().split("/hotspots/")[1];
  expect(wardId).toBeTruthy();
  await expect(page.getByText("Top heat drivers")).toBeVisible();

  // DRIVER ANALYSIS
  await page.click('button:has-text("Driver analysis")');
  await page.waitForURL("**/drivers?ward=**");
  await expect(page.getByText("Driver contributions")).toBeVisible();
  await expect(page.getByText(/is hot primarily due to/i)).toBeVisible();

  // PREDICTION
  await page.goto(`/predictions?ward=${wardId}`);
  await expect(page.getByText("Predicted land surface temperature")).toBeVisible();
  await expect(page.getByText(/not a guaranteed outcome/i)).toBeVisible();

  // SIMULATION
  await page.goto(`/simulation?ward=${wardId}`);
  await expect(page.getByText("Intervention coverage")).toBeVisible();
  const sliders = page.locator('input[type="range"]');
  await sliders.nth(0).fill("30"); // Urban Trees
  await sliders.nth(1).fill("40"); // Cool Roofs
  await page.click('button:has-text("Run simulation")');
  await expect(page.getByText("Expected cooling")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText("Population benefited")).toBeVisible();

  // OPTIMIZATION
  await page.goto(`/optimization?ward=${wardId}`);
  await expect(page.getByRole("heading", { name: "Constraints" })).toBeVisible();
  await page.click('button:has-text("Run optimization")');
  await expect(page.getByText("Score").first()).toBeVisible({ timeout: 30_000 });
  const optimizationRun = page.locator('button:has-text("View recommendations")');
  await expect(optimizationRun).toBeVisible();

  // RECOMMENDATIONS (reachable from the optimization result, matching the demo script)
  await optimizationRun.click();
  await page.waitForURL("**/recommendations?ward=**");
  await expect(page.getByText("Rank 1").first()).toBeVisible();

  // REPORT
  await page.goto("/reports");
  await expect(page.getByText("Generate a new report")).toBeVisible();
  await page.click('button:has-text("Generate report")');
  await expect(page.getByText("ready").first()).toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole("button", { name: /download pdf/i }).first()).toBeVisible();

  // LOGOUT
  await page.click('button[title="Log out"]');
  await page.waitForURL("**/login");

  // Protected route now redirects again.
  await page.goto("/dashboard");
  await page.waitForURL("**/login");

  expect(errors, `unexpected errors during journey:\n${errors.join("\n")}`).toEqual([]);
});
