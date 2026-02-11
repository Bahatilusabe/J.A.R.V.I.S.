#!/usr/bin/env node
/**
 * Detailed admin login flow test with comprehensive debugging
 */
const { chromium } = require('playwright');

async function runTest() {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:5175';
  const BACKEND_URL = 'http://127.0.0.1:8000';

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Listen to all console messages from the page
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error') console.log(`  🔴 [JS ERROR] ${text}`);
    else if (type === 'warn') console.log(`  🟡 [JS WARN] ${text}`);
    else if (type === 'info' || text.includes('Admin') || text.includes('backdoor')) console.log(`  ℹ️  [JS] ${text}`);
  });

  // Listen to network requests
  page.on('response', response => {
    if (response.url().includes('/api/auth')) {
      console.log(`  📡 [NETWORK] ${response.request().method()} ${response.url()} → ${response.status()}`);
    }
  });

  try {
    console.log(`\n🧪 COMPREHENSIVE ADMIN LOGIN TEST`);
    console.log('='.repeat(70));
    console.log(`Frontend: ${BASE_URL}`);
    console.log(`Backend: ${BACKEND_URL}`);

    // Step 1: Navigate to admin login
    console.log('\n📍 STEP 1: Navigate to /admin/login');
    await page.goto(`${BASE_URL}/admin/login`, { waitUntil: 'domcontentloaded' });
    console.log(`  ✓ Page loaded: ${page.url()}`);

    // Wait for form to be interactive
    await page.waitForSelector('input[placeholder="admin"]', { timeout: 5000 }).catch(e => {
      console.log(`  ❌ Form not found: ${e.message}`);
    });

    // Step 2: Check if env var is accessible
    console.log('\n📍 STEP 2: Check Vite environment');
    const envCheck = await page.evaluate(() => {
      try {
        const devFlag = (window.__VITE_DEV_ADMIN_BACKDOOR || 'undefined');
        return { devFlag, hasLocalStorage: !!window.localStorage };
      } catch (e) {
        return { error: e.message };
      }
    });
    console.log(`  Env check: ${JSON.stringify(envCheck)}`);

    // Step 3: Fill form
    console.log('\n📍 STEP 3: Fill login form with bahati / 1234');
    await page.fill('input[placeholder="admin"]', 'bahati');
    await page.fill('input[placeholder="••••••"]', '1234');

    const formValues = await page.evaluate(() => ({
      username: document.querySelector('input[placeholder="admin"]')?.value,
      password: document.querySelector('input[placeholder="••••••"]')?.value,
      buttonDisabled: document.querySelector('button[type="submit"]')?.disabled
    }));
    console.log(`  Form: ${JSON.stringify(formValues)}`);

    // Step 4: Submit form
    console.log('\n📍 STEP 4: Submit login form');
    const button = page.locator('button[type="submit"]');
    await button.click();
    console.log('  ✓ Form submitted');

    // Wait for network activity
    await page.waitForTimeout(3000);

    // Step 5: Check localStorage
    console.log('\n📍 STEP 5: Check localStorage after submission');
    const storage = await page.evaluate(() => ({
      accessToken: localStorage.getItem('jarvis_access_token'),
      user: localStorage.getItem('jarvis_user'),
      all: Object.keys(localStorage)
    }));
    console.log(`  Access Token: ${storage.accessToken ? '✓ SET' : '❌ NOT SET'}`);
    console.log(`  User Data: ${storage.user ? '✓ SET' : '❌ NOT SET'}`);
    console.log(`  All keys: [${storage.all.join(', ')}]`);

    // Step 6: Check URL
    console.log('\n📍 STEP 6: Check current URL');
    const finalUrl = page.url();
    console.log(`  Current URL: ${finalUrl}`);
    if (finalUrl.includes('/admin') && !finalUrl.includes('/admin/login')) {
      console.log(`  ✅ SUCCESS: Navigated to /admin`);
    } else {
      console.log(`  ❌ FAILED: Still on /admin/login or wrong URL`);
    }

    // Step 7: Check page title/heading
    console.log('\n📍 STEP 7: Check page content');
    const heading = await page.locator('h1, h2, h3').first().textContent().catch(() => 'N/A');
    const title = await page.title();
    console.log(`  Page title: ${title}`);
    console.log(`  First heading: ${heading}`);

    // Summary
    console.log('\n' + '='.repeat(70));
    const success = storage.accessToken && finalUrl.includes('/admin') && !finalUrl.includes('/admin/login');
    if (success) {
      console.log('✅ TEST PASSED: Admin login flow working!');
      return 0;
    } else {
      console.log('❌ TEST FAILED: Admin login has issues');
      console.log(`   - Tokens stored: ${storage.accessToken ? 'yes' : 'no'}`);
      console.log(`   - URL changed: ${finalUrl.includes('/admin') && !finalUrl.includes('/admin/login') ? 'yes' : 'no'}`);
      return 1;
    }

  } catch (err) {
    console.error('\n❌ Test error:', err.message);
    console.error(err.stack);
    return 1;
  } finally {
    await browser.close();
  }
}

runTest().then(code => process.exit(code));
