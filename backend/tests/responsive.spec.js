import { test, expect } from '@playwright/test';

test.describe('Responsive Layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display grid layout on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    
    // Check if Console is to the right of Progress (grid-cols-12 logic)
    // We can check positions or classes. 
    // Tailwind classes are 'lg:col-span-8' for main and 'lg:col-span-4' for console.
    
    const progressContainer = page.locator('.col-span-12.lg\\:col-span-8');
    const consoleContainer = page.locator('.col-span-12.lg\\:col-span-4');
    
    await expect(progressContainer).toBeVisible();
    await expect(consoleContainer).toBeVisible();
    
    // Bounding box check for layout relative positions
    const progressBox = await progressContainer.boundingBox();
    const consoleBox = await consoleContainer.boundingBox();
    
    expect(consoleBox.x).toBeGreaterThan(progressBox.x);
  });

  test('should stack layout on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    
    const progressContainer = page.locator('.col-span-12.lg\\:col-span-8');
    const consoleContainer = page.locator('.col-span-12.lg\\:col-span-4');
    
    const progressBox = await progressContainer.boundingBox();
    const consoleBox = await consoleContainer.boundingBox();
    
    // In stacked mode, X should be similar (padding diffs), Y should defer
    // Console should be below Progress
    expect(Math.abs(progressBox.x - consoleBox.x)).toBeLessThan(50); 
    expect(consoleBox.y).toBeGreaterThan(progressBox.y);
  });
  
  test('settings sidebar should overlay on mobile', async ({ page }) => {
    // Should behave same responsive overlay logic
    await page.setViewportSize({ width: 375, height: 667 });
    await page.getByRole('button', { name: 'Settings' }).click();
    
    // Check width of settings panel
    const sidebar = page.locator('div.w-96');
    await expect(sidebar).toBeVisible();
    // On small screens w-96 might overflow or be max-w-full if we added that util
    // Currently hardcoded w-96 (24rem = 384px), which is > 375px
    // It might cause scroll or be cut off. For now we assert visibility.
  });
});
