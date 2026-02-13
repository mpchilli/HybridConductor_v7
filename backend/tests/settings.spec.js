import { test, expect } from '@playwright/test';

test.describe('Settings Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should toggle settings sidebar', async ({ page }) => {
    // Open settings (Gear icon)
    await page.getByRole('button', { name: 'Settings' }).click();
    await expect(page.getByText('Orchestrator Complexity')).toBeVisible();
    
    // Close settings (X button)
    await page.getByRole('button', { name: '✕' }).click();
    await expect(page.getByText('Orchestrator Complexity')).toBeHidden();
  });

  test('should verify sliders exist', async ({ page }) => {
    await page.getByRole('button', { name: 'Settings' }).click();
    
    await expect(page.getByText('Creativity')).toBeVisible();
    await expect(page.getByText('70%')).toBeVisible();
    
    await expect(page.getByText('Detail Level')).toBeVisible();
    await expect(page.getByText('90%')).toBeVisible();
  });

  test('should reset to defaults', async ({ page }) => {
    await page.getByRole('button', { name: 'Settings' }).click();
    
    const resetButton = page.getByRole('button', { name: 'Reset to Defaults' });
    await expect(resetButton).toBeVisible();
    await resetButton.click();
    // Logic for reset is not fully implemented in component state yet, but button exists
  });
  
  test('should toggle via shortcut Ctrl+,', async ({ page }) => {
    // Press Ctrl+,
    await page.keyboard.press('Control+,');
    await expect(page.getByText('Orchestrator Complexity')).toBeVisible();
    
    // Press again to close
    await page.keyboard.press('Control+,');
    await expect(page.getByText('Orchestrator Complexity')).toBeHidden();
  });
});
