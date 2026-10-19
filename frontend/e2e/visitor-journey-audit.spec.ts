import { test, expect } from "@playwright/test";

test.describe("First-Time Visitor Journey & Usability Audit (RBPC 2026)", () => {
  test("Step 1: Homepage arrival and comprehension", async ({ page }) => {
    await page.goto("/");

    // 1. Brand identity and title
    await expect(page).toHaveTitle(/Lưu Niên/i);

    // 2. Main navigation and skip link
    const skipLink = page.locator("a[href='#main-content']");
    await expect(skipLink).toBeAttached();

    // 3. Header branding
    const brandMonogram = page.locator("header").getByText("LN");
    await expect(brandMonogram.first()).toBeVisible();

    // 4. Primary CTA to explore
    const exploreLinks = page.locator("a[href='/explore']");
    await expect(exploreLinks.first()).toBeVisible();
  });

  test("Step 2: Explore catalogue & category filter interaction", async ({ page }) => {
    await page.goto("/explore");

    // 1. Explore hero title and statistics
    await expect(page.getByTestId("explore-title")).toBeVisible();
    await expect(page.getByText("Khám phá Di sản Cố đô Huế")).toBeVisible();
    await expect(page.getByText("Cấu phần UNESCO")).toBeVisible();

    // 2. Legacy Cửu Đỉnh collection showcase banner
    await expect(page.getByTestId("legacy-cuu-dinh-banner")).toBeVisible();
    await expect(
      page.getByText("Bộ sưu tập Cửu Đỉnh & 162 Bản đúc nổi")
    ).toBeVisible();

    // 3. Category tabs
    await expect(page.getByRole("tab", { name: /Tất cả/i })).toBeVisible();
    await expect(
      page.getByRole("tab", { name: /Kiến trúc Cung đình/i })
    ).toBeVisible();
    await expect(
      page.getByRole("tab", { name: /Lăng tẩm Hoàng gia/i })
    ).toBeVisible();
    await expect(
      page.getByRole("tab", { name: /Làng nghề thủ công/i })
    ).toBeVisible();

    // 4. Click category tab: Lăng tẩm Hoàng gia
    await page.getByRole("tab", { name: /Lăng tẩm Hoàng gia/i }).click();

    // 5. Verify filtered list contains royal tombs (e.g. Lăng Tự Đức)
    await expect(page.getByText(/Lăng Tự Đức/i)).toBeVisible();
  });

  test("Step 3: Diacritic-tolerant search across Vietnamese and English", async ({ page }) => {
    await page.goto("/explore");

    const searchInput = page.getByRole("searchbox");
    await expect(searchInput).toBeVisible();

    // Test 1: Search without diacritics "tu duc"
    await searchInput.fill("tu duc");
    await expect(page.getByText(/Lăng Tự Đức/i)).toBeVisible();

    // Test 2: Search with full Vietnamese diacritics "Tự Đức"
    await searchInput.fill("Tự Đức");
    await expect(page.getByText(/Lăng Tự Đức/i)).toBeVisible();

    // Test 3: Search English equivalent "Meridian Gate"
    await searchInput.fill("Meridian Gate");
    await expect(page.getByText(/Ngọ Môn/i).first()).toBeVisible();

    // Test 4: Search UNESCO Reference ID "678-001"
    await searchInput.fill("678-001");
    await expect(page.getByText(/Ngọ Môn/i).first()).toBeVisible();

    // Test 5: Search living craft village "phuong duc"
    await searchInput.fill("phuong duc");
    await expect(
      page.getByText(/Phường Đúc/i).first()
    ).toBeVisible();

    // Test 6: Zero-result search shows empty state and reset action
    await searchInput.fill("nonexistentquery12345");
    await expect(
      page.getByText("Không tìm thấy di sản phù hợp")
    ).toBeVisible();
    const resetBtn = page.getByRole("button", { name: "Xóa toàn bộ bộ lọc" });
    await expect(resetBtn).toBeVisible();
    await resetBtn.click();
    await expect(searchInput).toHaveValue("");
    await expect(page.getByText(/Ngọ Môn/i).first()).toBeVisible();
  });

  test("Step 4: View toggle between Grid and Map showcase", async ({ page }) => {
    await page.goto("/explore");

    // Toggle to Map view
    const mapToggle = page.getByRole("button", { name: /Bản đồ/i });
    await expect(mapToggle).toBeVisible();
    await mapToggle.click();

    // Verify Map showcase presentation
    await expect(page.getByText("Bản đồ Di sản Cố đô Huế")).toBeVisible();
    await expect(
      page.getByRole("link", { name: /Mở Bản đồ Không gian Đầy đủ/i })
    ).toBeVisible();

    // Toggle back to Grid
    const returnGridBtn = page.getByRole("button", { name: "Quay lại dạng lưới" });
    await expect(returnGridBtn).toBeVisible();
    await returnGridBtn.click();
    await expect(page.getByText(/Ngọ Môn/i).first()).toBeVisible();
  });

  test("Step 5: Educational roadmap journey (/learn)", async ({ page }) => {
    await page.goto("/learn");

    // 1. Page title and continuum header
    await expect(
      page.getByRole("heading", {
        name: "Từ Ký Ức Thư Tịch Hoàng Triều Đến Bàn Tay Người Thợ Hôm Nay",
      })
    ).toBeVisible();
    await expect(
      page.getByText("Khung kết nối giáo dục di sản LƯU NIÊN — 4 Chặng đồng hành")
    ).toBeVisible();

    // 2. Audience filter / phase tabs selector
    await expect(page.getByRole("tab", { name: "Tất cả 4 chặng" })).toBeVisible();

    // 3. Verify all 4 roadmap continuum phases
    await expect(
      page.getByRole("heading", { name: "Nền tảng Thư tịch" })
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Tương tác 3D & Bản đúc" })
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Thực địa & Nghệ nhân" })
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Khung Chứng chỉ 2027" })
    ).toBeVisible();
  });

  test("Step 6: Availability inquiry flow and validation (/rbpc/inquiries)", async ({ page }) => {
    await page.goto("/rbpc/inquiries");

    // 1. Inquiry title and honest non-commercial disclaimer
    await expect(
      page.getByRole("heading", {
        name: "Cổng Yêu Cầu & Tra Cứu Lịch Trải Nghiệm",
      })
    ).toBeVisible();
    await expect(
      page.getByText(/không thu phí trực tuyến tức thì/i).first()
    ).toBeVisible();

    // 2. Form fields are present and accessible
    await expect(page.getByLabel(/Họ và tên của bạn/i)).toBeVisible();
    await expect(page.getByRole("combobox", { name: /Chọn trải nghiệm/i })).toBeVisible();

    // 3. Tab switching between new inquiry and status lookup
    await expect(page.getByRole("tab", { name: /1. Gửi yêu cầu mới/i })).toBeVisible();
    await expect(page.getByRole("tab", { name: /2. Tra cứu tiến độ hồ sơ/i })).toBeVisible();
  });

  test("Navigation Shell Audit: Desktop header layout", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/explore");

    const header = page.locator("header");
    await expect(header).toBeVisible();

    // Exactly 1 desktop header visible
    await expect(page.locator("header:visible")).toHaveCount(1);

    // Desktop search trigger exists
    const searchTrigger = page.locator("header").getByRole("button", { name: /Tìm kiếm/i });
    if (await searchTrigger.count() > 0) {
      await expect(searchTrigger.first()).toBeVisible();
    }
  });

  test("Navigation Shell Audit: Mobile drawer disclosure", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/explore");

    // Verify mobile header top bar is visible
    const mobileHeader = page.locator("div.sticky.top-0");
    await expect(mobileHeader).toBeVisible();

    // Verify mobile bottom nav is visible
    const bottomNav = page.locator("nav[aria-label='Điều hướng chính']").last();
    await expect(bottomNav).toBeVisible();

    // Open mobile drawer
    const menuTrigger = page.getByRole("button", { name: "Mở danh mục menu" });
    await expect(menuTrigger).toBeVisible();
    await menuTrigger.click();

    // Drawer dialog opens
    const drawerDialog = page.getByRole("dialog");
    await expect(drawerDialog).toBeVisible();
    await expect(drawerDialog.getByText("Di sản văn hóa")).toBeVisible();
    await expect(drawerDialog.locator("a[href='/cuu-dinh']")).toBeVisible();
    await expect(drawerDialog.locator("a[href='/atlas']")).toBeVisible();
    await expect(drawerDialog.locator("a[href='/map']")).toBeVisible();
  });
});
