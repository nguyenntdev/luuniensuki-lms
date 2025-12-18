import { test, expect } from '@playwright/test';

test('should register and login successfully', async ({ page }) => {
  const email = `test${Date.now()}@example.com`;
  const password = 'password123';
  const name = 'Test User';

  await page.goto('/login');

  // Switch to Register mode
  await page.getByRole('button', { name: 'Register' }).click();

  // Fill registration form
  await page.getByPlaceholder('Sử Quan Tập Sự').fill(name);
  await page.getByPlaceholder('you@example.com').fill(email);
  await page.getByPlaceholder('••••••••').fill(password);

  // Submit
  await page.getByRole('button', { name: 'Tạo tài khoản' }).click();

  // Should redirect to dashboard
  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByText(`Welcome, ${name}`)).toBeVisible();

  // Logout
  await page.getByRole('button', { name: 'Logout' }).click();
  await expect(page.getByText('Sign in to view your profile')).toBeVisible();

  // Login again
  await page.getByRole('link', { name: 'Login' }).first().click(); // Navbar might have Login link
  await page.getByRole('button', { name: 'Login' }).click(); // Switch to Login mode (default)
  
  await page.getByPlaceholder('you@example.com').fill(email);
  await page.getByPlaceholder('••••••••').fill(password);
  await page.getByRole('button', { name: 'Đăng nhập' }).click();

  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByText(`Welcome, ${name}`)).toBeVisible();
});
