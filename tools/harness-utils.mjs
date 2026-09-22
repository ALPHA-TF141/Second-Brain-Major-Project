/**
 * Shared helpers for the jsdom harnesses (smoke-render, test-orb-voice,
 * test-proactive-ui).
 * ===========================================================================
 * WHY THIS EXISTS - the "phantom failure" class of bug
 * ------------------------------------------------
 * All three harnesses render React into jsdom and then assert things about
 * what the app did. They used to assert after a fixed sleep:
 *
 *     root.render(<App />);
 *     await new Promise((r) => setTimeout(r, 350));   // <- hope
 *     assert(...);
 *
 * A fixed sleep is not a property of the application, it is a bet on how fast
 * the machine schedules React's work. React does not run effects inside
 * render(): it commits, then flushes passive effects in a later scheduler
 * task, a task that can be delayed indefinitely on a loaded box (Windows
 * Defender scanning the repo drive, the Electron dev server, Ollama pulling a
 * model, a page-file thrash). When that delay happened the harness asserted
 * against a tree whose effects had not run yet and reported
 * "a recogniser was created: FAIL" while the orb was perfectly healthy -
 * reproduced on this repo with a 700 ms stall of React's scheduler.
 *
 * The fix is to stop guessing and flush the work deliberately:
 *
 *     await flushMount(root, tree, React);   // effects are done when this returns
 *
 * `React.act()` (React 18.3+ / 19) runs the commit AND the passive effects
 * before it resolves, so there is nothing left to race. Everything that is
 * genuinely asynchronous (a 300 ms re-arm delay, a watchdog, a fetch) is
 * asserted with `waitFor()` - a bounded poll. That keeps the checks exactly as
 * strict as they were (a missing behaviour still fails, after the deadline),
 * while a slow machine only costs wall-clock time instead of producing a
 * failure that is not real.
 *
 * Rules of thumb for these harnesses:
 *   - never assert right after a bare render(); flush it first
 *   - never assert "eventually X" after a fixed sleep; use waitFor()
 *   - a negative assertion ("must NOT happen") should keep its sleep, and can
 *     only get stronger from an act() flush, because the work is done first
 */
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * Poll until `predicate()` is true or the deadline passes.
 * Returns true when the condition was reached. A throwing predicate counts as
 * "not yet", so a not-yet-mounted component never crashes the harness.
 */
export async function waitFor(predicate, timeout = 8000, step = 25) {
  const deadline = Date.now() + timeout;
  for (;;) {
    try {
      if (predicate()) return true;
    } catch {
      /* not ready */
    }
    if (Date.now() >= deadline) return false;
    await sleep(step);
  }
}

/** React 19 exposes act() on React itself; React 18.3 has React.act too,
 *  older React keeps it in react-dom/test-utils. Falls back to null. */
export function getAct(React) {
  if (React && typeof React.act === 'function') return React.act;
  try {
    const act = require('react-dom/test-utils').act;
    return typeof act === 'function' ? act : null;
  } catch {
    return null;
  }
}

/**
 * Render `tree` into `root` and flush it - commit plus passive effects - so
 * the caller may assert immediately afterwards. Returns the act() function
 * that was used, or null when the installed React has none (in which case the
 * caller must wait for whatever it needs explicitly).
 */
export async function flushMount(root, tree, React) {
  const act = getAct(React);
  if (!act) {
    root.render(tree);
    return null;
  }
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  try {
    await act(async () => {
      root.render(tree);
    });
  } finally {
    // Leave the flag off: the harness drives real timers afterwards and React
    // would report every one of those updates as "not wrapped in act(...)".
    globalThis.IS_REACT_ACT_ENVIRONMENT = false;
  }
  return act;
}

/**
 * Deliver an event to the app (socket message, DOM event) and, when act() is
 * available, flush the React updates it causes. Used so that "did the UI
 * react to this event?" is answered deterministically instead of after a
 * fixed sleep.
 */
export async function flushEvent(act, fn) {
  if (!act) {
    await fn();
    return;
  }
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  try {
    await act(async () => {
      await fn();
    });
  } finally {
    globalThis.IS_REACT_ACT_ENVIRONMENT = false;
  }
}
