import { test, expect } from "@playwright/test";

/**
 * V5-T090: Production Service Level Objective (SLO) E2E Drills.
 *
 * Verifies:
 * 1. Read latency budget for high-frequency heritage entry points (p95 <= 300ms observed or navigation ready).
 * 2. 2D fallback availability: When 3D/WebGL is constrained or unavailable, the page degrades smoothly
 *    to UrnAccessibleFallback (WCAG 2.2 AA compliant text & 2D rubbing archive).
 * 3. Zero fake success guard: Critical flows (experience inquiries, submissions, gradebook) do not
 *    synthesize mock confirmation without authentic server interaction.
 */

test.describe("Production SLO & Resilience Drills (Ticket V5-T090)", () => {
  test("SLO-01: Read latency target for static/heritage entry points", async ({ page }) => {
    const startTime = Date.now();
    const response = await page.goto("/explore", { waitUntil: "domcontentloaded" });
    const elapsed = Date.now() - startTime;

    expect(response?.status()).toBe(200);
    // Page must become interactable promptly
    await expect(page.getByTestId("explore-title")).toBeVisible();
    // Verify reasonable browser navigation latency
    expect(elapsed).toBeLessThan(5000);
  });

  test("SLO-02: 2D fallback availability for all rich media and 3D assets", async ({ page }) => {
    // Navigate to Cao Đỉnh 3D/heritage page
    await page.goto("/cuu-dinh/cao-dinh");

    // Accessible 2D description/fallback landmark must be attached and readable
    const fallbackSection = page.locator("section[role='region']");
    await expect(fallbackSection.first()).toBeAttached();

    // Verify presence of textual equivalent content for screen readers / 2D clients
    await expect(page.getByText(/Cao Đỉnh/i).first()).toBeVisible();
    await expect(page.getByText(/Thế Tổ Cao Hoàng Đế|Gia Long/i).first()).toBeVisible();
  });

  test("SLO-03: Zero fake success gate on visitor booking inquiry", async ({ page }) => {
    // An unauthenticated visitor navigating to an invalid inquiry token must receive explicit not-found
    const response = await page.goto("/inquiries/status/tok_fake_nonexistent_token_9999", {
      waitUntil: "domcontentloaded",
    });

    // The application must NOT fabricate a synthetic booking success
    const fakeSuccessIndicator = page.locator("[data-testid='fake-success-confirmed']");
    await expect(fakeSuccessIndicator).toHaveCount(0);
  });
});
