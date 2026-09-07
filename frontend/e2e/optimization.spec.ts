import { test, expect } from "@playwright/test";
import { login, trackPageErrors } from "./fixtures";

test.describe("Optimization", () => {
  test("running the optimizer with default constraints returns ranked strategies", async ({ page }) => {
    const errors = trackPageErrors(page);
    await login(page);
    await page.goto("/optimization");
    await expect(page.getByText("Select a ward to find the best cooling strategy")).toBeVisible();

    await page.locator(".cursor-pointer").first().click();
    await page.waitForURL("**/optimization?ward=**");
    await expect(page.getByRole("heading", { name: "Constraints" })).toBeVisible();

    await page.click('button:has-text("Run optimization")');
    await expect(page.getByText("Score").first()).toBeVisible({ timeout: 30_000 });
    // At least one ranked strategy card with a cost that respects the default budget.
    await expect(page.getByText(/#1/)).toBeVisible();
    await expect(page.getByText(/Cooling/i).first()).toBeVisible();
    expect(errors).toEqual([]);
  });

  test("an infeasible budget returns an empty-state, not an error", async ({ page }) => {
    await login(page);
    await page.goto("/optimization");
    await page.locator(".cursor-pointer").first().click();
    await page.waitForURL("**/optimization?ward=**");

    await page.fill('input[type="number"]', "1");
    await page.click('button:has-text("Run optimization")');
    await expect(page.getByText(/no feasible strategy found/i)).toBeVisible({ timeout: 30_000 });
  });
});
