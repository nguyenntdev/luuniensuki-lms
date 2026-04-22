import { test, expect } from '@playwright/test';

test('should allow exploring urns', async ({ page }) => {
  await page.goto('/explore');

  // Check if the explore hero is rendered
  await expect(page.getByTestId('explore-title')).toBeVisible();

  // Wait for at least one urn card to appear
  await expect(page.getByTestId('urn-card').first()).toBeVisible();

  // Click on the first urn
  await page.getByTestId('urn-card').first().click();

  // Should navigate to urn viewer
  await expect(page).toHaveURL(/\/urns\//);

  // Check if canvas exists (3D viewer loaded)
  await expect(page.locator('canvas')).toBeVisible({ timeout: 15000 });
});
