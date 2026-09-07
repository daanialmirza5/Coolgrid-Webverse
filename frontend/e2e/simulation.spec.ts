import { test, expect } from "@playwright/test";
import { login, trackPageErrors } from "./fixtures";

test.describe("Simulation", () => {
  test("ward picker appears with no ward selected, then simulating shows cooling results", async ({ page }) => {
    const errors = trackPageErrors(page);
    await login(page);
    await page.goto("/simulation");
    await expect(page.getByText("Select a ward to test cooling interventions")).toBeVisible();

    await page.locator(".cursor-pointer").first().click();
    await page.waitForURL("**/simulation?ward=**");
    await expect(page.getByText("Intervention coverage")).toBeVisible();

    await expect(page.getByText(/run a simulation to see cooling impact/i)).toBeVisible();
    await page.locator('input[type="range"]').first().fill("30"); // Urban Trees coverage
    await page.click('button:has-text("Run simulation")');
    await expect(page.getByText("Expected cooling")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("Land required")).toBeVisible();
    await expect(page.getByText("Population benefited")).toBeVisible();
    expect(errors).toEqual([]);
  });

  test("running with all interventions at 0% shows a validation error, not a crash", async ({ page }) => {
    await login(page);
    await page.goto("/simulation");
    await page.locator(".cursor-pointer").first().click();
    await page.waitForURL("**/simulation?ward=**");
    await page.click('button:has-text("Run simulation")');
    await expect(page.getByText(/set at least one intervention/i)).toBeVisible();
  });
});
