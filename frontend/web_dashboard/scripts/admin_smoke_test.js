const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  try {
    const base = process.env.BASE_URL || 'http://localhost:5174';
    const loginUrl = `${base}/admin/login`;
    console.log('Navigating to', loginUrl);
    await page.goto(loginUrl, { waitUntil: 'networkidle' });

    // Fill form
    await page.fill('input[placeholder="admin"], input[name="username"], input[type="text"]', 'Bahati').catch(() => { });
    await page.fill('input[type="password"]', '1234');

    // Click submit
    await page.click('button[type="submit"]');

    // Wait for navigation or admin content
    await page.waitForNavigation({ waitUntil: 'networkidle', timeout: 5000 }).catch(() => { });

    // Give SPA a moment to update state
    await page.waitForTimeout(500);

    const url = page.url();
    const access = await page.evaluate(() => localStorage.getItem('jarvis_access_token'));
    const refresh = await page.evaluate(() => localStorage.getItem('jarvis_refresh_token'));
    const user = await page.evaluate(() => localStorage.getItem('jarvis_user'));

    console.log(JSON.stringify({ url, access: !!access, accessValue: access || null, refresh: !!refresh, user: user ? JSON.parse(user) : null }, null, 2));

    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error('Smoke test failed:', err);
    await browser.close();
    process.exit(2);
  }
})();
