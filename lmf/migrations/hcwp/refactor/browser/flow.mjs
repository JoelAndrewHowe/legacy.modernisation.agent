import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { measureContrast } from './contrast.mjs';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
const root = fileURLToPath(new URL('../', import.meta.url));
const evidence = `${root}evidence/full-flow-browser`;
const url = 'http://127.0.0.1:5189';
const report = { startedAt: new Date().toISOString(), scope: 'Full-flow implementation smoke, not complete Refactor gate', checks: [], failed: 0, skipped: 0, browserExecuted: false };
let server, browser, log = '';
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function check(name, action) { await action(); report.checks.push({ name, status: 'passed' }); }
try {
  await mkdir(evidence, { recursive: true });
  try { await fetch(url); throw Error('Port occupied'); } catch (e) { if (e.message !== 'fetch failed') throw e; }
  server = spawn('dotnet', ['run', '--no-build', '--project', `${root}src`, '--urls', url], { stdio: ['ignore', 'pipe', 'pipe'] });
  server.stdout.on('data', x => log += x); server.stderr.on('data', x => log += x);
  let ready = false;
  for (let i = 0; i < 150; i++) { try { ready = (await fetch(url)).ok; if (ready) break; } catch {} await sleep(100); }
  assert.ok(ready, 'Server startup failed');
  browser = await chromium.launch(); report.browserExecuted = true; report.browser = browser.version();
  const context = await browser.newContext();
  const page = await context.newPage(); const errors = []; let frames = 0;
  page.on('pageerror', e => errors.push(String(e)));
  page.on('websocket', ws => { if (ws.url().includes('_blazor')) ws.on('framereceived', () => frames++); });
  await page.goto(url);
  for (let i = 0; i < 100 && frames < 2; i++) await sleep(100);
  assert.ok(frames >= 2, 'Live interactive circuit required');
  // Initial protocol frames precede completion of DOM event attachment.
  await sleep(800);
  const save = () => page.getByRole('button', { name: 'Save KD03 result', exact: true }).click();
  const rows = () => page.locator('main dl').count();
  const inspectState = async (state, selector) => {
    report.presentation ??= [];
    for (const width of [320, 768, 1280]) {
      await page.setViewportSize({ width, height: 900 });
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${state} overflow at ${width}`);
      await measureContrast(page, report, `${state} ${width}px`, selector);
      await page.screenshot({ path: `${evidence}/${state}-${width}.png`, fullPage: true });
      await writeFile(`${evidence}/${state}-${width}.html`, await page.content());
      report.presentation.push({ state, width, overflow: false, screenshot: `${state}-${width}.png`, html: `${state}-${width}.html` });
    }
  };
  const assertFieldError = async id => {
    const control = page.locator(`#${id}`);
    assert.equal(await control.getAttribute('aria-invalid'), 'true');
    assert.equal(await control.getAttribute('aria-describedby'), `${id}-error`);
    assert.ok(await control.evaluate(el => el.classList.contains('nhsw-is-invalid') && el.parentElement.classList.contains('nhsw-form-group--error')));
    assert.ok(await page.locator(`#${id}-error`).innerText());
  };
  await check('no-results rejection with focused summary and field link', async () => {
    await save(); await page.getByRole('heading', { name: 'Result not saved' }).waitFor();
    assert.match(await page.locator('.nhsw-error-summary').innerText(), /NoResultsEnteredMessage/);
    assert.equal(await rows(), 0);
    assert.equal(await page.evaluate(() => document.activeElement.className), 'nhsw-error-summary');
    await assertFieldError('heart');
    await measureContrast(page, report, 'focused no-results summary', '.nhsw-error-summary', true);
    await page.keyboard.press('Tab');
    assert.ok(await page.locator('.nhsw-error-summary a').evaluate(el => el === document.activeElement));
    await page.keyboard.press('Enter');
    await page.locator('#heart:focus').waitFor();
    await measureContrast(page, report, 'focused invalid select', '#heart', true);
    await page.locator('h1').click();
    await inspectState('select-error', '.nhsw-error-summary h2, .nhsw-error-summary a, .nhsw-error-message, #heart');
  });
  await check('input error structure, summary keyboard link, responsive presentation and contrast', async () => {
    await page.locator('#Height').fill('-1'); await save();
    await page.locator('#Height-error').waitFor();
    await assertFieldError('Height');
    assert.equal(await rows(), 0);
    await page.keyboard.press('Tab'); await page.keyboard.press('Enter');
    await page.locator('#Height:focus').waitFor();
    await measureContrast(page, report, 'focused invalid input', '#Height', true);
    await page.locator('h1').click();
    await inspectState('input-error', '.nhsw-error-summary h2, .nhsw-error-summary a, .nhsw-error-message, #Height');
  });
  await check('all physical fields and measurements save through live circuit', async () => {
    for (const id of ['heart', 'Hips', 'Eyes', 'Testes', 'PhysicalGeneral']) await page.locator(`#${id}`).selectOption('1');
    await page.locator('#Height').fill('60'); await page.locator('#Weight').fill('6'); await page.locator('#HeadCircumference').fill('40');
    await page.locator('#Consent').selectOption('N');
    await save(); await page.getByText('Result saved and read back from persistence.', { exact: true }).waitFor();
    assert.equal(await rows(), 1);
    const values = await page.locator('main dl').evaluate(el => Object.fromEntries([...el.querySelectorAll('dt')].map(dt => [dt.textContent, dt.nextElementSibling.textContent])));
    assert.equal(values['Patient ID'], '101'); assert.equal(values.Date, '2025-02-19');
    for (const key of ['Heart', 'Hips', 'Eyes', 'Testes', 'PhysicalGeneral']) assert.equal(values[key], '1');
    assert.equal(values.Height, '60'); assert.equal(values.Weight, '6'); assert.equal(values.HeadCircumference, '40');
    await page.screenshot({ path: `${evidence}/saved.png`, fullPage: true });
  });
  await check('repeat confirmation declines then accepts with age warning', async () => {
    await page.getByRole('button', { name: 'Start new result' }).click();
    await page.locator('#contact-date').fill('2025-03-14'); await page.locator('#heart').selectOption('2');
    await save();
    const yes = page.getByRole('button', { name: 'Yes, continue' });
    const no = page.getByRole('button', { name: 'No, do not save' });
    await yes.waitFor();
    await inspectState('confirmation', 'section[aria-labelledby="confirmation-title"] h2, section[aria-labelledby="confirmation-title"] p, section[aria-labelledby="confirmation-title"] button');
    await yes.focus(); await page.keyboard.press('Tab');
    assert.ok(await no.evaluate(el => el === document.activeElement));
    await measureContrast(page, report, 'keyboard confirmation no', 'section[aria-labelledby="confirmation-title"] .nhsw-button--secondary', true);
    await page.keyboard.press('Space'); await no.waitFor({ state: 'detached' }); assert.equal(await rows(), 1);
    await save(); await no.waitFor(); await no.focus(); await page.keyboard.press('Shift+Tab');
    assert.ok(await yes.evaluate(el => el === document.activeElement));
    await measureContrast(page, report, 'keyboard confirmation yes', 'section[aria-labelledby="confirmation-title"] .nhsw-button--primary', true);
    await page.keyboard.press('Enter');
    await page.getByText('Result saved and read back from persistence.', { exact: true }).waitFor();
    assert.equal(await rows(), 2); assert.match(await page.locator('.nhsw-warning-callout').innerText(), /KdpContactGivenAfterMaxAge/);
    assert.match(await page.locator('main dl').first().innerText(), /Repeat\s*True/);
    const warning = page.locator('.nhsw-warning-callout');
    for (const part of ['heading', 'icon', 'heading-text', 'content']) assert.equal(await warning.locator(`.nhsw-warning-callout__${part}`).count(), 1);
    assert.equal(await warning.locator('.nhsw-warning-callout__icon').getAttribute('aria-hidden'), 'true');
    await inspectState('warning', '.nhsw-warning-callout__heading-text, .nhsw-warning-callout__icon, .nhsw-warning-callout__content p');
    await page.screenshot({ path: `${evidence}/repeat-warning.png`, fullPage: true });
  });
  await check('fresh browser circuit reloads patient-specific saved values', async () => {
    const fresh = await browser.newContext(); const p = await fresh.newPage(); await p.goto(url);
    await p.locator('main dl').nth(1).waitFor(); assert.equal(await p.locator('main dl').count(), 2);
    assert.equal(await p.locator('#heart').inputValue(), ''); await fresh.close();
  });
  assert.deepEqual(errors, []); report.runtimeErrors = errors;
} catch (e) { report.failed = 1; report.error = String(e.stack); process.exitCode = 1; }
finally {
  if (browser) await browser.close(); if (server) { server.kill(); await sleep(500); }
  report.passed = report.checks.length; report.finishedAt = new Date().toISOString();
  report.sourceHashes = {};
  for (const path of ['browser/flow.mjs', 'browser/contrast.mjs', 'src/Components/Pages/Recording.razor', 'src/wwwroot/vendor/nhsw/nhsw.min.css']) report.sourceHashes[path] = createHash('sha256').update(await readFile(`${root}${path}`)).digest('hex');
  await writeFile(`${evidence}/results.json`, JSON.stringify(report, null, 2)); await writeFile(`${evidence}/server.log`, log);
  console.log(JSON.stringify(report, null, 2));
}
