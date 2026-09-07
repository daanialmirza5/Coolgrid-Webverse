import type { Page } from "@playwright/test";

export const DEMO_USER = { email: "demo@coolgrid.app", password: "CoolGrid#Demo2026" };
export const ADMIN_USER = { email: "admin@coolgrid.app", password: "CoolGrid#Admin2026" };

export async function login(page: Page, user: { email: string; password: string } = DEMO_USER) {
  await page.goto("/login");
  await page.fill("#email", user.email);
  await page.fill("#password", user.password);
  await page.click('button[type="submit"]');
  await page.waitForURL("**/dashboard");
}

/** Collects console errors and failed requests during a test; call
 * `assertNoErrors()` at the end (or inspect `.errors` directly). */
export function trackPageErrors(page: Page) {
  const errors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(`[console] ${msg.text()}`);
  });
  page.on("pageerror", (err) => errors.push(`[pageerror] ${err.message}`));
  page.on("requestfailed", (req) => {
    // The MapLibre demo basemap host is deliberately not used, and a
    // best-effort logout call can be aborted by the immediate client-side
    // redirect that follows it -- neither indicates an app bug.
    if (req.url().includes("/api/auth/logout")) return;
    errors.push(`[requestfailed] ${req.url()} - ${req.failure()?.errorText}`);
  });
  return errors;
}
