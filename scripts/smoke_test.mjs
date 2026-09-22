/**
 * Jarvis OS - End-to-End Route Smoke Test
 * =======================================
 * Boots the real backend (uvicorn) + the real frontend (vite), then loads EVERY
 * route from src/routes/AppRoutes.jsx in a real Chromium browser and reports:
 *
 *   - uncaught page exceptions (the class of bug that causes blank screens)
 *   - console errors
 *   - the ErrorBoundary "DIAGNOSTIC EXCEPTION" panel
 *   - routes that render nothing (empty root)
 *
 * Run:  npm run smoke
 * Exit code 0 = every route rendered clean, 1 = something is broken.
 */
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import process from 'node:process';

const ROOT = dirname(fileURLToPath(import.meta.url)) + '/..';
const IS_WIN = process.platform === 'win32';
const ARTIFACTS = join(ROOT, 'artifacts', 'smoke');
const FRONTEND_URL = process.env.SMOKE_FRONTEND_URL || 'http://127.0.0.1:5173';
const BACKEND_URL = process.env.SMOKE_BACKEND_URL || 'http://127.0.0.1:8000';

const C = { g: '\x1b[92m', r: '\x1b[91m', y: '\x1b[93m', d: '\x1b[2m', x: '\x1b[0m' };

/* -------------------------------------------------------------------------- */
/* discover routes straight from the router so this never goes stale          */
/* -------------------------------------------------------------------------- */
function discoverRoutes() {
  const src = readFileSync(join(ROOT, 'src', 'routes', 'AppRoutes.jsx'), 'utf8');
  const routes = [];
  // standalone routes (outside the AppLayout shell) also count
  for (const m of src.matchAll(/<Route\s+path="([^"]+)"/g)) {
    const path = m[1];
    if (path === '*') continue;
    routes.push(path === '/' ? '/' : path);
  }
  return [...new Set(routes)];
}

/* -------------------------------------------------------------------------- */
/* process helpers                                                            */
/* -------------------------------------------------------------------------- */
const children = [];
function launch(name, cmd, args, cwd, env = {}) {
  const child = spawn(cmd, args, {
    cwd,
    env: { ...process.env, ...env },
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: false,
  });
  child.stdout.on('data', (d) => {
    if (process.env.SMOKE_VERBOSE) process.stdout.write(`${C.d}[${name}] ${d}${C.x}`);
  });
  child.stderr.on('data', (d) => {
    if (process.env.SMOKE_VERBOSE) process.stdout.write(`${C.d}[${name}] ${d}${C.x}`);
  });
  child.on('exit', (code) => {
    if (code !== 0 && code !== null && !child.killed) {
      console.log(`${C.y}[${name}] exited with code ${code}${C.x}`);
    }
  });
  children.push(child);
  return child;
}

function shutdown() {
  for (const c of children) {
    try {
      if (IS_WIN) spawn('taskkill', ['/pid', String(c.pid), '/f', '/t']);
      else c.kill('SIGTERM');
    } catch {
      /* ignore */
    }
  }
}

async function waitFor(url, timeoutMs, label) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(2500) });
      if (res.status < 500) return true;
    } catch {
      /* not up yet */
    }
    await new Promise((r) => setTimeout(r, 700));
  }
  console.log(`${C.y}  ! ${label} did not respond within ${timeoutMs / 1000}s - continuing anyway${C.x}`);
  return false;
}

function venvPython() {
  const candidates = IS_WIN
    ? [join(ROOT, 'backend', '.venv', 'Scripts', 'python.exe')]
    : [join(ROOT, 'backend', '.venv', 'bin', 'python')];
  return candidates.find((p) => existsSync(p)) || null;
}

