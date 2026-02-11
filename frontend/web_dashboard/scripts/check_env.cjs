#!/usr/bin/env node
/**
 * Check if Vite env is available in browser
 */
const { chromium } = require('playwright');

async function runTest() {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:5175';
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log(`\n🧪 Checking Vite env variables at ${BASE_URL}\n`);

    await page.goto(`${BASE_URL}/admin/login`, { waitUntil: 'networkidle' });

    // Check import.meta.env in the page context
    const envVars = await page.evaluate(() => {
      return {
        VITE_DEV_ADMIN_BACKDOOR: window.__VITE_DEV_ADMIN_BACKDOOR || 'undefined',
        hasLocalStorage: !!window.localStorage,
        keys: Object.keys(window.localStorage || {})
      };
    });

    console.log('Vite environment variables:');
    console.log('  VITE_DEV_ADMIN_BACKDOOR:', envVars.VITE_DEV_ADMIN_BACKDOOR);
    console.log('  localStorage available:', envVars.hasLocalStorage);
    console.log('  localStorage keys:', envVars.keys);

    // Try to access the component state
    const hasButton = await page.locator('button[type="submit"]').count();
    console.log('\nForm elements:');
    console.log('  Submit button found:', hasButton > 0);

  } catch (err) {
    console.error('\n❌ Error:', err.message);
  } finally {
    await browser.close();
  }
}

runTest().then(() => process.exit(0));
