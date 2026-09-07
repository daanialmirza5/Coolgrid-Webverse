import { test, expect } from "@playwright/test";
import { DEMO_USER, login, trackPageErrors } from "./fixtures";

test.describe("Authentication", () => {
  test("landing page loads and links to login/register", async ({ page }) => {
    const errors = trackPageErrors(page);
    await page.goto("/");
    await expect(page.getByText("CoolGrid").first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Sign in" }).first()).toBeVisible();
    expect(errors).toEqual([]);
  });

  test("register creates a new account and lands on the dashboard", async ({ page }) => {
    const email = `judge-${Date.now()}@example.com`;
    await page.goto("/register");
    await page.fill("#fullName", "Hackathon Judge");
    await page.fill("#email", email);
    await page.fill("#password", "JudgePass123");
    await page.click('button[type="submit"]');
    await page.waitForURL("**/dashboard");
    await expect(page.getByText("City Heat Overview")).toBeVisible();
  });

  test("login with demo credentials succeeds", async ({ page }) => {
    await login(page);
    await expect(page.getByText("City Heat Overview")).toBeVisible();
    await expect(page.getByText("Demo City Planner")).toBeVisible();
  });

  test("login with wrong password shows an error and does not navigate", async ({ page }) => {
    await page.goto("/login");
    await page.fill("#email", DEMO_USER.email);
    await page.fill("#password", "WrongPassword123");
    await page.click('button[type="submit"]');
    await expect(page.getByText(/incorrect email or password/i)).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("visiting a protected route while logged out redirects to /login", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForURL("**/login");
  });

  test("logout returns to /login and re-visiting a protected route redirects again", async ({ page }) => {
    await login(page);
    await page.click('button[title="Log out"]');
    await page.waitForURL("**/login");
    await page.goto("/dashboard");
    await page.waitForURL("**/login");
  });

  test("forgot password issues a demo reset token that can reset the password", async ({ page }) => {
    // Uses a freshly registered account so it doesn't disturb the shared demo user's password.
    const email = `reset-${Date.now()}@example.com`;
    await page.goto("/register");
    await page.fill("#fullName", "Reset Test");
    await page.fill("#email", email);
    await page.fill("#password", "OriginalPass123");
    await page.click('button[type="submit"]');
    await page.waitForURL("**/dashboard");
    await page.click('button[title="Log out"]');
    await page.waitForURL("**/login");

    await page.goto("/forgot-password");
    await page.fill("#email", email);
    await page.click('button:has-text("Send reset link")');
    await expect(page.locator("input[readonly]")).toBeVisible();

    await page.click("text=Continue to reset password");
    await page.waitForURL("**/reset-password**");
    await page.fill("#newPassword", "NewPassword456");
    await page.click('button:has-text("Update password")');
    await expect(page.getByText(/password updated/i)).toBeVisible();

    await page.click("text=Go to sign in");
    await page.waitForURL("**/login");
    await page.fill("#email", email);
    await page.fill("#password", "NewPassword456");
    await page.click('button[type="submit"]');
    await page.waitForURL("**/dashboard");
  });
});
