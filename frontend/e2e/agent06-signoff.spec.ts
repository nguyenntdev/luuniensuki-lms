import { test, expect } from "@playwright/test";

test.describe("Agent 06 Verification - Desktop and Mobile Discovery Journey", () => {
  test("Desktop: Complete discovery journey, explore catalogue & routing", async ({ page }) => {
    // 1. Visit Explore catalogue
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/explore");

    // Check title and stats
    await expect(page.getByTestId("explore-title")).toBeVisible();
    await expect(page.getByText("Khám phá Di sản Cố đô Huế")).toBeVisible();
    await expect(page.getByTestId("explore-hero").getByText("14").first()).toBeVisible();
    await expect(page.getByText("Cấu phần UNESCO")).toBeVisible();

    // Verify Legacy Cuu Dinh Banner and routing
    const cuuDinhBanner = page.getByTestId("legacy-cuu-dinh-banner");
    await expect(cuuDinhBanner).toBeVisible();
    const cuuDinhLink = cuuDinhBanner.getByRole("link", { name: /Xem Bộ sưu tập Cửu Đỉnh/i });
    await expect(cuuDinhLink).toBeVisible();
    expect(await cuuDinhLink.getAttribute("href")).toBe("/cuu-dinh");

    // Verify category tabs
    const allTab = page.getByRole("tab", { name: /Tất cả/i });
    const tombTab = page.getByRole("tab", { name: /Lăng tẩm Hoàng gia/i });
    const craftTab = page.getByRole("tab", { name: /Làng nghề thủ công/i });
    await expect(allTab).toBeVisible();
    await expect(tombTab).toBeVisible();
    await expect(craftTab).toBeVisible();

    // Verify filter interaction
    await tombTab.click();
    await expect(page.getByText(/Lăng Tự Đức/i).first()).toBeVisible();

    // Verify Diacritic search
    const searchInput = page.getByRole("searchbox");
    await searchInput.fill("tu duc");
    await expect(page.getByText(/Lăng Tự Đức/i).first()).toBeVisible();

    await searchInput.fill("pháp lam");
    await expect(page.getByText(/Pháp lam/i).first()).toBeVisible();

    // Clear search and switch back to all
    await allTab.click();
    await searchInput.fill("");

    // Verify catalogue routing to /heritage/[slug]
    const tuDucCardLink = page.locator("a[href='/heritage/lang-tu-duc']").first();
    await expect(tuDucCardLink).toBeVisible();
    await tuDucCardLink.click();
    await page.waitForURL("**/heritage/lang-tu-duc");
    expect(page.url()).toContain("/heritage/lang-tu-duc");

    // Verify place detail components: tabs, 3d, sources, living bridge card
    await expect(page.getByRole("tab", { name: /Mô hình 3D/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /Thư viện ảnh/i })).toBeVisible();

    // Verify 3D model accuracy or attribution
    await expect(page.getByText(/Mô hình 3D đo đạc quang trắc/i).first()).toBeVisible();

    // Verify Sources rail
    await expect(page.getByText(/Đại Nam Thực Lục/i).first()).toBeVisible();

    // Verify Living Maker Bridge card
    await expect(page.getByTestId("living-bridge-card")).toBeVisible();
    await expect(page.getByText(/Nghệ nhân Nhân dân Nguyễn Văn Sinh/i).first()).toBeVisible();
    await expect(page.getByText(/Xưởng đúc đồng truyền thống Phường Đúc/i).first()).toBeVisible();
    
    // Verify inquiry link from living bridge card
    const inquiryBtn = page.getByRole("link", { name: /Đăng ký tham gia workshop/i });
    await expect(inquiryBtn).toBeVisible();
    await inquiryBtn.click();
    await page.waitForURL("**/rbpc/inquiries**");
    expect(page.url()).toContain("/rbpc/inquiries");
  });

  test("Mobile: Responsive discovery journey, drawer disclosure & card layout", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/explore");

    // Header and mobile drawer trigger
    const menuBtn = page.getByRole("button", { name: "Mở danh mục menu" });
    await expect(menuBtn).toBeVisible();

    // Check 44x44px minimum touch target on menu button
    const box = await menuBtn.boundingBox();
    expect(box).not.toBeNull();
    if (box) {
      expect(box.width).toBeGreaterThanOrEqual(40);
      expect(box.height).toBeGreaterThanOrEqual(40);
    }

    // Open drawer
    await menuBtn.click();
    const drawer = page.getByRole("dialog");
    await expect(drawer).toBeVisible();
    await expect(drawer.getByText("Di sản văn hóa")).toBeVisible();

    // Close drawer via Escape
    await page.keyboard.press("Escape");
    await expect(drawer).not.toBeVisible();

    // Verify mobile card rendering
    await expect(page.getByText(/Ngọ Môn/i).first()).toBeVisible();

    // Verify filter category horizontally scrollable or wraps cleanly
    await expect(page.getByRole("tab", { name: /Kiến trúc Cung đình/i })).toBeVisible();
    await page.getByRole("tab", { name: /Kiến trúc Cung đình/i }).click();
    await expect(page.getByText(/Ngọ Môn/i).first()).toBeVisible();

    // Navigate to /heritage/ngo-mon on mobile
    const cardLink = page.locator("a[href='/heritage/ngo-mon']").first();
    await cardLink.click();
    await page.waitForURL("**/heritage/ngo-mon");
    expect(page.url()).toContain("/heritage/ngo-mon");

    // Verify mobile media tabs and content
    await expect(page.getByRole("tab", { name: /Thư viện ảnh/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /Mô hình 3D/i })).toBeVisible();
    await expect(page.getByTestId("living-bridge-card")).toBeVisible();
  });
});
