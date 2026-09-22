/**
 * JARVIS OS — Route Render Smoke Test
 * ===========================================================================
 * Why this exists:
 *   `npm run build` only checks that the code COMPILES. It does NOT catch
 *   runtime crashes like:
 *       ReferenceError: Activity is not defined   (missing lucide-react import)
 *       TypeError: Cannot read properties of null
 *   Those only appear when React actually renders the page — which is exactly
 *   how the "JARVIS NEURAL CORE DIAGNOSTIC EXCEPTION" red screen happened.
 *
 * What this does:
 *   Spins up a real Vite SSR pipeline, loads the app's own modules
 *   (contexts + App), and renders EVERY route in the navigation through
 *   React on the server. Any page that throws is reported with its stack.
 *
 * Usage:
 *   npm run smoke
 * ===========================================================================
 */
import { createServer } from 'vite';
import { createRequire } from 'node:module';
import { JSDOM } from 'jsdom';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

/* ------------------------------------------------------------------ *
 * 1. Minimal browser environment (jsdom) for module-scope DOM access
 * ------------------------------------------------------------------ */
const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', {
  url: 'http://127.0.0.1:5173/',
  pretendToBeVisual: true
});

/**
 * Install a global safely.
 *
 * Node 21+ ships some globals as GETTER-ONLY accessors - `navigator` and
 * `crypto` in particular - so a plain `globalThis.navigator = x` throws
 * "Cannot set property navigator of #<Object> which has only a getter".
 * That is exactly what broke this script on Node 24 while it worked on Node 20.
 * They are still `configurable`, so defineProperty succeeds; we fall back to
 * plain assignment for runtimes where that is the only option.
 */
function setGlobal(name, value) {
  try {
    Object.defineProperty(globalThis, name, {
      value,
      writable: true,
      configurable: true,
      enumerable: false
    });
    return true;
  } catch {
    /* not configurable on this runtime - try assignment */
  }
  try {
    globalThis[name] = value;
    return true;
  } catch {
    return false;
  }
}

setGlobal('window', dom.window);
setGlobal('document', dom.window.document);
setGlobal('navigator', dom.window.navigator);
setGlobal('location', dom.window.location);
setGlobal('localStorage', dom.window.localStorage);
setGlobal('sessionStorage', dom.window.sessionStorage);
setGlobal('HTMLElement', dom.window.HTMLElement);
setGlobal('Element', dom.window.Element);
setGlobal('Node', dom.window.Node);
setGlobal('getComputedStyle', dom.window.getComputedStyle.bind(dom.window));
setGlobal('requestAnimationFrame', (cb) => setTimeout(() => cb(Date.now()), 0));
setGlobal('cancelAnimationFrame', (id) => clearTimeout(id));

if (typeof globalThis.navigator === 'undefined' || typeof globalThis.document === 'undefined') {
  console.error('\u001b[31mCould not install the browser environment globals on Node '
    + process.version + ' - cannot run the route smoke test.\u001b[0m');
  process.exit(2);
}

// APIs Electron/Chromium may expose that jsdom does not
dom.window.matchMedia = dom.window.matchMedia || (() => ({
  matches: false,
  media: '',
  addListener() {},
  removeListener() {},
  addEventListener() {},
  removeEventListener() {},
  dispatchEvent() { return false; }
}));
setGlobal('matchMedia', dom.window.matchMedia);
setGlobal('ResizeObserver', class { observe() {} unobserve() {} disconnect() {} });
setGlobal('IntersectionObserver', class { observe() {} unobserve() {} disconnect() {} });
setGlobal('SpeechSynthesisUtterance', class { constructor(t) { this.text = t; } });
dom.window.speechSynthesis = { speak() {}, cancel() {}, getVoices: () => [] };
setGlobal('WebSocket', class { constructor() {} close() {} send() {} addEventListener() {} });
setGlobal('AudioContext', class { constructor() { this.state = 'running'; this.destination = {}; } createOscillator() { return { connect() {}, start() {}, stop() {}, frequency: {}, type: '' }; } createGain() { return { connect() {}, gain: { value: 0, setValueAtTime() {}, exponentialRampToValueAtTime() {} } }; } close() {} });

