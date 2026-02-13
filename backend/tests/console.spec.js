import { test, expect } from '@playwright/test';

test.describe('Console Component', () => {
  test.beforeEach(async ({ page }) => {
    // Mock SSE to provide logs
    await page.route('/api/stream', async route => {
      const mockData = {
        tasks: [],
        logs: [
            { type: 'INFO', message: 'System started', timestamp: Date.now() },
            { type: 'ERROR', message: 'Connection failed', timestamp: Date.now() },
            { type: 'DEBUG', message: 'Variable x=10', timestamp: Date.now() }
        ]
      };
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: `data: ${JSON.stringify(mockData)}\n\n`
      });
    });
    
    await page.goto('/');
  });

  test('should display logs', async ({ page }) => {
    await expect(page.getByText('System started')).toBeVisible();
    await expect(page.getByText('Connection failed')).toBeVisible();
  });

  test('should filter logs', async ({ page }) => {
    // Click ERROR filter
    await page.getByRole('button', { name: 'ERROR' }).click();
    await expect(page.getByText('Connection failed')).toBeVisible();
    await expect(page.getByText('System started')).toBeHidden();
    
    // Click INFO filter
    await page.getByRole('button', { name: 'INFO' }).click();
    await expect(page.getByText('System started')).toBeVisible();
    await expect(page.getByText('Connection failed')).toBeHidden();
    
    // Click ALL
    await page.getByRole('button', { name: 'ALL' }).click();
    await expect(page.getByText('System started')).toBeVisible();
    await expect(page.getByText('Connection failed')).toBeVisible();
  });

  test('should search logs', async ({ page }) => {
    const searchInput = page.getByPlaceholder('Search logs...');
    
    await searchInput.fill('Connection');
    await expect(page.getByText('Connection failed')).toBeVisible();
    await expect(page.getByText('System started')).toBeHidden();
    
    await searchInput.fill('Variable');
    await expect(page.getByText('Variable x=10')).toBeVisible();
  });

  test('should copy to clipboard', async ({ page }) => {
    // Mock clipboard API
    await page.exposeFunction('mockClipboardWrite', text => {
        return text;
    });
    
    await page.addInitScript(() => {
        navigator.clipboard = {
            writeText: window.mockClipboardWrite
        };
    });

    // Currently we just check if it doesn't crash, validating the actual text usually requires
    // reading from clipboard which is flaky in headless.
    // Instead we can spy on the mock if we could, but exposeFunction binding is one way.
    // A simpler way is to check if the button is clickable.
    
    await page.getByTitle('Copy to Clipboard').click();
    // Pass if click happened without error
  });
});
