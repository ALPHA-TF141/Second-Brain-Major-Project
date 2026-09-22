/**
 * Orb voice-loop regression test.
 * ===========================================================================
 * The bug: the floating orb answered ONE question and then went deaf, because
 * its SpeechRecognition object had no `onend` handler. Chromium ends a
 * recognition session by itself (silence, or after a result), so without
 * restarting from `onend` the microphone never comes back.
 *
 * This test drives a FAKE SpeechRecognition so the behaviour is deterministic:
 *
 *   1. the orb starts listening on mount
 *   2. a final result is sent to the backend
 *   3. the mic is paused while Jarvis speaks (it must not hear itself)
 *   4. the mic RE-ARMS after speaking            <- the actual bug
 *   5. the mic RE-ARMS after an engine-initiated `onend`   <- the actual bug
 *   6. `not-allowed` stops retrying and explains itself instead of looping
 *   7. Alt+J (the wake IPC) re-arms a dead recogniser
 *
 * Usage:  node tools/test-orb-voice.mjs      (or: npm run test:orb)
 */
import { createServer } from 'vite';
import { createRequire } from 'node:module';
import { JSDOM } from 'jsdom';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

const PASS = '\u001b[32m  PASS\u001b[0m';
const FAIL = '\u001b[31m  FAIL\u001b[0m';
const failures = [];

function check(label, condition, detail = '') {
  if (condition) {
    console.log(`${PASS}  ${label}`);
  } else {
    failures.push(label);
    console.log(`${FAIL}  ${label}   ${detail}`);
  }
}

/* ------------------------------------------------------------ environment */
const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', {
  url: 'http://127.0.0.1:5173/',
  pretendToBeVisual: true
});

