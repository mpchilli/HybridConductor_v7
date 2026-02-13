import { test, expect } from '@playwright/test';

test.describe('ProgressTree Component', () => {
  test.beforeEach(async ({ page }) => {
    // Mock SSE endpoint
    await page.route('/api/stream', async route => {
      const mockData = {
        tasks: [
          { 
            id: 1, 
            name: 'Root Task', 
            status: 'running',
            details: 'Processing...',
            children: [
              { id: 2, name: 'Child Task A', status: 'completed' },
              { id: 3, name: 'Child Task B', status: 'pending' }
            ]
          }
        ],
        logs: []
      };
      
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: `data: ${JSON.stringify(mockData)}\n\n`
      });
    });

    await page.goto('/');
  });

  test('should render task tree from SSE data', async ({ page }) => {
    await expect(page.getByText('Root Task')).toBeVisible();
    await expect(page.getByText('Child Task A')).toBeVisible();
    await expect(page.getByText('Child Task B')).toBeVisible();
  });

  test('should show correct status icons/styles', async ({ page }) => {
    // Check for running state (pulse animation or specific class)
    const rootNode = page.getByText('Root Task').locator('..'); 
    // This selector is a bit loose, in real app we'd use test-ids
    // But we know 'running' adds specific classes
    // We can check if the icon is present
    await expect(page.getByText('●')).toBeVisible(); // Running icon
    await expect(page.getByText('✓')).toBeVisible(); // Completed icon
  });

  test('should toggle collapse/expand', async ({ page }) => {
    // By default it starts expanded (set in component: useState(true))
    await expect(page.getByText('Child Task A')).toBeVisible();
    
    // Click the root task to collapse
    await page.getByText('Root Task').click();
    
    // Should NOT be visible now (or detached)
    await expect(page.getByText('Child Task A')).toBeHidden();
    
    // Click again to expand
    await page.getByText('Root Task').click();
    await expect(page.getByText('Child Task A')).toBeVisible();
  });
});
