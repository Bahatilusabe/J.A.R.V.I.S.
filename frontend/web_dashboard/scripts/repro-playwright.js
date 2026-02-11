import playwright from 'playwright';

(async () => {
  const browser = await playwright.chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('console', (msg) => {
    console.log(`[console:${msg.type()}] ${msg.text()}`);
  });

  page.on('pageerror', (err) => {
    console.error('[pageerror]', err);
  });

  page.on('requestfailed', (req) => {
    console.error('[requestfailed]', req.url(), req.failure()?.errorText);
  });

  page.on('response', async (res) => {
    if (res.status() >= 400) {
      console.error('[badresponse]', res.status(), res.url());
      try {
        const text = await res.text();
        console.error('[badresponse-body]', text.slice(0, 500));
      } catch (e) {
        /* ignore */
      }
    }
  });

  try {
    console.log('Navigating to app...');
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle', timeout: 10000 });

    // Wait briefly and capture snapshot of body
    await page.waitForTimeout(1000);
    const body = await page.evaluate(() => document.body.innerHTML);
    console.log('BODY LEN:', body.length);
    console.log('BODY PREVIEW:', body.slice(0, 1000));

    // Try to login if login form present
    const hasLogin = await page.$('form[action*="login"],form#login, input[name="username"], input[name="email"]');
    console.log('Has login form:', !!hasLogin);
  } catch (err) {
    console.error('Test script error:', err);
  } finally {
    await browser.close();
  }
})();
