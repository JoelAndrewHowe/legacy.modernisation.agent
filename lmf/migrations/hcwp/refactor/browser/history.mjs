// Task 4: real default synthetic history and URL-backed query flow, not the final bilingual gate.
import { chromium } from 'playwright';
import { measureContrast } from './contrast.mjs';
import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
const root = fileURLToPath(new URL('../', import.meta.url));
assert.ok(process.argv[2], 'Evidence directory required');
const evidence = path.resolve(process.argv[2]);
const origin = 'http://127.0.0.1:5194';
const report = { startedAt: new Date().toISOString(), checks: [], errors: [], skipped: 0 };
let server, browser, log = '';
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function check(name, action) { await action(); report.checks.push({ name, status: 'passed' }); }
try {
  await mkdir(evidence, { recursive: true });
  try { await fetch(origin); throw Error('Port occupied'); } catch (e) { if (e.message !== 'fetch failed') throw e; }
  server = spawn('dotnet', ['run', '--no-build', '--project', path.join(root, 'src'), '--urls', origin],
    { env: { ...process.env, DemoHistory: 'true' }, stdio: ['ignore', 'pipe', 'pipe'] });
  server.stdout.on('data', d => log += d); server.stderr.on('data', d => log += d);
  let ready = false;
  for (let i = 0; i < 150; i++) {
    if (server.exitCode !== null) throw Error(log);
    try { if ((await fetch(origin + '/results')).ok) { ready = true; break; } } catch {}
    await sleep(100);
  }
  assert.ok(ready, 'Application must start');
  browser = await chromium.launch({ headless: true }); report.browser = browser.version();
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const external = []; page.on('request', r => { if (!r.url().startsWith(origin + '/')) external.push(r.url()); });
  page.on('pageerror', e => report.errors.push(String(e)));
  async function range(text) { await page.getByText(text, { exact: true }).waitFor(); }
  await check('23 results, 10 rows, third page and no other patient detail', async () => {
    await page.goto(origin + '/results'); await range('Showing 1–10 of 23 results.');
    await page.locator('header[data-ready="true"]').waitFor();
    await page.locator('form[data-ready="true"]').waitFor();
    assert.equal(await page.locator('article').count(), 10);
    await page.getByRole('link', { name: 'Page 3', exact: true }).click();
    await range('Showing 21–23 of 23 results.');
    assert.equal(await page.locator('nav[aria-label="Results pages"] .nhsw-pagination__list > .nhsw-pagination__item--current [aria-current="page"]').innerText(), '3');
    assert.equal(await page.locator('.nhsw-pagination__list > li').count(), 3);
    await page.locator('h1').click(); // Compare neutral current-page styling, not retained click focus.
    const colours = await page.locator('.nhsw-pagination__number-link').evaluateAll(links => links.map(el => getComputedStyle(el).backgroundColor));
    report.paginationColours = colours;
    assert.notEqual(colours[2], colours[0], 'Current page must be visually distinct: ' + JSON.stringify(colours));
    await page.reload(); await range('Showing 21–23 of 23 results.');
    await page.screenshot({ path: path.join(evidence, 'third-page.png'), fullPage: true });
  });
  await check('details restore list state and complete labelled groups', async () => {
    const url = page.url();
    await page.getByRole('link', { name: /^View details/ }).first().click();
    for (const name of ['Contact details', 'Measurements', 'Physical assessments', 'Child and family information', 'Location and professional', 'Recording metadata'])
      await page.getByRole('heading', { name, exact: true }).waitFor();
    assert.ok(await page.getByText('Not recorded', { exact: true }).count() > 0);
    assert.equal(await page.getByText(/HISTA|HISTB|HISTX|HISTY|8024/).count(), 0);
    await page.screenshot({ path: path.join(evidence, 'details.png'), fullPage: true });
    await page.getByRole('link', { name: 'Back to HCWP results', exact: true }).click();
    assert.equal(page.url(), url); await range('Showing 21–23 of 23 results.');
  });
  await check('filter resets page, AND categories, active summary, reload and clear', async () => {
    await page.getByLabel('Recorded', { exact: true }).check();
    await page.getByLabel('Repeat', { exact: true }).check();
    await page.getByRole('button', { name: 'Apply filters and page size' }).click();
    await range('Showing 1–6 of 6 results.');
    assert.equal(new URL(page.url()).searchParams.get('page'), null);
    assert.ok((await page.locator('section[aria-labelledby="active-filters"]').innerText()).includes('Recorded; Repeat'));
    await page.reload(); await range('Showing 1–6 of 6 results.');
    await page.getByLabel('Results per page', { exact: true }).selectOption('25');
    assert.equal(await page.getByLabel('Results per page', { exact: true }).inputValue(), '25');
    await page.getByRole('button', { name: 'Apply filters and page size' }).click();
    await page.waitForURL(url => url.searchParams.get('size') === '25').catch(async e => { report.sizeFailure = { url: page.url(), html: await page.locator('form').innerHTML() }; throw e; });
    await range('Showing 1–6 of 6 results.');
    assert.equal(new URL(page.url()).searchParams.get('size'), '25');
    await page.getByRole('link', { name: 'Clear all filters', exact: true }).click();
    await range('Showing 1–10 of 23 results.');
  });
  await check('approved Invalid filters error summary, safe fallbacks and retained valid values', async () => {
    async function summary(messages) {
      const alert = page.getByRole('alert').filter({ has: page.getByRole('heading', { name: 'Invalid filters', exact: true }) });
      await alert.waitFor();
      assert.equal(await alert.getAttribute('aria-labelledby'), 'invalid-filters-title');
      assert.equal(await alert.locator('li').count(), messages.length);
      for (const message of messages) {
        const link = alert.getByRole('link', { name: message, exact: true });
        assert.equal(await link.getAttribute('href'), '#results-filters');
      }
      await page.locator('form[data-ready="true"]').waitFor();
      await alert.getByRole('link').first().click();
      await page.waitForFunction(() => document.activeElement.id === 'results-filters');
    }
    await page.goto(origin + '/results?state=bad&location=otherpatient&from=nope&page=999&size=11');
    await range('Showing 21–23 of 23 results.');
    await summary(['Invalid from date ignored.', 'Invalid or unavailable state values ignored.',
      'Invalid or unavailable location values ignored.', 'Invalid size ignored.',
      'Page outside result range; showing the nearest valid page.']);
    assert.equal(await page.getByRole('checkbox', { checked: true }).count(), 0);
    assert.equal(await page.getByLabel('Results per page', { exact: true }).inputValue(), '10');
    await page.screenshot({ path: path.join(evidence, 'invalid-filters.png'), fullPage: true });
    await page.goto(origin + '/results?state=Recorded&state=bad&repeat=repeat&page=bad&size=bad');
    await range('Showing 1–6 of 6 results.');
    await summary(['Invalid or unavailable state values ignored.', 'Invalid page ignored.', 'Invalid size ignored.']);
    assert.equal(await page.getByLabel('Recorded', { exact: true }).isChecked(), true);
    assert.equal(await page.getByLabel('Repeat', { exact: true }).isChecked(), true);
    assert.equal(await page.getByLabel('Results per page', { exact: true }).inputValue(), '10');
    await page.goto(origin + '/results'); await range('Showing 1–10 of 23 results.');
    assert.equal(await page.locator('.nhsw-error-summary').count(), 0);
  });
  await check('inclusive dates and empty state on narrow viewport', async () => {
    await page.goto(origin + '/results?from=2025-01-02&to=2025-01-03'); await range('Showing 1–6 of 6 results.');
    await page.goto(origin + '/results?from=2099-01-01&page=999'); await range('Showing 0–0 of 0 results.');
    await page.getByText('No saved KD03 results match the selected filters.', { exact: true }).waitFor();
    await page.setViewportSize({ width: 320, height: 900 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({ path: path.join(evidence, 'empty-narrow.png'), fullPage: true });
  });
  await check('task-4 controls: keyboard operation, visible focus and rendered contrast at 320/1280px', async () => {
    report.controlKeyboard = [];
    for (const width of [320, 1280]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(origin + '/results?from=2025-01-02&to=2025-01-03');
      await page.locator('form[data-ready="true"]').waitFor();
      const controls = page.locator('form input, form select');
      const ids = await controls.evaluateAll(els => els.map(el => el.id));
      assert.equal(ids.length, 15, 'All twelve checkboxes, two dates and page-size select');
      await measureContrast(page, report, `${width}-controls-default`, 'form label, form legend, form input, form select');
      // Reach the skip link with real keys, then walk forwards through every control.
      for (let i = 0; i < 200; i++) {
        if (await page.locator('.nhsw-skip-link').evaluate(el => el === document.activeElement)) break;
        await page.keyboard.press('Shift+Tab');
      }
      assert.equal(await page.locator('.nhsw-skip-link').evaluate(el => el === document.activeElement), true);
      const seen = [];
      for (let i = 0; i < 160 && seen.length < ids.length; i++) {
        await page.keyboard.press('Tab');
        const id = await page.evaluate(() => document.activeElement?.id);
        if (!ids.includes(id) || seen.includes(id)) continue; // Native dates have several keyboard segments.
        seen.push(id);
        const control = page.locator(`[id="${id}"]`);
        const type = await control.getAttribute('type');
        const before = await control.inputValue();
        if (type === 'checkbox') {
          await page.keyboard.press('Space'); assert.equal(await control.isChecked(), true);
        } else {
          await page.keyboard.press(type === 'date' ? 'ArrowUp' : 'ArrowDown');
          assert.notEqual(await control.inputValue(), before, `${id} must respond to keyboard`);
        }
        await measureContrast(page, report, `${width}-${id}-keyboard-focus`, `[id="${id}"]`, true);
        const observation = await control.evaluate(el => {
          const target = el.type === 'checkbox' ? el.nextElementSibling : el;
          const style = getComputedStyle(target, el.type === 'checkbox' ? '::before' : null);
          const rect = target.getBoundingClientRect();
          return { id: el.id, value: el.value, checked: el.checked, focused: el === document.activeElement,
            outline: style.outline, border: style.border, shadow: style.boxShadow,
            rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height } };
        });
        assert.ok(observation.focused);
        assert.ok(observation.rect.x >= 0 && observation.rect.x + observation.rect.width <= width);
        report.controlKeyboard.push({ width, ...observation });
        await page.screenshot({ path: path.join(evidence, `keyboard-${width}-${id}.png`) });
        if (type === 'checkbox') { await page.keyboard.press('Space'); assert.equal(await control.isChecked(), false); }
        else if (type === 'date') { await page.keyboard.press('ArrowDown'); assert.equal(await control.inputValue(), before); }
        else assert.equal(await control.inputValue(), '25');
      }
      assert.deepEqual(seen, ids, 'Native Tab order covers every task-4 control');
      // Tab from the select to Apply and submit the keyboard-edited page size.
      await page.keyboard.press('Tab');
      assert.equal(await page.locator('button[type="submit"]').evaluate(el => el === document.activeElement), true);
      await page.keyboard.press('Enter');
      await page.waitForURL(url => url.searchParams.get('size') === '25');
      await range('Showing 1–6 of 6 results.');
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({ path: path.join(evidence, `controls-${width}.png`), fullPage: true });
    }
  });
  await check('safe other-patient and missing result routes', async () => {
    for (const id of [8024, 999999]) {
      await page.goto(origin + '/results/' + id + '?page=2');
      await page.getByText('Result not found for the selected patient.', { exact: true }).waitFor();
      assert.equal(await page.locator('main article').count(), 0);
    }
  });
  await check('no external runtime requests', async () => assert.deepEqual(external, []));
} catch (error) { report.errors.push(String(error.stack ?? error)); }
finally {
  if (browser) await browser.close(); if (server) { server.kill('SIGTERM'); await sleep(300); }
  report.failed = report.errors.length; report.passed = report.checks.length; report.total = report.passed + report.failed;
  report.finishedAt = new Date().toISOString();
  await writeFile(path.join(evidence, 'server.log'), log);
  await writeFile(path.join(evidence, 'results.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report));
}
process.exitCode = report.failed || !report.passed ? 1 : 0;
