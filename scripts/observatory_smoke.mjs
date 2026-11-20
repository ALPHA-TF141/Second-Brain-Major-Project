// Requires a running research API + Vite proxy and optional `playwright` package.
// Use a throwaway database: this test creates a synthetic note and a benchmark run.
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';
import assert from 'node:assert/strict';

const url = process.env.OBSERVATORY_URL || 'http://127.0.0.1:5173';
mkdirSync('artifacts/observatory', { recursive: true });
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  const captureRequests = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('request', r => { if (r.url().includes('/capture/start')) captureRequests.push(r.url()); });
  await page.goto(url);
  await page.locator('.ro-comparison tbody tr').first().waitFor({ timeout: 30000 });
  await page.screenshot({ path: 'artifacts/observatory/benchmark.png' });
  await page.getByRole('button', { name: 'Run core experiment', exact: true }).click();
  await page.getByText(/Measured isolated run #/).waitFor({ timeout: 90000 });
  console.log('PASS: core experiment completed in browser');
  await page.getByRole('button', { name: 'Live calculations', exact: true }).click();
  await page.getByText('Memory importance, fully expanded', { exact: true }).waitFor();
  const beforeCount = Number(await page.locator('.ro-counts .ro-kpi strong').first().textContent());
  const probeToken = `obsprobe${Date.now()}`;
  const created = await page.evaluate(async (probeToken) => {
    const r = await fetch('/api/memory/memories', { method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + localStorage.getItem('second_brain_token') },
      body: JSON.stringify({ content: `Synthetic observatory browser smoke research note ${probeToken}.`, title: 'Synthetic browser verification' }) });
    return { status: r.status, data: await r.json() };
  }, probeToken);
  assert.equal(created.status, 201, JSON.stringify(created));
  await page.waitForFunction(count => Number(document.querySelector('.ro-counts .ro-kpi strong')?.textContent) > count, beforeCount, { timeout: 15000 });
  await page.screenshot({ path: 'artifacts/observatory/live.png' });
  console.log('PASS: new note reflected by live score polling');
  await page.getByLabel('Live retrieval query', { exact: true }).fill(probeToken);
  const probeResponse = page.waitForResponse(r => r.url().includes('/api/observatory/probe') && r.status() === 200);
  await page.getByRole('button', { name: 'Inspect live retrieval', exact: true }).click();
  const firstProbe = await (await probeResponse).json();
  assert(firstProbe.results.some(r => r.memory_id === created.data.id));
  const updatedProbe = page.waitForResponse(r => r.url().includes('/api/observatory/probe') && r.status() === 200, { timeout: 20000 });
  await page.evaluate(async id => {
    const r = await fetch(`/api/memory/memories/${id}`, { method: 'DELETE', headers: { Authorization: 'Bearer ' + localStorage.getItem('second_brain_token') } });
    if (!r.ok) throw Error('Failed to forget smoke note');
  }, created.data.id);
  const afterForget = await (await updatedProbe).json();
  assert(!afterForget.results.some(r => r.memory_id === created.data.id));
  console.log('PASS: live probe automatically updated after forgetting');
  await page.getByRole('button', { name: 'All research artifacts', exact: true }).click();
  await page.getByRole('button', { name: 'Inspect artifact', exact: true }).click();
  await page.getByPlaceholder('Find a number by its data path…').waitFor();
  console.log('PASS: historical artifact explorer');
  await page.setViewportSize({ width: 800, height: 900 });
  await page.getByRole('button', { name: 'IEEE benchmark', exact: true }).click();
  await page.locator('.ro-comparison tbody tr').first().waitFor();
  await page.screenshot({ path: 'artifacts/observatory/tablet.png' });
  assert.deepEqual(errors, [], 'Uncaught browser errors');
  assert.deepEqual(captureRequests, [], 'Capture must not start automatically');
  console.log('PASS: no uncaught page errors or automatic screen capture');
} finally {
  await browser.close();
}
