import { test, expect } from '@playwright/test';

test('should allow exploring urns', async ({ page }) => {
  await page.goto('/explore');
  
  // Check if urns are loaded
  await expect(page.getByText('Explore the Nine Urns')).toBeVisible();
  
  // Wait for at least one urn card to appear (skipping skeletons)
  // The skeleton doesn't have "Open viewer →" text, so waiting for that text is safe.
  await expect(page.getByText('Open viewer →').first()).toBeVisible();

  // Click on the first urn
  await page.getByText('Open viewer →').first().click();

  // Should navigate to urn viewer
  await expect(page).toHaveURL(/\/urns\//);
  
  // Check if canvas exists (3D viewer loaded)
  await expect(page.locator('canvas')).toBeVisible({ timeout: 15000 });
});