// Offline-safe fetch stub: never touches the network, always answers.
// Real data is irrelevant here — we only care that rendering does not crash.
// Switched to 'connected' for Phase 3 so the Google pages render with real data.
let stubMode = 'disconnected';

const CONNECTED_PAYLOADS = {
  '/api/google/status': {
    configured: true,
    redirect_uri: 'http://127.0.0.1:8000/api/google/callback',
    account_count: 2,
    accounts: [
      { id: 'gacct_1', email: 'immanuellourdu@gmail.com', name: 'Immanuel', picture: '', services: ['gmail', 'calendar'], scopes: ['https://www.googleapis.com/auth/gmail.readonly'], status: 'connected' },
      { id: 'gacct_2', email: 'vtu24334@veltech.edu.in', name: 'Immanuel L', picture: '', services: ['gmail'], scopes: [], status: 'connected' }
    ]
  },
  '/api/mail/accounts': [
    { id: 'imap_abc123', email: 'immanuellourdu@gmail.com', name: 'Personal', provider: 'imap',
      provider_label: 'IMAP + App Password', services: ['gmail'], scopes: [], status: 'connected',
      stats: { total_messages: 4210, unread: 37, checked_at: '2026-09-22T10:00:00Z' } },
    { id: 'gacct_1', email: 'vtu24334@veltech.edu.in', name: 'College', provider: 'google',
      provider_label: 'Google OAuth', services: ['gmail', 'calendar'], scopes: [], status: 'connected' }
  ],
  '/api/os/notifications': [
    { id: 'ntf_1', title: 'Deadline: IEEE conference draft deadline', body: 'From sharma@university.edu (college) - due 2026-09-25', kind: 'email_action', priority: 'high', source: 'mail', read: false, timestamp: '2026-09-22T10:00:00Z' },
    { id: 'ntf_2', title: 'Important email: Project review notes', body: 'From sharma@university.edu', kind: 'email_important', priority: 'high', source: 'mail', read: true, timestamp: '2026-09-22T09:00:00Z' }
  ],
  '/api/calendar/sources': [
    { id: 'ics_xyz789', email: 'College', name: 'College Calendar', provider: 'ical',
      provider_label: 'iCal secret address', kind: 'snapshot', status: 'connected',
      stats: { parsed_events: 214, in_window: 6 } },
    { id: 'gacct_1', email: 'vtu24334@veltech.edu.in', name: 'College', provider: 'google',
      provider_label: 'Google OAuth', kind: 'live', status: 'connected' }
  ],
  '/api/calendar/source-events': {
    count: 2,
    events: [
      { id: 'e1', summary: 'AI Project Review', start: '2026-09-23T10:00:00+05:30',
        end: '2026-09-23T11:00:00+05:30', all_day: false, location: 'Lab 3',
        attendees: ['a@b.c'], html_link: '' },
      { id: 'e2', summary: 'Holiday', start: '2026-09-25', end: '2026-09-26',
        all_day: true, attendees: [] }
    ]
  },
  '/api/google/accounts': [
    { id: 'gacct_1', email: 'immanuellourdu@gmail.com', name: 'Immanuel', services: ['gmail', 'calendar'], scopes: [], status: 'connected' }
  ],
  '/api/google/gmail/messages': {
    count: 2,
    messages: [
      { id: 'm1', thread_id: 't1', from: 'Prof. Sharma <sharma@university.edu>', to: 'vtu24334@veltech.edu.in', subject: 'IEEE draft deadline', snippet: 'Please submit before Friday 5 PM.', date: 'Tue, 22 Sep 2026 09:00:00 +0530', unread: true, important: true, labels: ['INBOX'] },
      { id: 'm2', thread_id: 't2', from: 'AWS <no-reply@aws.amazon.com>', subject: 'Your AWS invoice', snippet: 'Invoice ready.', date: 'Tue, 22 Sep 2026 10:00:00 +0530', unread: false, important: false, labels: ['INBOX'] }
    ]
  },
  '/api/google/calendar/events': {
    count: 2,
    events: [
      { id: 'e1', summary: 'AI Project Review', start: '2026-09-23T10:00:00+05:30', end: '2026-09-23T11:00:00+05:30', all_day: false, location: 'Lab 3', attendees: ['a@b.c'], html_link: 'https://calendar.google.com/event?eid=e1' },
      { id: 'e2', summary: 'Holiday', start: '2026-09-25', end: '2026-09-26', all_day: true, attendees: [] }
    ]
  }
};

