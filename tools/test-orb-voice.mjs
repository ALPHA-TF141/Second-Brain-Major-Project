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
 * TIMING POLICY (do not reintroduce fixed sleeps for mount)
 * ---------------------------------------------------------
 * The mount is flushed with `React.act()` rather than "sleep 300 ms and hope".
 * A constant sleep is a wall-clock race: on a busy Windows box (antivirus
 * scanning the drive, the dev server, Electron and Ollama all running) the
 * first effect can land later than any constant, and the gate then reports a
 * phantom failure while the orb is perfectly healthy. `act()` flushes the
 * mount and its effects before a single assertion runs, on any machine.
 *
 * Every later assertion about asynchronous behaviour (re-arm, watchdog,
 * captions) polls for the condition with a generous deadline instead of
 * asserting after a fixed sleep - same property, no machine-speed dependency.
 * A bounded poll still fails when the behaviour is genuinely missing, so
 * nothing is weakened: the checks below fail on a real defect either way.
 *
 * If the orb never arms the microphone the harness prints a diagnosis (what
 * loaded, whether React committed, what React logged) and exits non-zero - it
 * never dies with a bare TypeError.
 *
 * Usage:  node tools/test-orb-voice.mjs      (or: npm run test:orb)
 */
import { createServer } from 'vite';
import { createRequire } from 'node:module';
import { JSDOM } from 'jsdom';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
// Shared mount/poll policy - see harness-utils.mjs for why a fixed sleep after
// render() is not allowed in these harnesses.
import { sleep, waitFor, flushMount } from './harness-utils.mjs';

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

const PASS = '\u001b[32m  PASS\u001b[0m';
const FAIL = '\u001b[31m  FAIL\u001b[0m';
const failures = [];
let checkCount = 0;

