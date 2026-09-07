import { test, expect } from "@playwright/test";
import { login, trackPageErrors } from "./fixtures";

const NAV_PAGES: Array<{ href: string; heading: string | RegExp }> = [
  { href: "/dashboard", heading: "City Heat Overview" },
  { href: "/map", heading: "Heat Map" },
  { href: "/hotspots", heading: "Hotspots" },
  { href: "/drivers", heading: "Driver Analysis" },
  { href: "/predictions", heading: "Predictions" },
  { href: "/simulation", heading: "Simulation" },
  { href: "/optimization", heading: "Optimization" },
  { href: "/recommendations", heading: "Recommendations" },
  { href: "/comparison", heading: "Ward Comparison" },
  { href: "/reports", heading: "Reports" },
  { href: "/datasources", heading: "Data Sources & Model Status" },
  { href: "/settings", heading: "Settings" },
];

test.describe("Navigation", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  for (const { href, heading } of NAV_PAGES) {
    test(`sidebar link to ${href} renders without console/page errors`, async ({ page }) => {
      const errors = trackPageErrors(page);
      await page.goto(href);
      await expect(page.getByRole("heading", { name: heading }).first()).toBeVisible({ timeout: 15_000 });
      expect(errors, `unexpected errors on ${href}:\n${errors.join("\n")}`).toEqual([]);
    });
  }

  test("admin nav item is hidden for a non-admin user", async ({ page }) => {
    await expect(page.getByRole("link", { name: "Admin" })).toHaveCount(0);
  });

  test("non-admin visiting /admin directly is redirected to /dashboard", async ({ page }) => {
    await page.goto("/admin");
    await page.waitForURL("**/dashboard");
  });
});
