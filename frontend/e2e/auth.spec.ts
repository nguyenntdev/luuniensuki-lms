import { test, expect } from '@playwright/test';

test('should register and land on post-auth flow', async ({ page }) => {
  const email = `test${Date.now()}@example.com`;
  const password = 'password123';
  const name = 'Test User';

  await page.goto('/login');

  await page.getByRole('button', { name: 'Đăng ký' }).click();

  await page.getByPlaceholder('Sử Quan Tập Sự').fill(name);
  await page.getByPlaceholder('you@example.com').fill(email);
  await page.getByPlaceholder('••••••••').fill(password);

  await page.getByRole('button', { name: 'Tạo tài khoản' }).click();

  await expect(page).toHaveURL(/\/dashboard/);

  // New users can either see the dashboard hero or the starting-path gate.
  await expect(
    page.getByRole('heading', {
      name: /Tiến Trình Hôm Nay|Chọn lộ trình bắt đầu/,
    }),
  ).toBeVisible();
});