/* -------------------------------------------------------------------------- */
/* main                                                                       */
/* -------------------------------------------------------------------------- */
async function main() {
  const routes = discoverRoutes();
  console.log(`\n${'='.repeat(74)}`);
  console.log('  JARVIS OS - END-TO-END ROUTE SMOKE TEST (real Chromium)');
  console.log(`${'='.repeat(74)}`);
  console.log(`  discovered ${routes.length} routes: ${routes.join('  ')}\n`);

  let backendUp = false;
  try {
    const r = await fetch(`${BACKEND_URL}/api/health`, { signal: AbortSignal.timeout(1500) });
    backendUp = r.ok;
  } catch {
    /* not running */
  }

  if (!backendUp) {
    const py = venvPython();
    if (py) {
      console.log(`  ${C.d}starting backend: ${py} -m uvicorn app.main:app${C.x}`);
      launch('backend', py, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], join(ROOT, 'backend'));
      backendUp = await waitFor(`${BACKEND_URL}/api/health`, 90000, 'backend');
    } else {
      console.log(`  ${C.y}! no backend/.venv python found - testing frontend only${C.x}`);
    }
  } else {
    console.log(`  ${C.d}backend already running on ${BACKEND_URL}${C.x}`);
  }

  let frontendUp = false;
  try {
    const r = await fetch(FRONTEND_URL, { signal: AbortSignal.timeout(1500) });
    frontendUp = r.ok;
  } catch {
    /* not running */
  }
  if (!frontendUp) {
    console.log(`  ${C.d}starting vite dev server on ${FRONTEND_URL}${C.x}`);
    launch('vite', IS_WIN ? 'npm.cmd' : 'npm', ['run', 'dev:react'], ROOT);
    frontendUp = await waitFor(FRONTEND_URL, 120000, 'vite');
  } else {
    console.log(`  ${C.d}frontend already running on ${FRONTEND_URL}${C.x}`);
  }

  if (!frontendUp) {
    console.log(`${C.r}  frontend never came up - aborting${C.x}\n`);
    shutdown();
    process.exit(1);
  }

  rmSync(ARTIFACTS, { recursive: true, force: true });
  mkdirSync(ARTIFACTS, { recursive: true });

  let chromium;
  try {
    ({ chromium } = await import('playwright'));
  } catch {
    console.log(`${C.y}  Playwright is not installed - cannot run the browser smoke test.${C.x}`);
    console.log(`${C.d}  Enable it once with:  npm run smoke:setup${C.x}\n`);
    shutdown();
    process.exit(2);
  }
  const browser = await chromium.launch({ args: ['--no-sandbox', '--disable-gpu'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });

  const results = [];
  for (const route of routes) {
    const page = await context.newPage();
    const pageErrors = [];
    const consoleErrors = [];
    page.on('pageerror', (err) => pageErrors.push(String(err.message || err)));
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const t = msg.text();
        // network noise from intentionally-offline third-party services is not an app bug
        if (/favicon|ERR_CONNECTION_REFUSED|Failed to load resource/i.test(t)) return;
        consoleErrors.push(t);
      }
    });

    const url = `${FRONTEND_URL}/#${route}`;
    let status = 'ok';
    const problems = [];
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForTimeout(1600);

      const body = await page.evaluate(() => document.body.innerText || '');
      const html = await page.evaluate(() => document.getElementById('root')?.innerHTML?.length || 0);

      if (body.includes('JARVIS NEURAL CORE DIAGNOSTIC EXCEPTION') || body.includes('NEURAL CORE DIAGNOSTIC')) {
        status = 'crash';
        const line = body.split('\n').map((s) => s.trim()).filter(Boolean);
        const msg = line.find((l) => /Error|error:/.test(l)) || 'ErrorBoundary caught an exception';
        problems.push(`ErrorBoundary: ${msg}`);
      }
      if (pageErrors.length) {
        status = 'crash';
        problems.push(...pageErrors.map((e) => `uncaught: ${e}`));
      }
      if (consoleErrors.length) {
        if (status === 'ok') status = 'warn';
        problems.push(...consoleErrors.map((e) => `console.error: ${e.slice(0, 200)}`));
      }
      if (html < 200) {
        status = 'crash';
        problems.push(`route rendered (almost) nothing - root innerHTML length = ${html}`);
      }
    } catch (err) {
      status = 'crash';
      problems.push(`navigation/timings: ${String(err.message || err)}`);
    }

    await page.screenshot({ path: join(ARTIFACTS, `${route.replace(/\W+/g, '_') || 'home'}.png`) }).catch(() => {});
    await page.close();
    results.push({ route, status, problems });
  }

  await browser.close();

  /* ------------------------------- report -------------------------------- */
  console.log(`${'='.repeat(74)}`);
  let bad = 0;
  for (const r of results) {
    const label = r.route.padEnd(18);
    if (r.status === 'ok') {
      console.log(`  ${C.g}PASS${C.x}  ${label}`);
    } else if (r.status === 'warn') {
      console.log(`  ${C.y}WARN${C.x}  ${label}`);
      r.problems.forEach((p) => console.log(`          ${C.d}${p}${C.x}`));
    } else {
      bad += 1;
      console.log(`  ${C.r}FAIL${C.x}  ${label}`);
      r.problems.forEach((p) => console.log(`          ${C.r}${p}${C.x}`));
    }
  }
  console.log(`${'='.repeat(74)}`);
  console.log(`  ${bad ? C.r + bad + ' ROUTE(S) CRASHED' + C.x : C.g + 'ALL ' + results.length + ' ROUTES RENDERED CLEAN' + C.x}`);
  console.log(`${'='.repeat(74)}`);
  console.log(`  ${C.d}screenshots written to artifacts/smoke/${C.x}\n`);

  writeFileSync(join(ARTIFACTS, 'report.json'), JSON.stringify(results, null, 2));
  shutdown();
  process.exit(bad ? 1 : 0);
}

main().catch((err) => {
  console.error(err);
  shutdown();
  process.exit(1);
});