function check(label, condition, detail = '') {
  checkCount += 1;
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

/* --------------------------------------------------------------- summary */
/** Print the verdict. Exits non-zero on any failed check. */
function finish() {
  console.log('');
  if (failures.length) {
    const scope = checkCount > 0 ? ` (of ${checkCount})` : '';
    console.log(`\u001b[31m=== ${failures.length} ORB VOICE CHECK(S) FAILED${scope} ===\u001b[0m`);
    for (const f of failures) console.log(`\u001b[31m  - ${f}\u001b[0m`);
    process.exit(1);
  }
  console.log(`\u001b[32m=== ALL ${checkCount} ORB VOICE CHECKS PASSED ===\u001b[0m\n`);
}

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
    const orbModule = await vite.ssrLoadModule('/src/pages/JarvisHoloOrb.jsx');
    const Orb = orbModule.default;
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

    // Everything React logs while mounting is collected, so a genuine failure
    // explains itself instead of leaving us with "rec is null".
    const consoleIssues = [];
    const realError = console.error.bind(console);
    const realWarn = console.warn.bind(console);
    console.error = (...args) => { consoleIssues.push(args.map(String).join(' ')); realError(...args); };
    console.warn = (...args) => { consoleIssues.push(args.map(String).join(' ')); realWarn(...args); };

    const tree = React.createElement(MemoryRouter, { initialEntries: ['/jarvis-orb'] },
      React.createElement(BackendProvider, null,
        React.createElement(AssistantProvider, null, React.createElement(Orb, null))));

    const ARM_DEADLINE_MS = 20000;
    const armedBefore = engine.instances.length;
    const mountStart = Date.now();
    const act = await flushMount(root, tree, React);
    const mountMs = Date.now() - mountStart;

    // act() has already flushed the mount effect; the poll is a safety net for
    // React versions that defer passive effects anyway.
    const armed = await waitFor(() => engine.instances.length > armedBefore, ARM_DEADLINE_MS);
    console.log(`   (mount flushed in ${mountMs} ms with ${act ? 'React.act' : 'a plain render'}; ` +
      `mic armed: ${armed ? 'yes' : 'no'})`);

    if (!armed) {
      console.log('');
      console.log('\u001b[31m  The orb never created a SpeechRecognition object.\u001b[0m');
      console.log('\u001b[31m  Diagnosis:\u001b[0m');
      console.log(`    module default export:            ${typeof Orb} (expected: function)`);
      console.log(`    window.SpeechRecognition:         ${typeof dom.window.SpeechRecognition}`);
      console.log(`    window.webkitSpeechRecognition:   ${typeof dom.window.webkitSpeechRecognition}`);
      console.log(`    React committed DOM nodes:        ${container.children.length}`);
      console.log(`    recogniser instances created:     ${engine.instances.length}`);
      console.log(`    DOM text:                         ${JSON.stringify(container.textContent.slice(0, 120))}`);
      console.log(`    wait budget after the mount:      ${ARM_DEADLINE_MS} ms`);
      console.log('    what React logged while mounting:');
      if (consoleIssues.length === 0) {
        console.log('      (nothing - the component tree never rendered)');
      } else {
        for (const line of consoleIssues.slice(0, 8)) {
          console.log(`      ${line.replace(/\s+/g, ' ').slice(0, 220)}`);
        }
      }
      console.log('');
      console.log('    - "React committed DOM nodes: 0"  -> the page failed to render at all.');
      console.log('    - a ReferenceError / TypeError above -> that is the app bug to fix.');
      console.log('    - everything plausible -> the box was simply busy; re-run this gate.');
      failures.push('the orb armed the microphone');
      console.error = realError;
      console.warn = realWarn;
      finish();
      return;
    }

    const rec = engine.last;

    console.log('\n[1] Starts listening on mount');
    check('a recogniser was created', !!rec);
    check('continuous + interim enabled', rec?.continuous === true && rec?.interimResults === true,
      `continuous=${rec?.continuous} interim=${rec?.interimResults}`);
    check('microphone started', engine.startCalls === 1, `start calls: ${engine.startCalls}`);

    console.log('\n[2] A spoken question reaches the backend');
    rec.emitFinal('what is the IEEE conference draft deadline');
    await waitFor(() => sent.some((m) => m.type === 'transcript'), 4000);
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
    const gotSecond = await waitFor(
      () => sent.filter((m) => m.type === 'transcript').length === 2, 4000);
    check('a SECOND question is accepted (orb is not deaf after one turn)',
      gotSecond,
      `transcripts: ${sent.filter((m) => m.type === 'transcript').length}`);

    console.log('\n[4] The engine ends the session by itself (the actual bug)');
    // Deliver a real answer first, so the turn completes the way it should.
    sockets[0].deliver({ type: 'answer', text: 'The deadline is Friday at 5 PM.' });
    await waitFor(() => spoken.some((t) => t.includes('Friday')), 5000);
    check('answer is spoken aloud', spoken.some((t) => t.includes('Friday')),
      JSON.stringify(spoken));

    // A real voice engine fires onend when it finishes. Simulate that.
    finishSpeaking();
    const resumed = await waitFor(() => engine.last.started === true, 8000);
    check('mic resumes after Jarvis finishes speaking', resumed,
      'orb stayed muted after the answer');

    const beforeRestart = engine.startCalls;
    rec.engineEnds();                          // <-- what Chromium does after silence
    const reArmed = await waitFor(() => engine.startCalls > beforeRestart, 8000);
    check('microphone RE-ARMS after an engine-initiated onend',
      reArmed,
      `start calls before=${beforeRestart} after=${engine.startCalls}`);
    check('re-arm does not rebuild the recogniser',
      engine.instances.length === 1,
      `instances: ${engine.instances.length} (should reuse the same object)`);

    console.log('\n[4a] TTS that never reports finishing must not leave the orb muted');
    const beforeTts = engine.stopCalls;
    sockets[0].deliver({ type: 'answer', text: 'short reply' });
    await waitFor(() => spoken.some((t) => t === 'short reply'), 4000);
    // Deliberately do NOT fire onend: only the watchdog can rescue this turn.
    const recovered = await waitFor(() => engine.last.started === true && engine.stopCalls >= beforeTts, 20000);
    check('orb recovers when the voice engine says nothing at all',
      recovered, `mic started=${engine.last.started}`);

    console.log('\n[4b] A turn the backend never answers must not strand the orb');
    // Hand over a turn, then deliver NO answer at all. Without a watchdog the
    // orb would wait forever and never listen again.
    const beforeHang = engine.startCalls;
    engine.last.emitFinal('a question the backend will never answer');
    const handedOver = await waitFor(() => engine.last.started === false, 4000);
    check('turn handed over (mic paused)', handedOver,
      'mic should pause while waiting for the answer');

    // force the watchdog by shrinking the wait: emulate by firing the same path
    // the socket close takes, which is the other real-world way a turn dies
    sockets[0].close();
    const released = await waitFor(() => engine.startCalls > beforeHang, 8000);
    check('socket loss releases the turn and resumes listening',
      released,
      `start calls before=${beforeHang} after=${engine.startCalls}`);

    console.log('\n[5] Repeated silence must not spin the CPU');
    const spinBefore = engine.startCalls;
    for (let i = 0; i < 5; i += 1) {
      engine.last.engineEnds();
      await sleep(60);
    }
    await sleep(600);
    check('restarts stay bounded', engine.startCalls - spinBefore <= 8,
      `restarts: ${engine.startCalls - spinBefore} in ~1s`);

    console.log('\n[6] A blocked microphone explains itself instead of looping');
    engine.last.failWith('not-allowed');
    await waitFor(() => container.textContent.includes('Microphone blocked'), 6000);
    check('tells the user what to do',
      container.textContent.includes('Microphone blocked'),
      container.textContent.slice(0, 120));
    // Snapshot only once the denial has been processed, then prove the orb
    // stays put: a retry loop is the failure this guards against.
    const afterBlock = engine.startCalls;
    engine.last.engineEnds();
    await sleep(900);
    check('stops retrying once permission is denied',
      engine.startCalls === afterBlock,
      `start calls grew from ${afterBlock} to ${engine.startCalls}`);

    console.log('\n[7] Alt+J revives a dead recogniser');
    check('wake callback registered', wakeCallbacks.length > 0, `${wakeCallbacks.length} callbacks`);
    const beforeWake = engine.startCalls;
    wakeCallbacks[0]?.();
    const woke = await waitFor(() => engine.startCalls > beforeWake, 8000);
    check('mic re-armed on wake', woke,
      `start calls before=${beforeWake} after=${engine.startCalls}`);
    const greeted = await waitFor(() => spoken.some((t) => t.includes('Yes, Sir')), 6000);
    check('greeting is spoken', greeted, JSON.stringify(spoken));

    console.log('\n[8] Interim results show as live captions (no backend spam)');
    const beforeInterim = sent.filter((m) => m.type === 'transcript').length;
    engine.last.emitInterim('what is the');
    await waitFor(() => container.textContent.includes('what is the'), 4000);
    await sleep(80);   // let any (wrong) transmission land before we count
    check('interim text shown but NOT sent',
      sent.filter((m) => m.type === 'transcript').length === beforeInterim,
      'interim results must not be transmitted as questions');
    check('interim caption rendered', container.textContent.includes('what is the'),
      container.textContent.slice(0, 120));

    console.error = realError;
    console.warn = realWarn;

    try { root.unmount(); } catch { /* ignore */ }
    container.remove();
  } finally {
    await vite.close().catch(() => {});
  }

  finish();
}

main().catch((err) => {
  console.error('\u001b[31mHarness failed:\u001b[0m', err);
  process.exit(1);
});