const offlineFetch = async (url) => {
  const payloads = {
    '/api/os/intelligence': { while_you_were_away: {}, attention_items: [] },
    '/api/graph/briefing/today': { spoken_script: 'Smoke test briefing.' },
    '/api/os/tasks': [],
    '/api/os/reminders': [],
    '/api/os/calendar': [],
    '/api/os/projects': [],
    '/api/os/automations': [],
    '/api/os/activity': [],
    '/api/os/integrations': [],
    '/api/os/search': { results: [] },
    '/api/google/status': { configured: false, accounts: [], account_count: 0, setup_help: '' },
    '/api/mail/accounts': [],
    '/api/calendar/sources': [],
    '/api/os/notifications': [],
    '/api/research/overview': { memories_total: 0, scored: 0, temporal_facts: 0, open_facts: 0, superseded_facts: 0, conflicts: 0, consolidations: 0, gaps: 0, forgotten: 0 },
    '/api/research/scores': [],
    '/api/research/temporal': { current: [], history: [] },
    '/api/research/conflicts': { total: 0, by_type: {}, unresolved: 0, conflicts: [] },
    '/api/research/gaps': { gaps: 0, concepts_examined: 0, items: [] },
    '/api/research/forgotten': { forgotten_count: 0, total_memories: 0, entries: [] },
    '/api/research/runs': [],
    '/api/proactive/status': {
      wake_word: { enabled: true, running: false, available: false, missing_packages: ['openwakeword'], model: 'hey_jarvis', threshold: 0.5, detections: 0, last_error: '', detail: 'dependencies missing', install_hint: 'pip install openwakeword sounddevice', recent_scores: [] },
      voice: { enabled: true, min_priority: 'high', quiet_hours: '23:00-07:00', in_quiet_hours: false, spoken_count: 0, skipped_count: 0, last_spoken: null, broadcaster_ready: true }
    },
    '/api/mail/sync/status': { enabled: false, interval_minutes: 10, folders: ['inbox'], limit_per_run: 25, skip_bulk: true, is_syncing: false, stats: {} },
    '/api/google/accounts': [],
    '/api/google/gmail/messages': { messages: [], count: 0 },
    '/api/google/calendar/events': { events: [], count: 0 },
    '/api/graph/data': { nodes: [], edges: [] },
    '/api/graph/knowledge': { nodes: [], edges: [] }
  };
  const source = stubMode === 'connected' ? { ...payloads, ...CONNECTED_PAYLOADS } : payloads;
  const key = Object.keys(source).find((k) => String(url).includes(k));
  const body = key ? source[key] : {};
  return {
    ok: true,
    status: 200,
    statusText: 'OK',
    json: async () => body,
    text: async () => JSON.stringify(body),
    headers: new Map(),
    clone() { return this; }
  };
};
setGlobal('fetch', offlineFetch);
dom.window.fetch = offlineFetch;

/* ------------------------------------------------------------------ *
 * 2. Capture React's own console errors/warnings during render
 * ------------------------------------------------------------------ */
