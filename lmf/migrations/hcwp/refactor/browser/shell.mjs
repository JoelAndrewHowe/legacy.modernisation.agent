// Task-3 English routes, rendered contrast/focus and isolated alert component harness.
import { measureContrast } from './contrast.mjs';
import { execFileSync } from 'node:child_process';
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';

const root = fileURLToPath(new URL('../', import.meta.url));
assert.ok(process.argv[2], 'Explicit evidence directory required');
const evidence = path.resolve(process.argv[2]);
const origin = 'http://127.0.0.1:5193';
const report = { startedAt: new Date().toISOString(), checks: [], errors: [], failed: 0, skipped: 0,
  scope: 'Task 3 English shell/routes, rendered contrast, keyboard link focus and alert fixture presentation; not final bilingual/filter slice gate' };
let server, browser, serverLog = '';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function check(name, action) {
  await action(); report.checks.push({ name, status: 'passed' });
}
async function shell(page, active = 'HCWP results') {
  await page.waitForFunction(() => document.querySelector('.nhsw-skip-link')?.getAttribute('href') === location.pathname + location.search + '#maincontent');
  assert.equal(await page.locator('main#maincontent').count(), 1);
  assert.equal(await page.getByRole('banner').count(), 1);
  assert.equal(await page.getByRole('contentinfo').count(), 1);
  assert.equal(await page.getByRole('link', { name: 'Skip to main content', exact: true }).getAttribute('href'), new URL(page.url()).pathname + new URL(page.url()).search + '#maincontent');
  assert.equal(await page.locator('nav [aria-current="page"]').innerText(), active);
  assert.ok(await page.getByRole('heading', { name: 'Important: Demonstration — synthetic patient data', exact: true }).isVisible());
  assert.ok(await page.getByText('SYN-NHS-101', { exact: true }).isVisible());
  assert.ok(await page.getByText('Health board', { exact: true }).isVisible());
  assert.ok(await page.getByText('SYNORG1, Cardiff and Vale University Health Board', { exact: true }).isVisible());
  assert.equal(await page.getByText('Organisation', { exact: true }).count(), 0);
  assert.equal(await page.getByText('Patient ID', { exact: true }).count(), 0);
  assert.equal(await page.getByText('Result ID', { exact: true }).count(), 0);
  assert.equal(await page.getByText('ClientId', { exact: true }).count(), 0);
  assert.equal(await page.locator('header img').evaluate(img => img.complete && img.naturalWidth > 0), true);
}
async function snapshot(page, name) {
  await page.screenshot({ path: path.join(evidence, `${name}.png`), fullPage: true });
}
try {
  await mkdir(evidence, { recursive: true });
  try { await fetch(origin); throw Error('Port 5193 occupied'); }
  catch (error) { if (error.message !== 'fetch failed') throw error; }
  server = spawn('dotnet', ['run', '--no-build', '--project', path.join(root, 'src/Hcwp.csproj'), '--urls', origin],
    { cwd: root, env: { ...process.env, ASPNETCORE_ENVIRONMENT: 'Development' }, stdio: ['ignore', 'pipe', 'pipe'] });
  server.stdout.on('data', data => serverLog += data);
  server.stderr.on('data', data => serverLog += data);
  let ready = false;
  for (let i = 0; i < 150; i++) {
    if (server.exitCode !== null) throw Error(serverLog);
    try { if ((await fetch(origin + '/results')).ok) { ready = true; break; } } catch {}
    await sleep(100);
  }
  assert.ok(ready, 'Application startup required');
  browser = await chromium.launch({ headless: true });
  report.browser = browser.version();
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const external = [];
  let circuitFrames = 0;
  page.on('websocket', socket => {
    if (socket.url().includes('_blazor')) socket.on('framereceived', () => circuitFrames++);
  });
  async function interactive() {
    for (let i = 0; i < 100 && circuitFrames < 2; i++) await sleep(100);
    assert.ok(circuitFrames >= 2, 'Live interactive Blazor circuit required');
  }
  page.on('request', request => { if (!request.url().startsWith(origin + '/')) external.push(request.url()); });
  page.on('pageerror', error => report.errors.push(String(error)));
  await check('empty results route with shared shell and keyboard skip target', async () => {
    await page.goto(origin + '/results');
    await shell(page);
    await interactive();
    assert.ok(await page.getByText('No saved KD03 results for the selected patient.', { exact: true }).isVisible());
    // FocusOnNavigate initially focuses h1. Walk backwards to the shell skip link.
    for (let i = 0; i < 12; i++) {
      if (await page.locator('.nhsw-skip-link').evaluate(el => el === document.activeElement)) break;
      await page.keyboard.press('Shift+Tab');
    }
    assert.equal(await page.locator(':focus').innerText(), 'Skip to main content');
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => document.activeElement?.id === 'maincontent', null, { timeout: 5000 }).catch(async error => {
      report.focusFailure = await page.evaluate(() => ({ active: document.activeElement?.outerHTML, url: location.href, skip: document.querySelector('.nhsw-skip-link').outerHTML }));
      throw error;
    });
    await snapshot(page, '01-results');
  });
  await check('dedicated record route saves and exposes persisted detail', async () => {
    await page.getByRole('link', { name: 'Record result', exact: true }).click();
    await page.getByRole('heading', { name: '6–8-week contact (KD03)', exact: true }).waitFor();
    await shell(page);
    // Wait for the interactive server circuit, not just prerendered HTML.
    await page.waitForFunction(() => document.querySelector('form') !== null);
    await interactive();
    await page.getByLabel('Contact date', { exact: true }).fill('2025-02-20');
    await page.getByLabel('Heart assessment', { exact: true }).selectOption('1');
    await page.getByRole('button', { name: 'Save KD03 result', exact: true }).click();
    await page.getByText('Result saved and read back from persistence.', { exact: true }).waitFor();
    assert.equal(await page.locator('#saved-results dd').filter({ hasText: /^Satisfactory$/ }).count(), 1);
    await snapshot(page, '02-record-saved');
    await page.getByRole('link', { name: 'View saved result details', exact: true }).click();
    await page.getByRole('heading', { name: 'Result details', exact: true }).waitFor();
    await shell(page);
    assert.ok(await page.getByText('20 February 2025', { exact: true }).isVisible());
    assert.ok(await page.getByText('Satisfactory', { exact: true }).isVisible());
    report.savedDetailPath = new URL(page.url()).pathname;
    await page.reload();
    assert.ok(await page.getByText('Satisfactory', { exact: true }).isVisible());
    await snapshot(page, '03-details');
  });
  await check('history navigation and safe absent-result details', async () => {
    await page.getByRole('link', { name: 'Back to HCWP results', exact: true }).click();
    await shell(page);
    assert.ok(await page.getByRole('link', { name: /View details/ }).isVisible());
    for (const id of ['999999', '2201']) {
      await page.goto(origin + '/results/' + id);
      await shell(page);
      assert.ok(await page.getByText('Result not found for the selected patient.', { exact: true }).isVisible());
      assert.equal(await page.locator('main').getByText('Satisfactory', { exact: true }).count(), 0);
    }
    await page.goto(origin + '/patient-summary');
    await shell(page, 'Patient summary');
  });
  await check('shared shell readable at narrow and wide route layouts', async () => {
    for (const width of [320, 1280]) {
      await page.setViewportSize({ width, height: 900 });
      for (const route of ['/results', report.savedDetailPath, '/record']) {
        await page.goto(origin + route);
        await shell(page);
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `${width}px overflow at ${route}`);
        await snapshot(page, `${width}-${route.replaceAll('/', '-')}`);
      }
    }
  });
  await check('English route rendered contrast and visible keyboard focus on every link', async () => {
    report.keyboardFocus = [];
    for (const width of [320, 1280]) {
      await page.setViewportSize({ width, height: 900 });
      for (const route of ['/patient-summary', '/results', report.savedDetailPath, '/results/999999', '/record']) {
        await page.goto(origin + route);
        await shell(page, route === '/patient-summary' ? 'Patient summary' : 'HCWP results');
        const state = `${width}-${route.replaceAll('/', '-')}`;
        // Text-bearing rendered shell and route content, not the visually-hidden helpers.
        await measureContrast(page, report, state,
          'header .nhsw-site-header__title, nav a, h1, h2, p, dt, dd, label, legend, th, td, main a, button, input:not([type=hidden]), select, footer p');
        assert.equal(await page.getByRole('alert').count(), 0, 'No empty patient alert in normal fixture');
        // Native Tab traversal, not programmatic focus(). Begin at the first shell link.
        for (let i = 0; i < 200; i++) {
          if (await page.locator('.nhsw-skip-link').evaluate(el => el === document.activeElement)) break;
          await page.keyboard.press('Shift+Tab');
        }
        assert.equal(await page.locator('.nhsw-skip-link').evaluate(el => el === document.activeElement), true);
        const links = await page.locator('a[href]').count();
        let tested = 0;
        for (let i = 0; i < 250; i++) {
          if (await page.locator('a:focus').count()) {
            const link = page.locator('a:focus');
            const observation = await link.evaluate(el => {
              const s = getComputedStyle(el), r = el.getBoundingClientRect();
              return { name: el.textContent.trim() || el.querySelector('img')?.alt,
                href: el.getAttribute('href'), focusVisible: el.matches(':focus-visible'),
                outline: s.outline, shadow: s.boxShadow, background: s.backgroundColor,
                visible: r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight };
            });
            assert.ok(observation.focusVisible && observation.visible, JSON.stringify(observation));
            await measureContrast(page, report, state + '-keyboard', 'a:focus', true);
            report.keyboardFocus.push({ state, ...observation });
            await snapshot(page, `${state}-focus-${tested}`);
            tested++;
            if (tested === links) break;
          }
          await page.keyboard.press('Tab');
        }
        assert.equal(tested, links, `Every link reached by Tab at ${state}`);
      }
    }
  });
  await check('approved alert fixture visible and accessible in Chromium component harness', async () => {
    const fixturePath = path.join(evidence, 'alert-fixture.html');
    const output = execFileSync('dotnet', ['run', '--no-build', '--project', path.join(root, 'checks'), '--',
      '--shell-browser-fixture', path.join(root, 'src/patient-summary-fixtures.json'), fixturePath], { encoding: 'utf8' });
    await writeFile(path.join(evidence, 'alert-renderer.json'), output);
    const html = await readFile(fixturePath, 'utf8');
    await page.route(origin + '/__test-only-alert-fixture', route => route.fulfill({ contentType: 'text/html', body: html }));
    report.alert = { method: 'Test-only intercepted document from HtmlRenderer of real PatientBanner with approved alert graph; local pinned CSS; no product route or switching' , layouts: [] };
    for (const width of [320, 1280]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(origin + '/__test-only-alert-fixture');
      const alert = page.getByRole('alert', { name: 'Important: Patient alert — synthetic demonstration', exact: true });
      await alert.scrollIntoViewIfNeeded();
      assert.equal(await alert.count(), 1);
      assert.ok(await alert.isVisible());
      for (const text of ['SYNTHETIC CHILD ALERT — demonstration only', 'SYNTHETIC SECOND ALERT — no clinical meaning']) assert.ok(await alert.getByText(text, { exact: true }).isVisible());
      assert.ok(!(await page.locator('body').innerText()).includes('OTHER-PATIENT'));
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      const ax = await alert.ariaSnapshot();
      await writeFile(path.join(evidence, `alert-${width}-accessibility.yml`), ax);
      assert.ok(ax.includes('alert "Important: Patient alert — synthetic demonstration"'));
      await measureContrast(page, report, `alert-${width}`, 'h2, dt, dd, .nhsw-warning-callout p');
      report.alert.layouts.push({ width, role: 'alert', name: await alert.getAttribute('aria-labelledby'), text: await alert.innerText(), accessibilitySnapshot: `alert-${width}-accessibility.yml` });
      await snapshot(page, `alert-${width}`);
    }
  });
  await check('reviewed local assets and no external requests/runtime errors', async () => {
    report.assetSha256 = {};
    for (const [asset, expected] of Object.entries({
      'nhsw-logo.svg': '41d8993c511627d36aea058c397b5a743ef9c17031a8dbba62fa826404cf4df7',
      'nhsw.min.css': '117106cd1129ddfc0dae636d123d9123583c8f3970ebad63e2295d63bb502d99'
    })) {
      const bytes = await readFile(path.join(root, 'src/wwwroot/vendor/nhsw', asset));
      const hash = createHash('sha256').update(bytes).digest('hex');
      assert.equal(hash, expected);
      const response = await fetch(`${origin}/vendor/nhsw/${asset}`);
      assert.ok(response.ok);
      assert.equal(createHash('sha256').update(Buffer.from(await response.arrayBuffer())).digest('hex'), expected);
      report.assetSha256[asset] = hash;
    }
    assert.deepEqual(external, []);
    assert.deepEqual(report.errors, []);
  });
} catch (error) {
  report.failed++; report.errors.push(error.stack ?? String(error)); process.exitCode = 1;
} finally {
  await browser?.close();
  if (server && server.exitCode === null) {
    server.kill('SIGTERM');
    await Promise.race([new Promise(resolve => server.once('exit', resolve)), sleep(5000)]);
    if (server.exitCode === null) server.kill('SIGKILL');
  }
  report.finishedAt = new Date().toISOString();
  report.passed = report.checks.length;
  report.total = report.passed + report.failed;
  if (!report.passed) { report.failed = Math.max(1, report.failed); process.exitCode = 1; }
  await mkdir(evidence, { recursive: true });
  await writeFile(path.join(evidence, 'server.log'), serverLog);
  await writeFile(path.join(evidence, 'results.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report));
}
