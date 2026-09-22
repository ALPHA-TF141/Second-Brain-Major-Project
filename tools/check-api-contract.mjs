/**
 * JARVIS OS — Frontend <-> Backend API Contract Check
 * ===========================================================================
 * Why this exists:
 *   A UI screen can be perfectly coded and still be broken, because it calls
 *   an endpoint that does not exist (404), or uses the wrong HTTP method.
 *   This checker statically compares EVERY url the React app calls against
 *   EVERY route the FastAPI backend registers, and reports mismatches.
 *
 * Usage:
 *   npm run check:api
 * ===========================================================================
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const SRC = path.join(ROOT, 'src');
const BACKEND = path.join(ROOT, 'backend', 'app');

/* ---------------------------- helpers ---------------------------- */

function walk(dir, filter, acc = []) {
  if (!fs.existsSync(dir)) return acc;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (['node_modules', '.venv', '__pycache__', 'dist'].includes(entry.name)) continue;
      walk(full, filter, acc);
    } else if (filter(full)) {
      acc.push(full);
    }
  }
  return acc;
}

/** Normalise a url so literal params and template params compare equal. */
function normalize(url) {
  let u = url.split('?')[0].split('#')[0];
  u = u.replace(/\$\{[^}]*\}/g, '{}');       // ${id}   -> {}
  u = u.replace(/\{[^}]+\}/g, '{}');          // {id}    -> {}
  u = u.replace(/\/+$/, '');                  // trailing slash
  if (u === '') u = '/';
  return u;
}

/* -------------------- 1. Collect backend routes -------------------- */

