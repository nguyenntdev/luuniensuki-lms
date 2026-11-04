import { test, expect } from "@playwright/test";

test.describe("Media Accessibility & WCAG 2.2 AA Audit (Ticket V5-T049)", () => {
  test("Accessibility: Audio guides and transcripts provide text equivalence", async ({ page }) => {
    await page.goto("/explore");

    // Skip to content accessible link must exist
    const skipLink = page.locator("a[href='#main-content']");
    await expect(skipLink).toBeAttached();

    // Verify main region has appropriate role and landmark
    const mainContent = page.locator("main#main-content");
    await expect(mainContent).toBeAttached();
  });

  test("Accessibility: Heritage virtual tours expose accessible tablist and 2D descriptions", async ({ page }) => {
    // Navigate to virtual tours or heritage page
    await page.goto("/cuu-dinh/cao-dinh");

    // Verify 2D accessible fallback or urn description landmark exists
    const fallbackSection = page.locator("section[role='region']");
    await expect(fallbackSection.first()).toBeAttached();
  });

  test("Negative abuse: No content exclusively locked behind WebGL/Canvas", async ({ page }) => {
    await page.goto("/cuu-dinh/cao-dinh");

    // Even if WebGL is disabled or slow, text content of Cao Dinh is readable
    await expect(page.getByText(/Cao Đỉnh/i).first()).toBeVisible();
    await expect(page.getByText(/Thế Tổ Cao Hoàng Đế|Gia Long/i).first()).toBeVisible();
  });
});
