#!/usr/bin/env node
/**
 * Debug admin login form submission
 */
const { chromium } = require('playwright');

async function runTest() {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:5175';
  const browser = await chromium.launch({ headless: false }); // Show the browser
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log(`\n🧪 Debugging Admin Login Form at ${BASE_URL}`);

    // Navigate to admin login page
    console.log('\n1️⃣  Navigating to /admin/login...');
    await page.goto(`${BASE_URL}/admin/login`, { waitUntil: 'networkidle' });

    // Wait a bit for form to render
    await page.waitForTimeout(1000);

    // Fill in credentials
    console.log('\n2️⃣  Filling in login form...');
    await page.fill('input[placeholder="admin"]', 'bahati');
    console.log('   ✓ Username filled');
    await page.fill('input[placeholder="••••••"]', '1234');
    console.log('   ✓ Password filled');

    // Check button state
    const button = page.locator('button[type="submit"]');
    const isDisabled = await button.isDisabled();
    const buttonText = await button.textContent();
    console.log(`\n3️⃣  Button state:`);
    console.log(`   - Text: ${buttonText}`);
    console.log(`   - Disabled: ${isDisabled}`);

    // Check form values
    const username = await page.inputValue('input[placeholder="admin"]');
    const password = await page.inputValue('input[placeholder="••••••"]');
    console.log(`\n4️⃣  Form values:`);
    console.log(`   - Username: ${username}`);
    console.log(`   - Password: ${'*'.repeat(password?.length || 0)}`);

    // Try clicking the button
    console.log('\n5️⃣  Clicking button...');
    await button.click();
    console.log('   ✓ Button clicked');

    // Wait a bit and check localStorage
    await page.waitForTimeout(2000);
    const tokens = await page.evaluate(() => {
      return {
        accessToken: localStorage.getItem('jarvis_access_token'),
        user: localStorage.getItem('jarvis_user'),
        all: Object.keys(localStorage)
      };
    });
    console.log(`\n6️⃣  localStorage after click:`);
    console.log(`   - All keys: ${tokens.all.join(', ') || 'none'}`);
    console.log(`   - Access Token: ${tokens.accessToken ? 'yes' : 'no'}`);

    // Check current URL
    const url = page.url();
    console.log(`\n7️⃣  Current URL: ${url}`);

    console.log('\n⏸  Browser will stay open for 10 seconds - inspect it!');
    await page.waitForTimeout(10000);

  } catch (err) {
    console.error('\n❌ Error:', err.message);
  } finally {
    await browser.close();
  }
}

runTest().then(() => process.exit(0));