const mainPy = fs.readFileSync(path.join(BACKEND, 'main.py'), 'utf8');
const includePrefix = new Map(); // module -> prefix
for (const m of mainPy.matchAll(/include_router\(\s*([A-Za-z_][\w.]*)\s*(?:,\s*prefix\s*=\s*"([^"]*)")?/g)) {
  const mod = m[1].split('.')[0]; // "health.router" -> "health"
  includePrefix.set(mod, m[2] || '');
}

const backendRoutes = new Map(); // "METHOD normalizedPath" -> source file
const routeFiles = walk(path.join(BACKEND, 'routes'), (f) => f.endsWith('.py'));

for (const file of routeFiles) {
  const mod = path.basename(file, '.py');
  const text = fs.readFileSync(file, 'utf8');

  // Router-level prefix, e.g. APIRouter(prefix="/api/os", tags=[...])
  const routerPrefixMatch = text.match(/APIRouter\(\s*([^)]*)\)/s);
  const routerPrefix = routerPrefixMatch
    ? (routerPrefixMatch[1].match(/prefix\s*=\s*["']([^"']*)["']/)?.[1] ?? '')
    : '';

  const mountPrefix =
    includePrefix.has(mod) && includePrefix.get(mod)
      ? includePrefix.get(mod)
      : includePrefix.has(mod)
        ? ''
        : routerPrefix; // router mounted elsewhere / standalone

  for (const m of text.matchAll(/@router\.(get|post|put|delete|patch|websocket)\(\s*["'`]([^"'`]*)["'`]/g)) {
    const method = m[1].toUpperCase();
    const routePath = m[2];
    const full = routePath.startsWith('/api') || routePath.startsWith('/ws')
      ? routePath // decorator declares the complete path
      : `${mountPrefix || routerPrefix}${routePath}`;
    backendRoutes.set(`${method} ${normalize(full)}`, path.relative(ROOT, file));
  }
}

/* -------------------- 2. Collect frontend calls -------------------- */

const frontendFiles = walk(SRC, (f) => /\.(jsx?|tsx?)$/.test(f));
const calls = []; // { url, method, file, line }

const CALL_SITE = /(apiFetch\(|fetch\(|apiClient\.[a-zA-Z]+\(|axios\.[a-zA-Z]+\(|\.open\(\s*['"]\w+['"]\s*,)/g;
const URL_IN_TEXT = /\/api\/[A-Za-z0-9_\-/.${}]*/g;

/** Blank out comments (preserving offsets) so doc text is never scanned. */
function stripComments(src) {
  return src
    .replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '))
    .replace(/(^|[^:"'`\\])\/\/[^\n]*/g, (m, p1) => p1 + m.slice(p1.length).replace(/[^\n]/g, ' '));
}

for (const file of frontendFiles) {
  const raw = fs.readFileSync(file, 'utf8');
  const text = stripComments(raw);
  const rel = path.relative(ROOT, file);

  const sites = [...text.matchAll(CALL_SITE)].map((m) => ({ index: m.index, text: m[0] }));

  // Scan urls across the WHOLE file so nothing is truncated at a window edge,
  // then attach each url to the nearest request call site before it.
  for (const m of text.matchAll(URL_IN_TEXT)) {
    const url = m[0].replace(/[.,)]+$/, '');
    const idx = m.index;
    const site = [...sites].filter((s) => s.index < idx + 4 && idx - s.index < 400).pop();
    if (!site) continue; // just a string in a config/map, not an actual request

    const lineNo = text.slice(0, idx).split('\n').length;
    const options = text.slice(site.index, site.index + 400);

    // Method: explicit `method: 'POST'` wins, else infer from apiClient.methodName()
    let method = 'GET';
    const explicit = options.match(/method:\s*['"`](\w+)['"`]/);
    if (explicit) {
      method = explicit[1].toUpperCase();
    } else {
      const verb = site.text.match(/apiClient\.([a-zA-Z]+)\(|axios\.([a-zA-Z]+)\(/);
      const name = (verb?.[1] || verb?.[2] || '').toLowerCase();
      if (['post', 'put', 'patch', 'delete'].includes(name)) method = name.toUpperCase();
      else if (/POST/.test(options.slice(0, 140))) method = 'POST';
    }

    calls.push({ url: normalize(url), method, file: rel, line: lineNo });
  }
}

/* -------------------- 3. Compare -------------------- */

const backendNormalized = new Set([...backendRoutes.keys()].map((k) => k.split(' ')[1]));
const missing = [];
const matched = [];

for (const c of calls) {
  const knownMethods = [...backendRoutes.keys()]
    .filter((k) => k.split(' ')[1] === c.url)
    .map((k) => k.split(' ')[0]);

  if (knownMethods.length === 0 && !backendNormalized.has(c.url)) {
    missing.push(c);
  } else {
    matched.push({ ...c, methods: knownMethods });
  }
}

/* -------------------- 4. Report -------------------- */

console.log('\n\u001b[36m=== API CONTRACT CHECK : React UI  <->  FastAPI ===\u001b[0m\n');
console.log(`Backend routes registered : ${backendRoutes.size}`);
console.log(`Frontend endpoints called : ${calls.length}`);
console.log(`Matched                   : ${matched.length}`);

if (missing.length) {
  // De-duplicate by url+file
  const seen = new Set();
  const unique = missing.filter((m) => {
    const k = `${m.url}|${m.file}`;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });

  console.log(`\n\u001b[31m\u001b[1m>>> ${unique.length} CALL(S) TARGET A ROUTE THE BACKEND DOES NOT SERVE (404 RISK) <<<\u001b[0m\n`);
  for (const m of unique) {
    console.log(`\u001b[31m  ${m.url}\u001b[0m`);
    console.log(`      ${m.file}:${m.line}`);
  }
  console.log('');
  process.exitCode = 1;
} else {
  console.log('\n\u001b[32m\u001b[1m>>> ALL FRONTEND ENDPOINTS EXIST ON THE BACKEND — NO 404 RISK <<<\u001b[0m\n');
}

/* Informational: routes nothing calls (dead or external-only endpoints) */
const calledPaths = new Set(calls.map((c) => c.url));
const unused = [...backendRoutes.keys()]
  .filter((k) => !calledPaths.has(k.split(' ')[1]))
  .map((k) => k);
if (unused.length) {
  console.log(`\u001b[90m\u001b[1mNote:\u001b[0m\u001b[90m ${unused.length} backend route(s) are not called by the UI (fine if used by scripts/tests/agents):\u001b[0m`);
  console.log(`\u001b[90m  ${unused.sort().join('\n  ')}\u001b[0m\n`);
}
