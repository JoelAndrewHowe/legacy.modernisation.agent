// Task 5 language and retention checks in the existing Playwright/Chromium stack.
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
const root = fileURLToPath(new URL('../', import.meta.url));
assert.ok(process.argv[2], 'Evidence directory required');
const evidence = path.resolve(process.argv[2]);
const origin = 'http://127.0.0.1:5195';
const report = { startedAt: new Date().toISOString(), checks: [], errors: [], skipped: 0 };
let server, browser, log = '';
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function check(name, action) { await action(); report.checks.push({ name, status: 'passed' }); }
try {
  await mkdir(evidence, { recursive: true });
  try { await fetch(origin); throw Error('Port occupied'); } catch (e) { if (e.message !== 'fetch failed') throw e; }
  server = spawn('dotnet', ['run', '--no-build', '--project', path.join(root, 'src'), '--urls', origin],
    { stdio: ['ignore', 'pipe', 'pipe'] });
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
  async function language(code) {
    await page.getByRole('button', { name: code === 'cy' ? 'Cymraeg' : 'English', exact: true }).click();
    await page.waitForFunction(code => document.documentElement.lang === code, code);
    await page.getByRole('button', { name: code === 'cy' ? 'Cymraeg' : 'English', exact: true, pressed: true }).waitFor();
  }
  const listUrl = origin + '/results?state=Recorded&size=10&page=2';
  await check('English default, Welsh document language and list URL retained', async () => {
    await page.goto(listUrl); await page.locator('form[data-ready="true"]').waitFor();
    assert.equal(await page.locator('html').getAttribute('lang'), 'en');
    await language('cy'); assert.equal(page.url(), listUrl);
    await page.getByRole('heading', { name: 'Canlyniadau Rhaglen Plant Iach Cymru', exact: true }).waitFor();
    await page.getByText('Yn dangos 11–18 o 18 canlyniad.', { exact: true }).waitFor();
    assert.ok(await page.getByText('Cymraeg drafft', { exact: false }).count());
  });
  await check('Welsh survives reload and detail-return restores page/filter', async () => {
    await page.reload(); await page.locator('form[data-ready="true"]').waitFor();
    await page.getByRole('link', { name: /^Gweld manylion/ }).first().click();
    await page.getByRole('heading', { name: 'Manylion y canlyniad', exact: true }).waitFor();
    await page.getByRole('heading', { name: 'Gwybodaeth am y plentyn a\'r teulu', exact: true }).waitFor();
    await language('en'); await page.getByRole('heading', { name: 'Result details', exact: true }).waitFor();
    await page.getByRole('link', { name: 'Back to HCWP results', exact: true }).click();
    assert.equal(page.url(), listUrl);
    assert.equal(await page.locator('#state-Recorded').isChecked(), true);
  });
  await check('Unsaved draft retained across both switches and internal navigation', async () => {
    await page.getByRole('link', { name: 'Record result', exact: true }).click();
    await page.locator('#Height').fill('61.5'); await page.locator('#Height').press('Tab');
    await page.locator('#heart').selectOption('2');
    const date = await page.locator('#contact-date').inputValue();
    await language('cy');
    await page.getByRole('button', { name: 'Cadw canlyniad KD03', exact: true }).waitFor();
    assert.equal(await page.locator('#Height').inputValue(), '61.5');
    assert.equal(await page.locator('#heart').inputValue(), '2');
    assert.equal(await page.locator('#contact-date').inputValue(), date);
    await page.getByRole('link', { name: 'Yn ôl i ganlyniadau Rhaglen Plant Iach Cymru', exact: true }).click();
    await page.getByRole('link', { name: 'Cofnodi canlyniad', exact: true }).click();
    assert.equal(await page.locator('#Height').inputValue(), '61.5');
    await language('en'); assert.equal(await page.locator('#heart').inputValue(), '2');
  });
  await check('Bilingual narrow/wide shell and recording labels without overflow', async () => {
    for (const code of ['en', 'cy']) {
      await language(code);
      for (const width of [320, 1280]) {
        await page.setViewportSize({ width, height: 900 });
        const overflow = await page.evaluate(() => [...document.querySelectorAll('body *')].filter(el => el.getBoundingClientRect().right > innerWidth + 1).map(el => ({ tag: el.tagName, class: el.className, text: el.textContent.slice(0, 180), right: el.getBoundingClientRect().right })));
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Overflow ${code}/${width}: ${JSON.stringify(overflow)}`);
        assert.equal(await page.locator('main').count(), 1);
        assert.equal(await page.locator('h1').count(), 1);
        assert.equal(await page.locator('label[for="heart"]').innerText(), code === 'cy' ? 'Asesiad y galon' : 'Heart assessment');
        await page.screenshot({ path: path.join(evidence, `${code}-${width}-draft.png`), fullPage: true });
      }
    }
  });
  await check('Welsh invalid-filter fallback, localized summary and unchanged URL', async () => {
    const url = origin + '/results?state=bad&from=nope&page=999';
    await page.goto(url); await page.locator('form[data-ready="true"]').waitFor();
    await page.getByRole('heading', { name: 'Hidlyddion annilys', exact: true }).waitFor();
    await page.getByRole('link', { name: 'Anwybyddwyd gwerthoedd cyflwr annilys neu nad ydynt ar gael.', exact: true }).waitFor();
    assert.equal(page.url(), url);
    await language('en');
    await page.getByRole('heading', { name: 'Invalid filters', exact: true }).waitFor();
  });
  await check('No unexpected external requests or runtime errors', async () => { assert.deepEqual(external, []); assert.deepEqual(report.errors, []); });
} catch (error) { report.errors.push(error.stack || String(error)); }
finally {
  if (browser) await browser.close();
  if (server) { server.kill('SIGTERM'); await new Promise(r => server.once('exit', r)); }
  report.total = report.checks.length + (report.errors.length ? 1 : 0);
  report.passed = report.checks.length; report.failed = report.errors.length ? 1 : 0;
  report.finishedAt = new Date().toISOString();
  await mkdir(evidence, { recursive: true });
  await writeFile(path.join(evidence, 'results.json'), JSON.stringify(report, null, 2) + '\n');
  await writeFile(path.join(evidence, 'server.log'), log);
  console.log(JSON.stringify(report));
}
process.exit(report.failed || !report.passed ? 1 : 0);
