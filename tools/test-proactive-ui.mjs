/**
 * Hands-free UI wiring test.
 * ===========================================================================
 * The backend decides WHEN to wake and WHAT to say; the renderer only has to
 * react. This asserts that reaction, because a broadcast nobody handles looks
 * exactly like a feature that does not exist.

 *   1. a `wake` event asks Electron to REVEAL the orb
 *   2. revealOrb is used, not the toggling showOrb (which would HIDE an orb
 *      that was already on screen - the opposite of the intent)
 *   3. a `speak` event is actually spoken
 *   4. the same event delivered twice is spoken once
 *   5. unrelated live events are ignored
 *
 * Usage:  node tools/test-proactive-ui.mjs
 */
import { createServer } from 'vite';
import { createRequire } from 'node:module';
import { JSDOM } from 'jsdom';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

const failures = [];
function check(label, condition, detail = '') {
  if (condition) console.log(`\u001b[32m  PASS\u001b[0m  ${label}`);
  else { failures.push(label); console.log(`\u001b[31m  FAIL\u001b[0m  ${label}   ${detail}`); }
}

/* --------------------------------------------------------------- environment */
const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', {
  url: 'http://127.0.0.1:5173/', pretendToBeVisual: true
});
function setGlobal(name, value) {
  try { Object.defineProperty(globalThis, name, { value, writable: true, configurable: true }); }
  catch { globalThis[name] = value; }
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
setGlobal('ResizeObserver', class { observe() {} unobserve() {} disconnect() {} });
setGlobal('AudioContext', class {
  constructor() { this.state = 'running'; this.destination = {}; }
  createOscillator() { return { connect() {}, start() {}, stop() {}, frequency: {}, type: '' }; }
  createGain() { return { connect() {}, gain: { setValueAtTime() {}, exponentialRampToValueAtTime() {}, value: 0 } }; }
  close() {}
});
setGlobal('SpeechRecognition', undefined);
dom.window.SpeechRecognition = undefined;

/* ------------------------------------------------------------- speech spy */
const spoken = [];
class FakeUtterance { constructor(text) { this.text = text; } }
setGlobal('SpeechSynthesisUtterance', FakeUtterance);
dom.window.SpeechSynthesisUtterance = FakeUtterance;
dom.window.speechSynthesis = {
  getVoices: () => [],
  cancel: () => {},
  speak: (u) => spoken.push(u.text)
};

/* ------------------------------------------------------------- electron spy */
const calls = { revealOrb: 0, showOrb: 0, hideOrb: 0 };
dom.window.secondBrain = {
  revealOrb: () => { calls.revealOrb += 1; },
  showOrb: () => { calls.showOrb += 1; },
  hideOrb: () => { calls.hideOrb += 1; },
  showMain: () => {},
  getAppInfo: async () => ({}),
  onCaptureCommand: () => () => {},
  onSpotlightToggle: () => () => {},
  onWakeTrigger: () => () => {}
};
setGlobal('secondBrain', dom.window.secondBrain);

/* -------------------------------------------------------------- live socket */
const sockets = [];
class FakeWebSocket {
  constructor(url) { this.url = url; sockets.push(this); setTimeout(() => this.onopen?.(), 0); }
  send() {}
  close() {}
  deliver(payload) { this.onmessage?.({ data: JSON.stringify(payload) }); }
}
setGlobal('WebSocket', FakeWebSocket);
dom.window.WebSocket = FakeWebSocket;

/* -------------------------------------------------------------------- fetch */
const offlineFetch = async (url) => {
  const body = String(url).includes('/api/auth/login')
    ? { access_token: 'fake-token', username: 'Immanuel' }
    : Array.isArray(undefined) ? [] : {};
  return { ok: true, status: 200, json: async () => body, text: async () => JSON.stringify(body) };
};
setGlobal('fetch', offlineFetch);
dom.window.fetch = offlineFetch;

/* ---------------------------------------------------------------------- run */
async function main() {
  console.log('\n\u001b[36m=== HANDS-FREE UI WIRING TEST ===\u001b[0m\n');

  const vite = await createServer({
    root: ROOT, server: { middlewareMode: true }, appType: 'custom',
    logLevel: 'error', optimizeDeps: { noDiscovery: true }
  });

  try {
    const React = require('react');
    const { createRoot } = require('react-dom/client');
    const { MemoryRouter } = require('react-router-dom');

    const { BackendProvider } = await vite.ssrLoadModule('/src/context/BackendContext.jsx');
    const { AssistantProvider } = await vite.ssrLoadModule('/src/context/AssistantContext.jsx');
    const AppRoutes = (await vite.ssrLoadModule('/src/routes/AppRoutes.jsx')).default;

    const container = dom.window.document.createElement('div');
    dom.window.document.body.appendChild(container);
    const root = createRoot(container);

    root.render(
      React.createElement(MemoryRouter, { initialEntries: ['/'] },
        React.createElement(BackendProvider, null,
          React.createElement(AssistantProvider, null, React.createElement(AppRoutes, null))))
    );

    await new Promise((r) => setTimeout(r, 500));

    // deliver() is called on the socket bound to this window; backend broadcast
    // = same payload to every client, so use whichever socket is the live one.
    const live = sockets.find((s) => String(s.url).includes('/ws/live')) || sockets[0];
    check('a live socket was opened by the UI', !!live, `sockets: ${sockets.length}`);

    console.log('\n[1] A wake word reaches the orb');
    calls.revealOrb = 0; calls.showOrb = 0;
    live.deliver({ type: 'wake', source: 'wake_word', score: 0.96, timestamp: 'T1' });
    await new Promise((r) => setTimeout(r, 120));
    check('revealOrb was called', calls.revealOrb === 1, `revealOrb=${calls.revealOrb}`);
    check('the TOGGLING showOrb was NOT used (it would hide a visible orb)',
      calls.showOrb === 0, `showOrb=${calls.showOrb}`);

    console.log('\n[2] The same wake event twice is handled once');
    live.deliver({ type: 'wake', source: 'wake_word', score: 0.96, timestamp: 'T1' });
    await new Promise((r) => setTimeout(r, 120));
    check('a duplicate event does not re-fire', calls.revealOrb === 1, `revealOrb=${calls.revealOrb}`);

    console.log('\n[3] Jarvis speaks first');
    spoken.length = 0; calls.revealOrb = 0;
    live.deliver({
      type: 'speak',
      text: 'Sir, the IEEE conference draft deadline is due 2026-09-25.',
      priority: 'high', source: 'mail', show_orb: true, timestamp: 'S1'
    });
    await new Promise((r) => setTimeout(r, 120));
    check('the line was spoken aloud', spoken.length === 1, JSON.stringify(spoken));
    check('the spoken text is the backend text',
      spoken[0]?.includes('IEEE conference draft deadline'), spoken[0]);
    check('the orb was revealed for the announcement', calls.revealOrb === 1, `revealOrb=${calls.revealOrb}`);

    console.log('\n[4] The same sentence is not said twice');
    live.deliver({ type: 'speak', text: 'identical sentence', priority: 'high', timestamp: 'S2' });
    await new Promise((r) => setTimeout(r, 80));
    live.deliver({ type: 'speak', text: 'identical sentence', priority: 'high', timestamp: 'S2' });
    await new Promise((r) => setTimeout(r, 120));
    check('duplicate speak event spoken once',
      spoken.filter((t) => t === 'identical sentence').length === 1,
      JSON.stringify(spoken));

    console.log('\n[5] Unrelated live events are ignored');
    const before = { spoken: spoken.length, reveal: calls.revealOrb };
    live.deliver({ type: 'status', status: 'connected' });
    live.deliver({ type: 'echo', message: 'hello' });
    live.deliver({ type: 'mail_sync', account: 'x@y.z', ingested: 3, timestamp: 'M1' });
    await new Promise((r) => setTimeout(r, 150));
    check('no speech from non-speak events', spoken.length === before.spoken,
      JSON.stringify(spoken));
    check('no orb reveal from non-wake events', calls.revealOrb === before.reveal,
      `revealOrb ${before.reveal} -> ${calls.revealOrb}`);

    try { root.unmount(); } catch { /* ignore */ }
    container.remove();
  } finally {
    await vite.close().catch(() => {});
  }

  console.log('');
  if (failures.length) {
    console.log(`\u001b[31m=== ${failures.length} HANDS-FREE UI CHECK(S) FAILED ===\u001b[0m`);
    for (const f of failures) console.log(`\u001b[31m  - ${f}\u001b[0m`);
    process.exit(1);
  }
  console.log('\u001b[32m=== ALL HANDS-FREE UI CHECKS PASSED ===\u001b[0m\n');
}

main().catch((err) => { console.error('\u001b[31mHarness failed:\u001b[0m', err); process.exit(1); });
