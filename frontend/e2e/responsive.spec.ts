import { test, expect, devices } from "@playwright/test";
import { login } from "./fixtures";

const VIEWPORTS = {
  mobile: devices["iPhone 13"].viewport,
  tablet: { width: 768, height: 1024 },
};

const PAGES = ["/dashboard", "/map", "/hotspots", "/comparison", "/simulation", "/settings"];

for (const [sizeName, viewport] of Object.entries(VIEWPORTS)) {
  test.describe(`Responsive layout (${sizeName}, ${viewport.width}x${viewport.height})`, () => {
    test.use({ viewport });

    test(`no horizontal overflow on any page (${sizeName})`, async ({ page }) => {
      await login(page);
      for (const path of PAGES) {
        await page.goto(path);
        await page.waitForTimeout(800);
        const { scrollWidth, clientWidth } = await page.evaluate(() => ({
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        }));
        expect(scrollWidth, `${path} overflows horizontally at ${sizeName} (scrollWidth ${scrollWidth} > clientWidth ${clientWidth})`).toBeLessThanOrEqual(
          clientWidth + 1 // 1px rounding tolerance
        );
      }
    });
  });
}

test.describe("Mobile navigation drawer", () => {
  test.use({ viewport: devices["iPhone 13"].viewport });

  test("hamburger menu opens and closes the sidebar", async ({ page }) => {
    await login(page);
    const drawer = page.getByTestId("mobile-sidebar");
    await expect(drawer).toHaveCount(0);

    await page.getByRole("button", { name: "Open menu" }).click();
    await expect(drawer).toBeVisible();
    await expect(drawer.getByRole("link", { name: "Heat Map" })).toBeVisible();

    await page.getByRole("button", { name: "Close menu" }).click();
    await expect(drawer).toHaveCount(0);
  });
});
