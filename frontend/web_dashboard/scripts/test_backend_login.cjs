#!/usr/bin/env node
/**
 * Test admin login using backend auth (not dev backdoor)
 */
const { chromium } = require('playwright');

async function runTest() {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:5175';
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log(`\n🧪 Testing Backend Admin Login at ${BASE_URL}`);
    console.log('='.repeat(60));

    // Navigate to admin login page
    console.log('\n1️⃣  Navigating to /admin/login...');
    await page.goto(`${BASE_URL}/admin/login`, { waitUntil: 'domcontentloaded' });
    const initialUrl = page.url();
    console.log(`   ✓ URL: ${initialUrl}`);

    // Wait for form to be interactive
    await page.waitForSelector('button[type="submit"]', { timeout: 5000 });

    // Fill in credentials (lowercase bahati, password 1234)
    console.log('\n2️⃣  Filling in login form (bahati / 1234)...');
    await page.fill('input[placeholder="admin"]', 'bahati');
    await page.fill('input[placeholder="••••••"]', '1234');

    const username = await page.inputValue('input[placeholder="admin"]');
    const password = await page.inputValue('input[placeholder="••••••"]');
    console.log(`   ✓ Username: ${username}, Password: ${password ? '***' : 'empty'}`);

    // Monitor network requests
    let loginRequest = null;
    page.on('response', async (response) => {
      if (response.url().includes('/api/auth/login')) {
        loginRequest = {
          url: response.url(),
          status: response.status(),
          ok: response.ok()
        };
      }
    });

    // Submit form
    console.log('\n3️⃣  Submitting login form...');
    const submitButton = page.locator('button[type="submit"]');
    const isDisabled = await submitButton.isDisabled();
    console.log(`   - Button disabled: ${isDisabled}`);

    await submitButton.click();
    console.log('   ✓ Form submitted');

    // Wait for response or navigation
    console.log('\n4️⃣  Waiting for backend response...');
    await page.waitForTimeout(2000); // Give backend time to respond

    if (loginRequest) {
      console.log(`   ✓ Backend response: ${loginRequest.status}`);
    } else {
      console.log('   ℹ️  No login request detected');
    }

    // Check localStorage
    console.log('\n5️⃣  Checking localStorage...');
    const tokens = await page.evaluate(() => {
      return {
        accessToken: localStorage.getItem('jarvis_access_token'),
        user: localStorage.getItem('jarvis_user'),
        all: Object.keys(localStorage)
      };
    });

    if (tokens.accessToken) {
      console.log(`   ✓ Access Token stored: ${tokens.accessToken.substring(0, 30)}...`);
    } else {
      console.log('   ❌ No access token');
    }

    if (tokens.user) {
      const user = JSON.parse(tokens.user);
      console.log(`   ✓ User: ${user.username} (role: ${user.role})`);
    } else {
      console.log('   ❌ No user data');
    }

    // Check URL change
    const finalUrl = page.url();
    console.log(`\n6️⃣  Final URL: ${finalUrl}`);
    if (finalUrl.includes('/admin') && !finalUrl.includes('/admin/login')) {
      console.log('   ✅ Navigation successful (on /admin)');
    } else {
      console.log('   ❌ Still on /admin/login');
    }

    // Summary
    console.log('\n' + '='.repeat(60));
    if (tokens.accessToken && finalUrl.includes('/admin') && !finalUrl.includes('/admin/login')) {
      console.log('✅ BACKEND LOGIN WORKS!');
      return 0;
    } else {
      console.log('❌ Backend login has issues');
      console.log(`   - Tokens: ${tokens.accessToken ? 'yes' : 'no'}`);
      console.log(`   - URL changed: ${finalUrl.includes('/admin') && !finalUrl.includes('/admin/login')}`);
      return 1;
    }
  } catch (err) {
    console.error('\n❌ Test error:', err.message);
    return 1;
  } finally {
    await browser.close();
  }
}

runTest().then(code => process.exit(code));