const reactIssues = [];
const realError = console.error;
const realWarn = console.warn;
// jsdom reports unimplemented browser features (canvas 2D, layout engine) through
// its virtual console. Those are LIMITATIONS OF THE TEST ENVIRONMENT, not app
// bugs — the components guard against a null 2D context. Filter them out so a
// green run means "the app is fine", not "the harness ran out of features".
const ENV_NOISE = [
  'useLayoutEffect does nothing on the server',
  'Not implemented: HTMLCanvasElement',
  'Not implemented: window.scrollTo',
  'Not implemented: navigation'
];

console.error = (...args) => {
  const text = args.map(String).join(' ');
  if (!ENV_NOISE.some((noise) => text.includes(noise))) {
    reactIssues.push({ level: 'error', text: text.slice(0, 400) });
  }
};
console.warn = (...args) => {
  const text = args.map(String).join(' ');
  if (/Warning|Invalid|NaN|undefined/.test(text)) {
    reactIssues.push({ level: 'warn', text: text.slice(0, 400) });
  }
};

/* ------------------------------------------------------------------ *
 * 3. Every route in the navigation
 * ------------------------------------------------------------------ */
const ROUTES = [
  ['/', 'Home — Jarvis Command Center'],
  ['/agent', 'AI Agent Workspace'],
  ['/chat', 'AI Agent (legacy alias)'],
  ['/gmail', 'Gmail Workspace'],
  ['/calendar', 'Calendar Workspace'],
  ['/tasks', 'Tasks'],
  ['/notifications', 'Notifications'],
  ['/reminders', 'Reminders'],
  ['/knowledge', 'Knowledge Base & Wiki'],
  ['/knowledge-graph', 'Interactive Knowledge Graph'],
  ['/files', 'Files & Artifacts'],
  ['/projects', 'Projects'],
  ['/automations', 'Automations'],
  ['/activity', 'Agent Activity Audit Log'],
  ['/integrations', 'Integrations Manager'],
  ['/memory-lab', 'Memory Lab (research layer)'],
  ['/voice', 'Voice Companion'],
  ['/settings', 'Settings'],
  ['/jarvis-orb', 'Floating Holographic Orb']
];

