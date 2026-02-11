#!/usr/bin/env node
/**
 * End-to-end test of admin login flow
 * Tests both dev backdoor and backend real credentials
 */
const { chromium } = require('playwright');

async function runTest() {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:5175';
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log(`\n🧪 Testing Admin Login Flow at ${BASE_URL}`);
    console.log('='.repeat(60));

    // Navigate to admin login page
    console.log('\n1️⃣  Navigating to /admin/login...');
    await page.goto(`${BASE_URL}/admin/login`, { waitUntil: 'networkidle' });
    const initialUrl = page.url();
    console.log(`   ✓ URL: ${initialUrl}`);

    // Fill in credentials (lowercase bahati, password 1234)
    console.log('\n2️⃣  Filling in login form (bahati / 1234)...');
    await page.fill('input[placeholder="admin"]', 'bahati');
    await page.fill('input[placeholder="••••••"]', '1234');
    console.log('   ✓ Form filled');

    // Submit form
    console.log('\n3️⃣  Submitting login form...');
    const submitButton = page.locator('button[type="submit"]');

    // Listen for errors before submitting
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await submitButton.click();

    // Wait for navigation (should go to /admin without full-page reload)
    console.log('\n4️⃣  Waiting for navigation...');
    await page.waitForNavigation({ waitUntil: 'networkidle', timeout: 5000 }).catch(() => {
      if (errors.length > 0) {
        console.log('   ℹ️  Browser errors:', errors);
      }
    });
    const finalUrl = page.url();
    console.log(`   ✓ Final URL: ${finalUrl}`);

    // Check if we're on /admin
    if (finalUrl.includes('/admin') && !finalUrl.includes('/admin/login')) {
      console.log('   ✅ Navigation successful (not on /admin/login)');
    } else {
      console.log(`   ⚠️  URL did not change to /admin (still on ${finalUrl})`);
    }

    // Check localStorage for tokens
    console.log('\n5️⃣  Checking localStorage for authentication tokens...');
    const tokens = await page.evaluate(() => {
      const accessToken = localStorage.getItem('jarvis_access_token');
      const refreshToken = localStorage.getItem('jarvis_refresh_token');
      const user = localStorage.getItem('jarvis_user');
      return { accessToken, refreshToken, user };
    });

    if (tokens.accessToken) {
      console.log(`   ✓ Access Token: ${tokens.accessToken.substring(0, 20)}...`);
    } else {
      console.log('   ⚠️  No access token in localStorage');
    }

    if (tokens.refreshToken) {
      console.log(`   ✓ Refresh Token: ${tokens.refreshToken.substring(0, 20)}...`);
    } else {
      console.log('   ⚠️  No refresh token in localStorage');
    }

    if (tokens.user) {
      console.log(`   ✓ User: ${tokens.user}`);
    } else {
      console.log('   ⚠️  No user data in localStorage');
    }

    // Check for admin page content (look for "Admin Console" heading)
    const pageTitle = await page.title();
    const heading = await page.locator('h1, h2, h3').first().textContent().catch(() => null);
    console.log('\n6️⃣  Checking admin page content...');
    console.log(`   Page title: ${pageTitle}`);
    console.log(`   First heading: ${heading}`);

    // Summary
    console.log('\n' + '='.repeat(60));
    if (finalUrl.includes('/admin') && !finalUrl.includes('/admin/login') && tokens.accessToken) {
      console.log('✅ TEST PASSED: Admin login flow working correctly!');
      return 0;
    } else {
      console.log('❌ TEST FAILED: Admin login flow has issues');
      console.log(`   - URL changed: ${finalUrl.includes('/admin') && !finalUrl.includes('/admin/login')}`);
      console.log(`   - Token stored: ${!!tokens.accessToken}`);
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
