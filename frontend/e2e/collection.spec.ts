import { test, expect } from '@playwright/test';

test('should display collection and filter items', async ({ page }) => {
  // Login first
  const email = `test-col-${Date.now()}@example.com`;
  const password = 'password123';
  const name = 'Collection User';

  await page.goto('/login');
  await page.getByRole('button', { name: 'Register' }).click();
  await page.getByPlaceholder('Sử Quan Tập Sự').fill(name);
  await page.getByPlaceholder('you@example.com').fill(email);
  await page.getByPlaceholder('••••••••').fill(password);
  await page.getByRole('button', { name: 'Tạo tài khoản' }).click();
  await expect(page).toHaveURL(/\/dashboard/);

  // Go to collection
  await page.goto('/collection');
  
  await expect(page.getByText('Your Collection')).toBeVisible();
  
  // Wait for loading to finish (stats visible)
  await expect(page.getByText('Total Motifs')).toBeVisible();

  // Test Status Filter: Discovered (should be empty for new user)
  await page.getByLabel('Status').selectOption('discovered'); // value is lowercase
  await expect(page.getByText('No motifs found matching your filters')).toBeVisible();
  
  // Clear filters
  await page.getByRole('button', { name: 'Clear all filters' }).click();
  await expect(page.getByText('No motifs found matching your filters')).not.toBeVisible();
  
  // Test Search Filter (random string)
  await page.getByLabel('Search').fill('NonExistentMotifXYZ');
  await expect(page.getByText('No motifs found matching your filters')).toBeVisible();
});
