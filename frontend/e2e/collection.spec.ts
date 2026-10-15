import { test, expect } from '@playwright/test';

test('should display collection and filter items', async ({ page }) => {
  // Login first
  const email = `test-col-${Date.now()}@example.com`;
  const password = 'password123';
  const name = 'Collection User';

  await page.goto('/login');
  await page.getByRole('button', { name: 'Đăng ký' }).click();
  await page.getByPlaceholder('Sử Quan Tập Sự').fill(name);
  await page.getByPlaceholder('you@example.com').fill(email);
  await page.getByPlaceholder('••••••••').fill(password);
  await page.getByRole('button', { name: 'Tạo tài khoản' }).click();
  await expect(page).toHaveURL(/\/dashboard/);

  // Go to collection
  await page.goto('/collection');
  
  await expect(page.getByText('Bộ sưu tập của bạn')).toBeVisible();
  
  // Wait for loading to finish (stats visible)
  await expect(page.getByText('Tổng họa tiết')).toBeVisible();

  // Test Status Filter: Discovered (should be empty for new user)
  await page.getByLabel('Trạng thái').selectOption('discovered'); // value is lowercase
  await expect(page.getByText('Không tìm thấy họa tiết nào phù hợp với bộ lọc của bạn.')).toBeVisible();
  
  // Clear filters
  await page.getByRole('button', { name: 'Xóa tất cả bộ lọc' }).click();
  await expect(page.getByText('Không tìm thấy họa tiết nào phù hợp với bộ lọc của bạn.')).not.toBeVisible();
  
  // Test Search Filter (random string)
  await page.getByLabel('Tìm kiếm').fill('NonExistentMotifXYZ');
  await expect(page.getByText('Không tìm thấy họa tiết nào phù hợp với bộ lọc của bạn.')).toBeVisible();
});
