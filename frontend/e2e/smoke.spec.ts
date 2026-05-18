import { expect, test } from "@playwright/test";

test("login page renders and toggles auth modes @smoke", async ({ page }) => {
  await page.goto("/login");

  await expect(
    page.getByRole("heading", { name: "Lưu Niên Sử Kí" }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Đăng nhập" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Đăng ký" })).toBeVisible();
  await expect(page.getByPlaceholder("Sử Quan Tập Sự")).toHaveCount(0);

  await page.getByRole("button", { name: "Đăng ký" }).click();
  await expect(page.getByPlaceholder("Sử Quan Tập Sự")).toBeVisible();

  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page.getByPlaceholder("Sử Quan Tập Sự")).toHaveCount(0);
});
