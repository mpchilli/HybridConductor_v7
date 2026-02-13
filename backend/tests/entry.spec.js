import { test, expect } from '@playwright/test';

test.describe('EntryField Component', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should allow typing and show char count', async ({ page }) => {
    const textarea = page.locator('textarea');
    await expect(textarea).toBeVisible();
    
    await textarea.fill('Hello Ralph');
    await expect(page.getByText('11 chars')).toBeVisible();
  });

  test('should clear input on Ctrl+Enter', async ({ page }) => {
    const textarea = page.locator('textarea');
    await textarea.fill('Execute this');
    await textarea.press('Control+Enter');
    await expect(textarea).toBeEmpty();
  });

  test('should clear input on Run button click', async ({ page }) => {
    const textarea = page.locator('textarea');
    await textarea.fill('Run this');
    await page.getByRole('button', { name: 'Run' }).click();
    await expect(textarea).toBeEmpty();
  });
  
  test('should resize handle exist (visual check logic)', async ({ page }) => {
     // Just checking if resize handle is present in DOM
     const handle = page.locator('div[title="Drag to resize"]');
     await expect(handle).toBeVisible();
  });
});