async function main() {
  console.log('\n\u001b[36m=== JARVIS OS : ROUTE RENDER SMOKE TEST ===\u001b[0m\n');

  const vite = await createServer({
    root: ROOT,
    server: { middlewareMode: true },
    appType: 'custom',
    logLevel: 'error',
    optimizeDeps: { noDiscovery: true }
  });

  try {
    const React = require('react');
    const { renderToString } = require('react-dom/server');
    const { MemoryRouter } = require('react-router-dom');

    const { BackendProvider } = await vite.ssrLoadModule('/src/context/BackendContext.jsx');
    const { AssistantProvider } = await vite.ssrLoadModule('/src/context/AssistantContext.jsx');
    const App = (await vite.ssrLoadModule('/src/App.jsx')).default;

    let passed = 0;
    const failures = [];

    for (const [route, label] of ROUTES) {
      reactIssues.length = 0;
      const started = Date.now();
      try {
        const html = renderToString(
          React.createElement(
            MemoryRouter,
            { initialEntries: [route] },
            React.createElement(
              BackendProvider,
              null,
              React.createElement(AssistantProvider, null, React.createElement(App, null))
            )
          )
        );

        const ms = Date.now() - started;
        const hardIssues = reactIssues.filter((i) => i.level === 'error');

        if (!html || html.length < 40) {
          throw new Error(`Rendered empty output (${html.length} chars)`);
        }
        if (hardIssues.length) {
          failures.push({ route, label, error: `React error(s):\n    - ${hardIssues.map((i) => i.text.replace(/\s+/g, ' ')).join('\n    - ')}` });
          console.log(`\u001b[33m  WARN\u001b[0m  ${route.padEnd(18)} ${label}  (${ms}ms)`);
        } else {
          passed += 1;
          console.log(`\u001b[32m  PASS\u001b[0m  ${route.padEnd(18)} ${label}  (${ms}ms, ${html.length} bytes HTML)`);
        }
      } catch (err) {
        const stackLines = String(err.stack || '').split('\n').slice(0, 6).join('\n      ');
        failures.push({ route, label, error: `${err.name}: ${err.message}\n      ${stackLines}` });
        console.log(`\u001b[31m  FAIL\u001b[0m  ${route.padEnd(18)} ${label}`);
      }
    }

    /* ---------------------------------------------------------------- *
     * PHASE 2 — Live mount: actually run effects, timers and fetch
     * callbacks inside jsdom. This is where most real crashes live
     * (e.g. reading .map() off an API field that came back undefined).
     * ---------------------------------------------------------------- */
    console.log('\n\u001b[36m--- PHASE 2: LIVE MOUNT + EFFECTS (jsdom) ---\u001b[0m\n');

    const { createRoot } = require('react-dom/client');
    const mountFailures = [];
    let mountPassed = 0;

    const onUncaught = (err) => {
      reactIssues.push({
        level: 'error',
        text: `${err?.name || 'Error'}: ${err?.message || String(err)}`
      });
    };
    process.on('uncaughtException', onUncaught);
    process.on('unhandledRejection', onUncaught);

    for (const [route, label] of ROUTES) {
      reactIssues.length = 0;
      const container = dom.window.document.createElement('div');
      dom.window.document.body.appendChild(container);

      let root = null;
      try {
        root = createRoot(container);
        root.render(
          React.createElement(
            MemoryRouter,
            { initialEntries: [route] },
            React.createElement(
              BackendProvider,
              null,
              React.createElement(AssistantProvider, null, React.createElement(App, null))
            )
          )
        );

        // Give effects, timers and the stubbed fetch promises time to settle
        await new Promise((r) => setTimeout(r, 350));

        const hardIssues = reactIssues.filter((i) => i.level === 'error');
        if (hardIssues.length) {
          mountFailures.push({
            route,
            label,
            error: `Runtime error(s) after mount:\n    - ${hardIssues.map((i) => i.text.replace(/\s+/g, ' ')).join('\n    - ')}`
          });
          console.log(`\u001b[33m  WARN\u001b[0m  ${route.padEnd(18)} ${label}`);
        } else {
          mountPassed += 1;
          console.log(`\u001b[32m  PASS\u001b[0m  ${route.padEnd(18)} ${label}  (${container.innerHTML.length} bytes live DOM)`);
        }
      } catch (err) {
        mountFailures.push({
          route,
          label,
          error: `${err.name}: ${err.message}\n      ${String(err.stack || '').split('\n').slice(1, 6).join('\n      ')}`
        });
        console.log(`\u001b[31m  FAIL\u001b[0m  ${route.padEnd(18)} ${label}`);
      } finally {
        try { root?.unmount(); } catch { /* ignore */ }
        container.remove();
      }
    }

    process.removeListener('uncaughtException', onUncaught);
    process.removeListener('unhandledRejection', onUncaught);

    console.log('');
    if (mountFailures.length) {
      console.log(`\u001b[31m=== ${mountFailures.length} ROUTE(S) THREW DURING LIVE MOUNT ===\u001b[0m`);
      for (const f of mountFailures) {
        console.log(`\n\u001b[31m▸ ${f.route}  (${f.label})\u001b[0m\n    ${f.error}`);
      }
      failures.push(...mountFailures);
    } else {
      console.log(`\u001b[32m=== ALL ${mountPassed}/${ROUTES.length} ROUTES MOUNTED AND RAN EFFECTS CLEANLY ===\u001b[0m`);
    }

    /* ---------------------------------------------------------------- *
     * PHASE 3 - the Google pages WITH connected accounts.
     * Phase 2 only proves the "Not Connected" state renders. This proves the
     * connected state (account switcher, message list, event agenda) does too.
     * ---------------------------------------------------------------- */
    console.log('\n\u001b[36m--- PHASE 3: GOOGLE PAGES WITH CONNECTED ACCOUNTS ---\u001b[0m\n');
    stubMode = 'connected';

    const GOOGLE_ROUTES = [
      ['/gmail', 'Gmail (connected)'],
      ['/calendar', 'Calendar (connected)'],
      ['/integrations', 'Integrations (connected)']
    ];
    let connectedPassed = 0;
    const connectedFailures = [];

    for (const [route, label] of GOOGLE_ROUTES) {
      reactIssues.length = 0;
      const container = dom.window.document.createElement('div');
      dom.window.document.body.appendChild(container);
      let root = null;
      try {
        root = createRoot(container);
        root.render(
          React.createElement(
            MemoryRouter,
            { initialEntries: [route] },
            React.createElement(BackendProvider, null,
              React.createElement(AssistantProvider, null, React.createElement(App, null)))
          )
        );
        await new Promise((r) => setTimeout(r, 400));

        const hard = reactIssues.filter((i) => i.level === 'error');
        const html = container.innerHTML;

        if (hard.length) {
          connectedFailures.push({ route, label, error: hard.map((i) => i.text.replace(/\s+/g, ' ')).join(' | ') });
          console.log(`\u001b[33m  WARN\u001b[0m  ${route.padEnd(18)} ${label}`);
        } else if (route !== '/integrations' && !html.includes('@')) {
          // A connected page must show the account address, not an empty shell
          connectedFailures.push({ route, label, error: 'page rendered but shows no account/email content' });
          console.log(`\u001b[33m  WARN\u001b[0m  ${route.padEnd(18)} ${label}  (no account content found)`);
        } else {
          connectedPassed += 1;
          console.log(`\u001b[32m  PASS\u001b[0m  ${route.padEnd(18)} ${label}  (${html.length} bytes live DOM)`);
        }
      } catch (err) {
        connectedFailures.push({ route, label, error: `${err.name}: ${err.message}` });
        console.log(`\u001b[31m  FAIL\u001b[0m  ${route.padEnd(18)} ${label}`);
      } finally {
        try { root?.unmount(); } catch { /* ignore */ }
        container.remove();
      }
    }

    stubMode = 'disconnected';
    console.log('');
    if (connectedFailures.length) {
      console.log(`\u001b[31m=== ${connectedFailures.length} CONNECTED-STATE ROUTE(S) PROBLEM ===\u001b[0m`);
      for (const f of connectedFailures) {
        console.log(`\n\u001b[31m\u25b8 ${f.route}  (${f.label})\u001b[0m\n    ${f.error}`);
      }
      failures.push(...connectedFailures);
    } else {
      console.log(`\u001b[32m=== ALL ${connectedPassed}/${GOOGLE_ROUTES.length} GOOGLE PAGES RENDER CORRECTLY WITH ACCOUNTS CONNECTED ===\u001b[0m`);
    }

    console.log('');
    if (failures.length) {
      console.log(`\u001b[31m=== ${failures.length} ROUTE(S) CRASHED — THESE WOULD SHOW THE RED JARVIS DIAGNOSTIC SCREEN ===\u001b[0m`);
      for (const f of failures) {
        console.log(`\n\u001b[31m▸ ${f.route}  (${f.label})\u001b[0m\n    ${f.error}`);
      }
      console.error = realError;
      console.warn = realWarn;
      await vite.close();
      process.exit(1);
    }

    console.log(`\u001b[32m=== ALL ${passed}/${ROUTES.length} ROUTES RENDERED SUCCESSFULLY — NO RUNTIME CRASHES ===\u001b[0m\n`);
  } finally {
    console.error = realError;
    console.warn = realWarn;
    await vite.close().catch(() => {});
  }
}

main().catch((err) => {
  console.error('\u001b[31mSmoke test harness failed to boot:\u001b[0m', err);
  process.exit(1);
});
