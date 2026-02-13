const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    console.log('Navigating to dashboard...');
    await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#root'); // Ensure React mounted
    
    // Set viewports for desktop and mobile
    const viewports = [
      { width: 1920, height: 1080, name: 'desktop' },
      { width: 375, height: 667, name: 'mobile' }
    ];

    for (const v of viewports) {
      await page.setViewportSize({ width: v.width, height: v.height });
      console.log(`Taking ${v.name} screenshot...`);
      // Simulating some interaction to open settings
      if (v.name === 'mobile') {
         await page.getByRole('button', { name: 'Settings' }).click();
      }
      
      const screenshotPath = path.resolve(__dirname, `../../../../.gemini/antigravity/brain/07c471a5-0339-4734-ad08-13a4effdf9b9/dashboard_${v.name}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: true });
      console.log(`Saved to ${screenshotPath}`);
    }
  } catch (error) {
    console.error('Error capturing screenshot:', error);
  } finally {
    await browser.close();
  }
})();
