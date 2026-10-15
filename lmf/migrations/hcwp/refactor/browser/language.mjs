// Task 5 language and retention checks in the existing Playwright/Chromium stack.
import { measureContrast } from './contrast.mjs';
import { chromium } from 'playwright';
import { spawn, execFileSync } from 'node:child_process';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
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
    await page.locator('header[data-ready="true"]').waitFor();
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
  await check('Bilingual route accessibility, responsive layouts and rendered contrast', async () => {
    for (const code of ['en', 'cy']) {
      await language(code);
      for (const width of [320, 1280]) {
        await page.setViewportSize({ width, height: 900 });
        for (const requestedRoute of ['/results?page=2', 'detail', '/results/999999', '/record', '/patient-summary']) {
          const route = requestedRoute === 'detail' ? report.detailRoute : requestedRoute;
          assert.ok(route, 'A saved detail route is required');
          await page.goto(origin + route);
          await page.waitForFunction(code => document.documentElement.lang === code, code);
          await page.locator('h1').waitFor();
          // Wait for the interactive shell rather than sampling during prerender replacement.
          await language(code === 'en' ? 'cy' : 'en'); await language(code);
          if (route.startsWith('/results?')) {
            await page.locator('form[data-ready="true"]').waitFor();
            report.detailRoute = await page.locator('article a').first().getAttribute('href');
          }
          assert.equal(await page.locator('main#maincontent').count(), 1);
          assert.equal(await page.getByRole('banner').count(), 1);
          assert.equal(await page.getByRole('contentinfo').count(), 1);
          assert.equal(await page.locator('h1').count(), 1);
          assert.equal(await page.locator('.nhsw-site-header__nav [aria-current="page"]').count(), 1);
          assert.equal(await page.getByRole('alert').count(), 0, 'No empty patient alert');
          assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
          const controls = page.locator('main input:not([type=hidden]), main select');
          for (let i = 0; i < await controls.count(); i++) {
            const control = controls.nth(i), id = await control.getAttribute('id');
            assert.ok(id);
            assert.equal(await page.locator(`label[for="${id}"]`).count(), 1);
            assert.ok((await page.locator(`label[for="${id}"]`).innerText()).trim());
          }
          const state = `${code}-${width}-${route.replaceAll(/[^a-z0-9]/gi, '-')}`;
          await page.locator('h1').click(); // Neutral state; focused controls are sampled separately below.
          await measureContrast(page, report, state, 'nav a, h1, h2, p, dt, dd, label, legend, th, td, main a, button, input:not([type=hidden]), select, footer p');
          // Native keyboard traversal of every enabled form control (no focus()).
          const ids = await controls.evaluateAll(els => els.filter(el => !el.disabled).map(el => el.id));
          const reached = new Set();
          for (let i = 0; i < 250 && reached.size < ids.length; i++) {
            await page.keyboard.press('Tab');
            const id = await page.evaluate(() => document.activeElement?.id);
            if (ids.includes(id) && !reached.has(id)) {
              reached.add(id);
              await measureContrast(page, report, state + '-focus', `#${id}`, true);
            }
          }
          assert.equal(reached.size, ids.length, `Keyboard reachability: ${state}`);
          const actions = page.locator('a[href], button:not(:disabled)');
          const actionCount = await actions.count();
          const seenActions = new Set();
          for (let i = 0; i < 350 && seenActions.size < actionCount; i++) {
            await page.keyboard.press('Tab');
            const index = await actions.evaluateAll(els => els.indexOf(document.activeElement));
            if (index < 0 || seenActions.has(index)) continue;
            seenActions.add(index);
            assert.ok((await actions.nth(index).innerText()).trim(), 'Accessible action text');
            await measureContrast(page, report, state + '-action-focus', 'a:focus, button:focus', true);
          }
          assert.equal(seenActions.size, actionCount, `All links/buttons keyboard reachable: ${state}`);
          // Keyboard activation of the shell skip link lands on the named main target.
          for (let i = 0; i < 350; i++) {
            if (await page.locator('.nhsw-skip-link').evaluate(el => el === document.activeElement)) break;
            await page.keyboard.press('Tab');
          }
          assert.ok(await page.locator('.nhsw-skip-link').evaluate(el => el === document.activeElement));
          await page.keyboard.press('Enter');
          await page.waitForFunction(() => document.activeElement?.id === 'maincontent');
          await writeFile(path.join(evidence, state + '.yml'), await page.locator('main').ariaSnapshot());
          await page.screenshot({ path: path.join(evidence, state + '.png'), fullPage: true });
        }
      }
    }
  });
  await check('Bilingual validation summary links and field associations', async () => {
    for (const code of ['en', 'cy']) {
      await language(code);
      await page.goto(origin + '/record');
      await page.locator('form[data-ready="true"]').waitFor();
      // A complete language round trip proves server event handlers attached.
      await language(code === 'en' ? 'cy' : 'en'); await language(code);
      await page.locator('#Height').fill('-1'); await page.locator('#Height').press('Tab');
      await page.locator('button[type=submit]').click();
      await page.locator('.nhsw-error-summary, #confirmation-title').first().waitFor();
      if (await page.locator('#confirmation-title').isVisible()) {
        await page.locator('section[aria-labelledby="confirmation-title"] button').first().click();
      }
      const summary = page.locator('.nhsw-error-summary');
      await summary.waitFor();
      assert.equal(await summary.getAttribute('role'), 'alert');
      assert.ok(await summary.getAttribute('aria-labelledby'));
      const links = summary.locator('a'); assert.ok(await links.count());
      for (let i = 0; i < await links.count(); i++) {
        const link = links.nth(i), target = await link.getAttribute('href');
        assert.ok(target.startsWith('#'));
        const field = page.locator(target);
        assert.equal(await field.getAttribute('aria-invalid'), 'true');
        const described = await field.getAttribute('aria-describedby');
        assert.ok(described); assert.ok(await page.locator('#' + described).isVisible());
        await link.click();
        await page.waitForFunction(id => document.activeElement?.id === id, target.slice(1));
      }
      for (const width of [320, 1280]) {
        await page.setViewportSize({ width, height: 900 });
        await page.locator('h1').click();
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        await measureContrast(page, report, `${code}-${width}-validation`, '.nhsw-error-summary h2, .nhsw-error-summary a, .nhsw-error-message, #Height');
        await page.screenshot({ path: path.join(evidence, `${code}-${width}-validation.png`), fullPage: true });
      }
    }
  });
  await check('English and Welsh alert fixture announcement, contrast and narrow/wide layouts', async () => {
    const fixture = path.join(evidence, 'alert.html');
    const output = execFileSync('dotnet', ['run', '--no-build', '--project', path.join(root, 'checks'), '--',
      '--shell-browser-fixture', path.join(root, 'src/patient-summary-fixtures.json'), fixture], { encoding: 'utf8' });
    const renderer = JSON.parse(output);
    assert.ok(renderer.passed > 0 && renderer.total === renderer.passed && renderer.failed === 0 && renderer.skipped === 0);
    await writeFile(path.join(evidence, 'alert-renderer.json'), output);
    for (const code of ['en', 'cy']) {
      const html = await readFile(code === 'en' ? fixture : fixture + '.cy.html', 'utf8');
      const url = origin + '/__test-only-alert-' + code;
      await page.route(url, route => route.fulfill({ contentType: 'text/html', body: html }));
      for (const width of [320, 1280]) {
        await page.setViewportSize({ width, height: 900 }); await page.goto(url);
        assert.equal(await page.locator('html').getAttribute('lang'), code);
        const alert = page.getByRole('alert');
        assert.equal(await alert.count(), 1);
        assert.equal(await alert.getAttribute('aria-labelledby'), 'patient-alert-title');
        assert.ok(await alert.isVisible());
        assert.ok((await alert.innerText()).includes('SYNTHETIC CHILD ALERT'));
        assert.ok((await alert.innerText()).includes('SYNTHETIC SECOND ALERT'));
        assert.ok(!(await page.locator('body').innerText()).includes('OTHER-PATIENT'));
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        await measureContrast(page, report, `${code}-${width}-alert`, 'h2, dt, dd, .nhsw-warning-callout p');
        await writeFile(path.join(evidence, `${code}-${width}-alert.yml`), await alert.ariaSnapshot());
        await page.screenshot({ path: path.join(evidence, `${code}-${width}-alert.png`), fullPage: true });
      }
    }
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
