import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const root = fileURLToPath(new URL('../', import.meta.url));
const evidence = path.join(root, 'evidence/browser-preview');
const url = 'http://127.0.0.1:5187/';
const report = { startedAt: new Date().toISOString(), url, browserExecuted: false,
  scope: 'Architecture preview Save and fresh-context Reload only; not the Refactor gate',
  checks: [], failed: 0, skipped: 0, errors: [] };
let server, browser, context, serverLog = '';
const artifacts = [];
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function snapshot(page, name) {
  await page.screenshot({ path: path.join(evidence, `${name}.png`), fullPage: true });
  await writeFile(path.join(evidence, `${name}.html`), await page.content());
  artifacts.push(`${name}.png`, `${name}.html`);
}
async function connect(ctx) {
  const page = await ctx.newPage();
  const circuit = { url: null, sent: 0, received: 0 };
  page.on('pageerror', error => report.errors.push(String(error)));
  page.on('websocket', socket => {
    if (!socket.url().includes('_blazor')) return;
    circuit.url = socket.url();
    socket.on('framesent', () => circuit.sent++);
    socket.on('framereceived', () => circuit.received++);
  });
  await page.goto(url);
  await page.getByRole('heading', { name: '6–8-week contact (KD03)', exact: true }).waitFor();
  for (let i = 0; i < 100 && circuit.received < 2; i++) await sleep(100);
  assert.ok(circuit.url && circuit.received >= 2, 'Live Blazor WebSocket circuit required');
  return { page, circuit };
}
async function savedValues(page) {
  return page.locator('main dl').evaluateAll(nodes => nodes.map(node =>
    Object.fromEntries([...node.querySelectorAll('dt')].map(dt => [dt.textContent, dt.nextElementSibling.textContent]))));
}
async function eventually(check) {
  let last;
  for (let i = 0; i < 100; i++) {
    try { await check(); return; } catch (error) { last = error; await sleep(100); }
  }
  throw last;
}
try {
  await mkdir(evidence, { recursive: true });
  // Refuse an existing process: the browser check requires a freshly seeded app.
  try { await fetch(url); throw new Error('Port 5187 already serves HTTP; stop it before this isolated check'); }
  catch (error) { if (error.message !== 'fetch failed') throw error; }
  server = spawn('dotnet', ['run', '--no-build', '--project', path.join(root, 'src/Hcwp.csproj'), '--urls', url.slice(0, -1)],
    { cwd: root, env: { ...process.env, DemoHistory: 'false', ASPNETCORE_ENVIRONMENT: 'Development' }, stdio: ['ignore', 'pipe', 'pipe'] });
  server.stdout.on('data', chunk => serverLog += chunk);
  server.stderr.on('data', chunk => serverLog += chunk);
  server.on('error', error => report.errors.push(String(error)));
  let ready = false;
  for (let i = 0; i < 150; i++) {
    if (server.exitCode !== null) throw new Error(`App exited: ${serverLog}`);
    try {
      const response = await fetch(url);
      if (response.ok) {
        await writeFile(path.join(root, 'evidence/http-preview.html'), await response.text());
        ready = true; break;
      }
    } catch { /* Wait for startup; failure is bounded, not skipped. */ }
    await sleep(100);
  }
  assert.ok(ready, 'App must start successfully');
  browser = await chromium.launch({ headless: true });
  report.browserExecuted = true;
  report.browser = { name: 'Chromium', version: browser.version(), playwright: '1.64.0' };
  context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  const { page, circuit } = await connect(context);
  assert.deepEqual(await savedValues(page), [], 'Fresh synthetic patient must have no KD03 results');
  await snapshot(page, '01-initial');
  await page.getByLabel('Contact date', { exact: true }).fill('2025-02-20');
  await page.getByLabel('Heart assessment', { exact: true }).selectOption('1');
  const beforeSave = circuit.sent;
  await page.getByRole('button', { name: 'Save KD03 result', exact: true }).click();
  await eventually(async () => {
    assert.equal((await savedValues(page)).length, 1);
    assert.ok(circuit.sent > beforeSave, 'Save must send a browser circuit event');
  });
  const saved = await savedValues(page);
  assert.equal(saved[0]['Patient ID'], '101');
  assert.equal(saved[0].Date, '2025-02-20');
  assert.equal(saved[0].Heart, '1');
  assert.ok(saved[0]['Result ID']);
  assert.equal(await page.getByRole('alert').count(), 0);
  await snapshot(page, '02-saved');
  report.checks.push({ name: 'Save via interactive circuit', status: 'passed', saved, circuit: { ...circuit } });

  // Unsaved form edits must not be echoed into the persisted result display.
  await page.getByLabel('Contact date', { exact: true }).fill('2025-02-21');
  await page.getByLabel('Heart assessment', { exact: true }).selectOption('2');
  const beforeReload = circuit.sent;
  const beforeReloadResponse = circuit.received;
  await page.getByRole('button', { name: 'Reload from persistence', exact: true }).click();
  await eventually(async () => {
    assert.ok(circuit.sent > beforeReload, 'Reload must send a browser circuit event');
    assert.ok(circuit.received > beforeReloadResponse, 'Server must respond to the circuit');
    assert.deepEqual(await savedValues(page), saved);
    assert.equal(await page.getByLabel('Heart assessment', { exact: true }).inputValue(), '2');
    assert.equal(await page.getByLabel('Contact date', { exact: true }).inputValue(), '2025-02-21');
  });
  await snapshot(page, '03-reloaded-with-unsaved-edits');
  report.checks.push({ name: 'Reload ignores unsaved draft changes', status: 'passed', saved: await savedValues(page), circuit: { ...circuit } });
  await context.tracing.stop({ path: path.join(evidence, 'save-reload-trace.zip') });
  artifacts.push('save-reload-trace.zip');
  await context.close();

  // A new browser context creates a new server circuit/form model, not just a DOM refresh.
  context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  const fresh = await connect(context);
  await eventually(async () => assert.deepEqual(await savedValues(fresh.page), saved));
  assert.equal(await fresh.page.getByLabel('Heart assessment', { exact: true }).inputValue(), '');
  assert.equal(await fresh.page.getByLabel('Contact date', { exact: true }).inputValue(), '2025-02-19');
  const beforeFreshReload = fresh.circuit.sent;
  const beforeFreshResponse = fresh.circuit.received;
  await fresh.page.getByRole('button', { name: 'Reload from persistence', exact: true }).click();
  await eventually(async () => {
    assert.ok(fresh.circuit.sent > beforeFreshReload);
    assert.ok(fresh.circuit.received > beforeFreshResponse);
    assert.deepEqual(await savedValues(fresh.page), saved);
  });
  await snapshot(fresh.page, '04-fresh-circuit-reloaded');
  report.checks.push({ name: 'New browser context/circuit reload retains saved patient values', status: 'passed', saved: await savedValues(fresh.page), circuit: { ...fresh.circuit } });
  await context.tracing.stop({ path: path.join(evidence, 'fresh-circuit-trace.zip') });
  artifacts.push('fresh-circuit-trace.zip');
  assert.deepEqual(report.errors, [], 'No browser runtime errors');
} catch (error) {
  report.failed++;
  report.errors.push(error.stack ?? String(error));
  process.exitCode = 1;
} finally {
  await context?.close().catch(() => {});
  await browser?.close().catch(() => {});
  if (server && server.exitCode === null) {
    server.kill('SIGTERM');
    await Promise.race([new Promise(resolve => server.once('exit', resolve)), sleep(5000)]);
    if (server.exitCode === null) server.kill('SIGKILL');
  }
  await writeFile(path.join(evidence, 'server.log'), serverLog);
  report.finishedAt = new Date().toISOString();
  report.passed = report.checks.length;
  report.artifacts = {};
  for (const name of artifacts) report.artifacts[name] = createHash('sha256').update(await readFile(path.join(evidence, name))).digest('hex');
  report.sourceHashes = {};
  for (const name of ['src/Components/Pages/Recording.razor', 'src/Presentation/RecordingPageModel.cs', 'src/Application/Kd03Recording.cs', 'src/Persistence/RecordingContext.cs', 'browser/preview.mjs']) {
    report.sourceHashes[name] = createHash('sha256').update(await readFile(path.join(root, name))).digest('hex');
  }
  await writeFile(path.join(evidence, 'results.json'), JSON.stringify(report, null, 2) + '\n');
  await writeFile(path.join(root, 'evidence/http-preview.json'), JSON.stringify({
    httpStatus: report.browserExecuted ? 200 : null,
    browserExecuted: report.browserExecuted, passed: report.passed, failed: report.failed, skipped: report.skipped,
    browserEvidence: 'browser-preview/results.json',
    claim: report.failed ? 'Preview browser check FAILED; see diagnostics' : 'Executed Chromium preview Save and fresh-circuit persistence Reload only; not comprehensive browser verification'
  }, null, 2) + '\n');
  console.log(JSON.stringify(report));
}