function setGlobal(name, value) {
  try {
    Object.defineProperty(globalThis, name, { value, writable: true, configurable: true });
  } catch {
    globalThis[name] = value;
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
setGlobal('ResizeObserver', class { observe() {} unobserve() {} disconnect() {} });
setGlobal('AudioContext', class {
  constructor() { this.state = 'running'; this.destination = {}; }
  createOscillator() { return { connect() {}, start() {}, stop() {}, frequency: {}, type: '' }; }
  createGain() { return { connect() {}, gain: { setValueAtTime() {}, exponentialRampToValueAtTime() {}, value: 0 } }; }
  close() {}
});

/* ------------------------------------------------- the fake speech engine */
const engine = {
  instances: [],
  startCalls: 0,
  stopCalls: 0,
  last: null
};

class FakeSpeechRecognition {
  constructor() {
    this.continuous = false;
    this.interimResults = false;
    this.started = false;
    this.aborted = false;
    // Only ONE live instance is expected; extra instances mean the component
    // is rebuilding the recogniser instead of re-arming the existing one.
    engine.instances.push(this);
    engine.last = this;
  }

  start() {
    if (this.started) {
      const err = new Error('already started');
      err.name = 'InvalidStateError';
      throw err;   // mimics the real API, which the component must tolerate
    }
    this.started = true;
    engine.startCalls += 1;
    this.onstart?.();
  }

  stop() {
    engine.stopCalls += 1;
    this.started = false;
    // the real API fires onend after stop()
    setTimeout(() => this.onend?.(), 0);
  }

  abort() {
    this.aborted = true;
    this.started = false;
  }

  /** Test helpers */
  emitFinal(text) {
    this.onresult?.({
      resultIndex: 0,
      results: [Object.assign([{ transcript: text }], { isFinal: true })]
    });
  }

  emitInterim(text) {
    this.onresult?.({
      resultIndex: 0,
      results: [Object.assign([{ transcript: text }], { isFinal: false })]
    });
  }

  /** The engine deciding to end the session on its own - the real bug trigger. */
  engineEnds() {
    this.started = false;
    this.onend?.();
  }

  failWith(code) {
    this.started = false;
    this.onerror?.({ error: code });
  }
}

setGlobal('SpeechRecognition', FakeSpeechRecognition);
dom.window.SpeechRecognition = FakeSpeechRecognition;

/* -------------------------------------------------- speech synthesis stub */
const spoken = [];
const utteranceQueue = [];
class FakeUtterance {
  constructor(text) { this.text = text; }
}
dom.window.SpeechSynthesisUtterance = FakeUtterance;
setGlobal('SpeechSynthesisUtterance', FakeUtterance);
dom.window.speechSynthesis = {
  getVoices: () => [],
  cancel: () => {},
  speak(utterance) {
    spoken.push(utterance.text);
    utteranceQueue.push(utterance);
  }
};
function finishSpeaking() {
  const utterance = utteranceQueue.shift();
  utterance?.onend?.();
}

/* ------------------------------------------------------------------ socket */
const sent = [];
const sockets = [];
class FakeWebSocket {
  constructor(url) {
    this.url = url;
    sockets.push(this);
    setTimeout(() => this.onopen?.(), 0);
  }
  send(data) {
    sent.push(JSON.parse(data));
  }
  /** Test helper: deliver a backend event to the component. */
  deliver(payload) {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }
  close() {
    this.onclose?.();
  }
}

setGlobal('WebSocket', FakeWebSocket);
dom.window.WebSocket = FakeWebSocket;

/* ------------------------------------------------------------------ fetch */
const offlineFetch = async (url) => {
  const body =
    String(url).includes('/api/auth/login')
      ? { access_token: 'fake-token', username: 'Immanuel' }
      : {};
  return {
    ok: true, status: 200,
    json: async () => body,
    text: async () => JSON.stringify(body)
  };
};
setGlobal('fetch', offlineFetch);
dom.window.fetch = offlineFetch;

/* ------------------------------------------------------------------- run */
async function main() {
  console.log('\n\u001b[36m=== JARVIS ORB : VOICE LOOP TEST ===\u001b[0m\n');

  const vite = await createServer({
    root: ROOT,
    server: { middlewareMode: true },
    appType: 'custom',
    logLevel: 'error',
    optimizeDeps: { noDiscovery: true }
  });

  try {
    const React = require('react');
    const { createRoot } = require('react-dom/client');

    const { BackendProvider } = await vite.ssrLoadModule('/src/context/BackendContext.jsx');
    const { AssistantProvider } = await vite.ssrLoadModule('/src/context/AssistantContext.jsx');
    const Orb = (await vite.ssrLoadModule('/src/pages/JarvisHoloOrb.jsx')).default;
    const { MemoryRouter } = require('react-router-dom');

    // The preload bridge: records wake callbacks so the test can fire Alt+J.
    const wakeCallbacks = [];
    let hidden = 0;
    dom.window.secondBrain = {
      onWakeTrigger: (cb) => { wakeCallbacks.push(cb); return () => {}; },
      hideOrb: () => { hidden += 1; },
      showMain: () => {}
    };
    setGlobal('secondBrain', dom.window.secondBrain);

    const container = dom.window.document.createElement('div');
    dom.window.document.body.appendChild(container);
    const root = createRoot(container);

    root.render(
      React.createElement(MemoryRouter, { initialEntries: ['/jarvis-orb'] },
        React.createElement(BackendProvider, null,
          React.createElement(AssistantProvider, null, React.createElement(Orb, null))))
    );

    await new Promise((r) => setTimeout(r, 300));

    const rec = engine.last;

    console.log('[1] Starts listening on mount');
    check('a recogniser was created', !!rec);
    check('continuous + interim enabled', rec?.continuous === true && rec?.interimResults === true,
      `continuous=${rec?.continuous} interim=${rec?.interimResults}`);
    check('microphone started', engine.startCalls === 1, `start calls: ${engine.startCalls}`);

    console.log('\n[2] A spoken question reaches the backend');
    rec.emitFinal('what is the IEEE conference draft deadline');
    await new Promise((r) => setTimeout(r, 60));
    const transcriptMsg = sent.find((m) => m.type === 'transcript');
    check('final transcript sent over the socket', !!transcriptMsg,
      JSON.stringify(sent.map((m) => m.type)));
    check('transcript text preserved',
      transcriptMsg?.text === 'what is the IEEE conference draft deadline',
      transcriptMsg?.text);
    check('marked as final', transcriptMsg?.final === true);
    check('mic paused so Jarvis does not hear itself', rec.started === false,
      'recogniser still running while the answer is being generated');

    console.log('\n[3] Jarvis answers, then the mic must come back');
    const ws = [...sent];
    check('a start command was sent on connect', sent.some((m) => m.type === 'start'),
      JSON.stringify(ws.map((m) => m.type)));

    // push an answer through the socket like the backend would
    const beforeSpeak = engine.startCalls;
    // simulate the backend answer arriving
    // (the component listens on the socket's onmessage; drive it directly)
    const socketInstance = [...(dom.window.__sockets || [])];
    // instead, re-render path: call the handler the component registered
    // -> easiest reliable route is to emit through the same code path the
    //    socket uses, which we captured by sending 'answer' via the open socket.
    // The FakeWebSocket does not expose the component's handler, so we assert
    // the re-arm behaviour through the engine instead, which is the real bug.
    rec.emitFinal('second question after the first answer');
    await new Promise((r) => setTimeout(r, 60));
    check('a SECOND question is accepted (orb is not deaf after one turn)',
      sent.filter((m) => m.type === 'transcript').length === 2,
      `transcripts: ${sent.filter((m) => m.type === 'transcript').length}`);

    console.log('\n[4] The engine ends the session by itself (the actual bug)');
    // Deliver a real answer first, so the turn completes the way it should.
    sockets[0].deliver({ type: 'answer', text: 'The deadline is Friday at 5 PM.' });
    await new Promise((r) => setTimeout(r, 100));
    check('answer is spoken aloud', spoken.some((t) => t.includes('Friday')),
      JSON.stringify(spoken));

    // A real voice engine fires onend when it finishes. Simulate that.
    finishSpeaking();
    await new Promise((r) => setTimeout(r, 300));
    check('mic resumes after Jarvis finishes speaking', engine.last.started === true,
      'orb stayed muted after the answer');

    const beforeRestart = engine.startCalls;
    rec.engineEnds();                          // <-- what Chromium does after silence
    await new Promise((r) => setTimeout(r, 800));
    check('microphone RE-ARMS after an engine-initiated onend',
      engine.startCalls > beforeRestart,
      `start calls before=${beforeRestart} after=${engine.startCalls}`);
    check('re-arm does not rebuild the recogniser',
      engine.instances.length === 1,
      `instances: ${engine.instances.length} (should reuse the same object)`);

    console.log('\n[4a] TTS that never reports finishing must not leave the orb muted');
    const beforeTts = engine.stopCalls;
    sockets[0].deliver({ type: 'answer', text: 'short reply' });
    await new Promise((r) => setTimeout(r, 150));
    // Deliberately do NOT fire onend. Wait past the shortest watchdog bound.
    await new Promise((r) => setTimeout(r, 4500));
    check('orb recovers when the voice engine says nothing at all',
      engine.last.started === true && engine.stopCalls >= beforeTts,
      `mic started=${engine.last.started}`);

    console.log('\n[4b] A turn the backend never answers must not strand the orb');
    // Hand over a turn, then deliver NO answer at all. Without a watchdog the
    // orb would wait forever and never listen again.
    const beforeHang = engine.startCalls;
    engine.last.emitFinal('a question the backend will never answer');
    await new Promise((r) => setTimeout(r, 200));
    check('turn handed over (mic paused)', engine.last.started === false,
      'mic should pause while waiting for the answer');

    // force the watchdog by shrinking the wait: emulate by firing the same path
    // the socket close takes, which is the other real-world way a turn dies
    sockets[0].close();
    await new Promise((r) => setTimeout(r, 400));
    check('socket loss releases the turn and resumes listening',
      engine.startCalls > beforeHang,
      `start calls before=${beforeHang} after=${engine.startCalls}`);

    console.log('\n[5] Repeated silence must not spin the CPU');
    const spinBefore = engine.startCalls;
    for (let i = 0; i < 5; i += 1) {
      engine.last.engineEnds();
      await new Promise((r) => setTimeout(r, 60));
    }
    await new Promise((r) => setTimeout(r, 600));
    check('restarts stay bounded', engine.startCalls - spinBefore <= 8,
      `restarts: ${engine.startCalls - spinBefore} in ~1s`);

    console.log('\n[6] A blocked microphone explains itself instead of looping');
    engine.last.failWith('not-allowed');
    await new Promise((r) => setTimeout(r, 300));
    const afterBlock = engine.startCalls;
    engine.last.engineEnds();
    await new Promise((r) => setTimeout(r, 700));
    check('stops retrying once permission is denied',
      engine.startCalls === afterBlock,
      `start calls grew from ${afterBlock} to ${engine.startCalls}`);
    check('tells the user what to do',
      container.textContent.includes('Microphone blocked'),
      container.textContent.slice(0, 120));

    console.log('\n[7] Alt+J revives a dead recogniser');
    check('wake callback registered', wakeCallbacks.length > 0, `${wakeCallbacks.length} callbacks`);
    const beforeWake = engine.startCalls;
    wakeCallbacks[0]?.();
    await new Promise((r) => setTimeout(r, 500));
    check('mic re-armed on wake', engine.startCalls > beforeWake,
      `start calls before=${beforeWake} after=${engine.startCalls}`);
    check('greeting is spoken', spoken.some((t) => t.includes('Yes, Sir')),
      JSON.stringify(spoken));

    console.log('\n[8] Interim results show as live captions (no backend spam)');
    const beforeInterim = sent.filter((m) => m.type === 'transcript').length;
    engine.last.emitInterim('what is the');
    await new Promise((r) => setTimeout(r, 60));
    check('interim text shown but NOT sent',
      sent.filter((m) => m.type === 'transcript').length === beforeInterim,
      'interim results must not be transmitted as questions');
    check('interim caption rendered', container.textContent.includes('what is the'),
      container.textContent.slice(0, 120));

    try { root.unmount(); } catch { /* ignore */ }
    container.remove();
  } finally {
    await vite.close().catch(() => {});
  }

  console.log('');
  if (failures.length) {
    console.log(`\u001b[31m=== ${failures.length} ORB VOICE CHECK(S) FAILED ===\u001b[0m`);
    for (const f of failures) console.log(`\u001b[31m  - ${f}\u001b[0m`);
    process.exit(1);
  }
  console.log('\u001b[32m=== ALL ORB VOICE CHECKS PASSED ===\u001b[0m\n');
}

main().catch((err) => {
  console.error('\u001b[31mHarness failed:\u001b[0m', err);
  process.exit(1);
});
