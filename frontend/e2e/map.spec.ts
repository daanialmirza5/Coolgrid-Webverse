import { test, expect } from "@playwright/test";
import { login, trackPageErrors } from "./fixtures";

test.describe("Heat map", () => {
  test("renders ward polygons and supports layer toggling + selection", async ({ page }) => {
    const errors = trackPageErrors(page);
    await login(page);
    await page.goto("/map");
    await expect(page.getByRole("heading", { name: "Heat Map" })).toBeVisible();

    // MapLibre needs a moment to load its (local, no-external-tiles) style and paint.
    await page.waitForTimeout(2000);
    const canvas = page.locator("canvas").first();
    await expect(canvas).toBeVisible();

    // Layer toggle buttons are present and switchable.
    for (const layer of ["Land Surface Temperature", "Heat Risk Level", "Vegetation Cover", "Built-up Density", "Population"]) {
      await page.click(`button:has-text("${layer}")`);
      await expect(page.getByText(layer, { exact: false }).first()).toBeVisible();
    }

    // Clicking a ward on the canvas selects it and shows the detail card.
    const box = await canvas.boundingBox();
    if (box) {
      await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
      await page.waitForTimeout(500);
    }

    expect(errors).toEqual([]);
  });
});

test.describe("Heat map in dark mode", () => {
  // Regression test for a real bug: MapLibre's canvas painted over sibling
  // overlays (the legend, the ward-detail card) regardless of DOM order or
  // z-index-less absolute positioning, and its background/outline colors
  // were hardcoded light-mode values -- both invisible in light mode by
  // coincidence, both a broken-looking jumble of a bright box mid-dark-UI
  // once an OS dark theme was active. Fixed with explicit z-index on the
  // overlays and theme-aware colors on the map itself.
  test.use({ colorScheme: "dark" });

  test("legend has a higher stacking order than the map canvas", async ({ page }) => {
    await login(page);
    await page.goto("/map");
    await page.waitForTimeout(2000);

    // "Cooler"/"Hotter" only appear in the legend's gradient bar labels (the
    // layer-toggle buttons above just say "Land Surface Temperature"), so
    // this unambiguously targets the legend card itself.
    const legendTitle = page.getByText("Cooler", { exact: true });
    await expect(legendTitle).toBeVisible();

    // The regression was a missing z-index on the legend's wrapper, which let
    // MapLibre's canvas paint over it despite coming first in DOM order.
    // (elementFromPoint isn't usable here: the wrapper is deliberately
    // pointer-events:none so map panning/clicks pass through it, and that
    // makes hit-testing APIs report the canvas regardless of paint order.)
    const stackedAboveCanvas = await page.evaluate(() => {
      const canvas = document.querySelector("canvas");
      const legendWrapper = document.querySelector(".pointer-events-none.absolute.bottom-4.left-4");
      if (!canvas || !legendWrapper) return false;
      const canvasZ = Number(getComputedStyle(canvas).zIndex) || 0;
      const legendZ = Number(getComputedStyle(legendWrapper).zIndex) || 0;
      // Either the legend wins on z-index, or it's later in DOM order with
      // an equal-or-greater z-index (both stack above in that case).
      return legendZ > canvasZ || (legendZ === canvasZ && !!(canvas.compareDocumentPosition(legendWrapper) & Node.DOCUMENT_POSITION_FOLLOWING));
    });
    expect(stackedAboveCanvas).toBe(true);
  });
});
