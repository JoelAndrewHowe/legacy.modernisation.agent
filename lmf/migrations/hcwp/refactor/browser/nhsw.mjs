import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { measureContrast } from './contrast.mjs';

const out = new URL('../evidence/nhsw-browser/', import.meta.url);
const report = { startedAt: new Date().toISOString(), scope: 'NHSW styling of current preview only, not full Refactor gate', checks: [], failed: 0, skipped: 0 };
let browser;
try {
  await mkdir(out, { recursive: true });
  browser = await chromium.launch({ headless: true });
  report.browser = browser.version();
  const page = await browser.newPage();
  const external = [];
  page.on('request', request => { if (!request.url().startsWith('http://127.0.0.1:5187/')) external.push(request.url()); });
  let received = 0;
  page.on('websocket', socket => {
    if (socket.url().includes('_blazor')) socket.on('framereceived', () => received++);
  });
  await page.goto('http://127.0.0.1:5187/');
  for (let i = 0; i < 100 && received < 2; i++) await new Promise(resolve => setTimeout(resolve, 100));
  assert.ok(received >= 2, 'Live circuit must be ready before testing keyboard focus');
  const css = await page.request.get('http://127.0.0.1:5187/vendor/nhsw/nhsw.min.css');
  assert.equal(css.status(), 200);
  assert.match(await css.text(), /\.nhsw-button/);
  assert.deepEqual(external, []);
  report.checks.push('Local official stylesheet served; no external runtime requests');
  for (const label of ['Contact date', 'Heart assessment']) {
    assert.equal(await page.getByLabel(label, { exact: true }).count(), 1);
  }
  report.checks.push('Visible labels remain associated with native controls');
  const save = page.getByRole('button', { name: 'Save KD03 result', exact: true });
  assert.equal(await save.evaluate(el => getComputedStyle(el).backgroundColor), 'rgb(27, 54, 93)');
  report.checks.push('Primary button renders official NHSW blue');
  const textAndControls = 'main h1, main h2, main p, main label, main .nhsw-hint, main input, main select, main button, main dt, main dd';
  await measureContrast(page, report, 'initial', textAndControls);
  for (const selector of ['.nhsw-button--primary', '.nhsw-button--secondary']) {
    await page.locator(selector).hover();
    await measureContrast(page, report, 'hover', selector);
  }
  await page.mouse.move(0, 0);
  await save.focus();
  await page.keyboard.press('Shift+Tab');
  assert.equal(await page.locator('#heart').evaluate(el => document.activeElement === el), true);
  const focus = await page.locator('#heart').evaluate(el => {
    const s = getComputedStyle(el); return { outline: s.outlineStyle, width: s.outlineWidth, shadow: s.boxShadow };
  });
  assert.ok((focus.outline !== 'none' && focus.width !== '0px') || focus.shadow !== 'none');
  report.focus = focus;
  report.checks.push('Keyboard Shift+Tab reaches select with visible focus styling');
  for (const selector of ['#heart', '#contact-date', '.nhsw-button--primary', '.nhsw-button--secondary']) {
    await page.locator(selector).focus();
    await measureContrast(page, report, 'focus', selector, true);
  }
  // Exercise the currently rendered summary values and generic fault, not a new full flow.
  await page.getByLabel('Contact date', { exact: true }).fill('2025-02-20');
  await page.getByLabel('Heart assessment', { exact: true }).selectOption('1');
  await save.click();
  await page.locator('main dl').waitFor();
  await page.locator('#heart').focus();
  await measureContrast(page, report, 'saved result', 'main dt, main dd');
  await page.getByLabel('Contact date', { exact: true }).fill('2024-12-31');
  await save.click();
  await page.getByRole('alert').waitFor();
  await page.locator('#heart').focus();
  await measureContrast(page, report, 'generic save error', '.nhsw-error-summary, .nhsw-error-summary h2, .nhsw-error-summary p');
  await page.getByRole('alert').focus();
  await measureContrast(page, report, 'programmatically focused generic error', '.nhsw-error-summary', true);
  report.checks.push('Executed AA contrast measurements for current text, hints, controls, buttons, hover/focus, saved values and generic error');
  await page.locator('h1').click(); // Remove focus/hover before normal responsive measurements.
  await page.mouse.move(0, 0);
  for (const width of [320, 768, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    await measureContrast(page, report, `rendered at ${width}px`, textAndControls);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await page.screenshot({ path: new URL(`${width}.png`, out).pathname, fullPage: true });
  }
  report.checks.push('Preview has no horizontal overflow at 320, 768 and 1280 pixels');
} catch (error) {
  report.failed++;
  report.error = String(error);
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  await mkdir(out, { recursive: true });
  report.finishedAt = new Date().toISOString();
  report.sourceHashes = {};
  for (const path of ['browser/nhsw.mjs', 'browser/contrast.mjs', 'src/Components/Pages/Recording.razor', 'src/wwwroot/vendor/nhsw/nhsw.min.css']) {
    report.sourceHashes[path] = createHash('sha256').update(await readFile(new URL(`../${path}`, import.meta.url))).digest('hex');
  }
  await writeFile(new URL('results.json', out), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report));
}
