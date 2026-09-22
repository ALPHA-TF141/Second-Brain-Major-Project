# JARVIS OS — FULL ERROR AUDIT REPORT

**Date:** 2026-09-22
**Scope:** complete frontend + Electron + backend + environment/dependency sweep
**Status:** ✅ **every check green — 0 errors**

This document covers two full audit passes. The second pass found serious bugs the
first pass missed, so read section 3 if you only read one thing.

---

## 1. The crash on your screen

```
JARVIS NEURAL CORE DIAGNOSTIC EXCEPTION
ReferenceError: Activity is not defined
    at HomeOS (/src/pages/HomeOS.jsx:33:35)
```

`HomeOS.jsx` rendered `<Activity />` but never imported `Activity` from `lucide-react`.
An unknown JSX tag is just an undefined variable → instant `ReferenceError` → the
ErrorBoundary replaced your whole screen with the red panel.

**Fixed**, and the static sweep also caught the identical bug waiting behind it:

| File | Missing symbol | Effect |
|---|---|---|
| `src/pages/HomeOS.jsx` | `Activity` | crashed the Home screen (what you saw) |
| `src/pages/AgentWorkspace.jsx` | `Brain` | would have crashed the **AI Agent** tab the moment you opened it |

`vite build` cannot catch these — a production build only proves the code *compiles*,
never that it *runs*. That is why the tooling in section 4 now exists.

---

## 2. First pass — backend, security and environment

| # | Where | Problem | Fix |
|---|---|---|---|
| 1 | `GET /api/graph/deliverables/content` | returned **500** (`IsADirectoryError`) when `filename` was empty — it tried to read the deliverables *folder* as a file | empty name → **400** with a clear message |
| 2 | same route + `GET /api/graph/vault/wiki/article` | **path traversal** — `filename=../../app/config.py` could read files outside the vault | `_safe_child()` resolves the path and rejects anything escaping its root |
| 3 | 15 endpoints in `routes/graph.py` | a missing node/cluster answered **`500` with a body saying "404: not found"**, because `except Exception` swallowed the deliberate `HTTPException` and re-wrapped it | `except HTTPException: raise` inserted before each generic handler → the UI now gets real 404s |
| 4 | `backend/requirements.txt` | **`httpx` is imported at module level** (`llm_client.py`, `social_ingestion_agent.py`) but was undeclared → a fresh machine crashed on startup. Your machine only worked because it had been installed by hand. `pillow` and `numpy` were also imported but undeclared | all three added |
| 5 | optional engines | `chromadb`, `sentence-transformers`, `whisper`, `paddleocr`, `neo4j`, `edge-tts` were undocumented — no way to know what was missing | new `backend/requirements-optional.txt` lists each pack, what it unlocks, and its size |

**Proof:** a brand-new empty virtual environment built from `requirements.txt` alone now
boots the backend — verified again on this pass: `FRESH VENV BOOT: OK`.

---

## 3. Second pass — the bugs that were breaking the app quietly

These do not show a red screen. They show **empty panels that look fine**, which is
worse. Every one was found by actually booting the backend, logging in, and calling
all 116 routes.

### 3.1 🔴 Login had never worked — `POST /api/auth/login` returned HTTP 500

```
NameError: name 'settings' is not defined
    at backend/app/services/auth_service.py, line 13
```

`auth_service.py` used `settings.demo_username` **without importing `settings`**. The
function raised *before* it ever compared a password, so on a fresh database **every
login attempt failed**.

Why you never saw an error: the frontend swallowed it —

```js
apiClient.login(...).catch(() => setUsername('Immanuel'));   // ← hides the 500
```

— so the app booted with **no JWT token at all**, and every protected endpoint answered
`401`. That is **52 endpoints**: the memory archive, the knowledge graph, OCR history,
capture status, settings, timeline, semantic search, voice sessions and the activity log
all rendered as empty shells. The only screens showing data were the newer `/api/os/*`
ones, because those happen to be unauthenticated.

**Fix:** `from app.config import settings`.
**Result:** login → `200`, and the graph now reports **350 nodes / 500 edges**.

### 3.2 🔴 33 call sites bypassed authentication

`apiClient.request()` attaches the token, but **33 screens used raw `fetch()`**, which
does not. Even with a valid token, those panels would still have 401'd:

> Knowledge · Files · Dashboard widgets · Gmail (task creation) · Tasks · Reminders ·
> Calendar · Automations · Integrations · Projects · Command palette · Social hub ·
> Executive briefing · Deliverable forge

**Fix:** new authenticated `apiFetch()` helper in `services/apiClient.js`, plus a codemod
applied across **18 files**. Verified: **0 raw backend fetches remain**.

### 3.3 Other second-pass fixes

| # | File | Problem | Fix |
|---|---|---|---|
| 6 | 5 canvas components | `canvas.getContext('2d')` returns **`null`** when a GPU is unavailable/blacklisted (common in Electron, and what happens on VMs) → `clearRect` of null → red screen | `if (!ctx) return` guard in `LivingJarvisCore`, `NeuralBrain3D`, `GoldenJarvisMatrix`, `InteractiveKnowledgeGraphEngine`, `ObsidianGraphView` |
| 7 | `AgentWorkspace.jsx`, `Chat.jsx` | `scrollIntoView is not a function` in some webview contexts | optional-call guard |
| 8 | `KnowledgeWorkspace.jsx`, `FilesWorkspace.jsx` | `X.filter is not a function` when an endpoint answers with a non-array (error envelope) | new `readList()` helper normalises any response to an array |
| 9 | `ProjectsWorkspace.jsx` | `.toUpperCase()` on `undefined` `status` / `priority` | safe defaults |
| 10 | `VoiceAssistant.jsx` | preferences were replaced wholesale → controlled input became uncontrolled → **typing in voice settings broke** | merge over defaults instead of replacing |
| 11 | `GET /api/graph/nodes/{node_id}` | declared `node_id: int`, but `/api/graph/nodes` returns **string** card ids (`card_20260921_…`) → every node-detail lookup failed | endpoint now understands **both** id spaces (SQLite int + vault JSON string) |
| 12 | `package.json` | **`npm install` failed with `ERESOLVE`**: `@eslint/js@^10` peer-requires ESLint 10, but ESLint was pinned `^9.39.5` → the lint tooling could not be installed at all | versions aligned to `^9.39.5` |

### 3.4 The verifier itself crashed on your machine (Node 24)

When you ran `verify-jarvis.ps1`, gate 4 died with:

```
TypeError: Cannot set property navigator of #<Object> which has only a getter
    at tools/smoke-render.mjs:41
```

**Cause:** Node 21+ ships `globalThis.navigator` as a **getter-only accessor**, so a plain
`globalThis.navigator = dom.window.navigator` throws. It worked in my sandbox because that
had Node 20. Your machine has Node 24.12.0. `crypto` is an accessor too.

**Fix:** all browser globals are now installed through a `setGlobal()` helper that uses
`Object.defineProperty` (they are still `configurable`), with plain assignment as a
fallback. Verified on **both** Node 24.12.0 and Node 20.20.2.

While in there I also removed the noisy
`MODULE_TYPELESS_PACKAGE_JSON` warning by renaming `eslint.config.js` → `eslint.config.mjs`.
(Adding `"type": "module"` to `package.json` would have been the other fix, but that
**breaks Electron** — `electron/main.js` and `run_backend.js` use CommonJS `require`.)

### 3.5 All 47 ESLint warnings cleared

The remaining warnings were all dead variables. They are now removed, so the lint output is
**0 errors / 0 warnings** — meaning any future warning is a real signal, not background
noise. One removal had to be reverted: `setIsConnected` in `GmailWorkspace.jsx` looked
unused but the "Connect Gmail Account" button calls it inline. Restored, with a comment
noting it only flips local UI state (see section 6).

### 3.6 Gate 7's "crash" was really a 30-second timeout — and it exposed two real bugs

Your run ended with:

```
--- 5xx SERVER ERRORS / CRASHES (1) ---
    -1  GET /api/semantic/related/1
```

`-1` is not an HTTP status — it means **my sweep's own client never got a reply**. Just
above it in your log:

```
Warning: You are sending unauthenticated requests to the HF Hub...
Loading weights: 100%|███| 103/103
```

The semantic engine loads `sentence-transformers` **inside the first request** that needs
it, downloading and loading the model from HuggingFace. That took longer than the 30-second
timeout I had configured, so the sweep gave up and mislabelled it as a server crash.

Three fixes:

1. **Backend: the embedding model is now warmed up in a background thread at startup**, so
   the model is usually ready before you open anything. Previously the first visit to
   Semantic Memory (or any semantic search) hung for 30s+ — a real, user-visible stall.
2. **Backend: `semantic_search` degrades to keyword search instead of 500ing** while the
   model is still loading or if `sentence-transformers` is not installed.
3. **My sweep was wrong and is now honest**: 180s timeout, a warm-up pass before timing,
   slow-but-successful calls listed under their own heading, and "no response / timeout"
   reported separately from "5xx server error" so a real crash can never hide behind
   "it's just slow".

### 3.7 Your Ollama model is missing — that is why Jarvis answered with a canned line

Your log:

```
[LLM] Ollama native stream failed: Ollama returned 404: {"error":"model 'qwen2.5:3b' not found"}
[LLM] OpenAI stream failed: Error code: 404 - model 'qwen2.5:3b' not found
```

Ollama no longer has `qwen2.5:3b`, so every generative reply fell through to the offline
fallback text — which then blamed *"not enough indexed memory context"*, pointing you at the
wrong problem entirely.

**Fixes:**

- `LLMClient` now asks Ollama `/api/tags` what is actually installed, uses the configured
  model when present, otherwise picks the closest installed model, and says so plainly:
  `[LLM] Configured model 'qwen2.5:3b' is not installed in Ollama. Using 'llama3.2:3b'
  instead. (Run: ollama pull qwen2.5:3b)`
- The offline fallback now names the real cause instead of blaming your memories:
  *"Local language model unavailable — Ollama returned 404 … Check that Ollama is running
  (ollama list) and that the model is installed."*
- Detection probes the server rather than trusting the URL, so a non-standard port or a
  remote Ollama still works. Tested against fake Ollama servers: configured-model-present,
  configured-model-missing, only-a-variant, nothing-installed, and server-unreachable.

**Action on your side:** run `ollama list`. If `qwen2.5:3b` is absent, either
`ollama pull qwen2.5:3b`, or leave it — Jarvis will now use whichever model you do have.

---

## 4. Permanent error-check system

Eight gates, all committed, none of them need the internet.

| Command | What it catches |
|---|---|
| `npm run lint` | **undefined variables / unimported JSX components** (the whole "blank screen / red panel" family), duplicate props, hook-rule violations |
| `npm run health:check` | 8 static checks: relative imports resolve · every `lucide-react` icon exists · every `apiClient.x()` has a definition · every backend module in `main.py` exists · **every `/api/...` URL the frontend calls matches a real route** · every `window.secondBrain.*` call is exposed by `preload.js` · every Python file compiles · every route in `AppRoutes.jsx` points at a real file |
| `npm run check:api` | dedicated UI ↔ backend **contract check**: parses all 116 backend routes and every URL the UI requests, reports 404 mismatches |
| `npm run smoke` | renders **all 18 routes** through React *and* mounts them in a live DOM so `useEffect` runs — catches runtime crashes a build never sees. No browser download needed. |
| `npm run build` | production bundle must compile |
| `npm run verify:backend` | boots the backend in-process, logs in, and calls **every GET route**, failing on any 5xx |
| `npm run smoke:browser` | optional: loads all 18 routes in **real Chromium**, saves screenshots to `artifacts/smoke/` *(one-time `npm run smoke:setup`)* |
| `backend/test_all_endpoints.py` | the 11-suite live functional test |

### One command (Windows)

```
verify-jarvis.bat        <- double-click this
.\verify-jarvis.ps1      <- or run in PowerShell
```

Runs all eight gates in order, stops with a clear `[FAIL]` marker.

### The guard was tested against the real bug

I deliberately re-introduced the exact crash and confirmed the tooling refuses it:

```
src/_guardtest.jsx
  3:16  error  'Activity' is not defined        react/jsx-no-undef
  3:37  error  'undefinedThing' is not defined  no-undef
```

Non-zero exit → `verify-jarvis` would have blocked it. This bug cannot ship again.

---

## 5. Verification results (final, this commit)

```
1. ESLint ..................... 0 errors, 0 warnings  (verified on Node 24.12.0 AND Node 20.20.2)
2. Static health check ........ ALL 8 CHECKS PASSED - 0 ERRORS
3. API contract ............... 46 / 46 UI endpoints matched - NO 404 RISK
4. Route render smoke ......... 18 / 18 routes render AND mount cleanly
5. Production build ........... built in 3.50s (1614 modules)
6. Backend test suites ........ ALL 11 TEST SUITES PASSED - 0 errors
7. Endpoint sweep ............. ok 58, slow 0, 4xx 13, timeouts 0, 5xx/crash 0   (exit 0)
8. Live API sweep tool ........ 71 GET endpoints probed, 0 crashing
9. Fresh venv from requirements boots OK, 124 routes
10. LLM model auto-detection ... 5/5 scenarios correct (incl. your missing-model case)
```

The 13 remaining 4xx are correct behaviour, not bugs: `401` on the four routes that
authenticate via `?token=` in the query string, `404` for sample ids that do not exist in
the database yet, `422` for `learning-path` (needs two query params), and `400` for the
deliverables route called with no filename.

---

## 6. Not errors — but they do break your "no fake data" rule

You asked me to flag anything pretend, and to label it. Honestly:

| Where | What is fake | Reality |
|---|---|---|
| **Home → "While You Were Away"** | `7 emails processed`, `2 calendar updates`, `3 tasks due`, `2 reminders`, `3 actions completed` | **hardcoded fallbacks** — `intel?.…?.emails_unread \|\| 7`. They display even though Gmail/Calendar were never connected. |
| **Home → "What Needs Your Attention"** | 3 priority alerts (Prof. Sharma deadline, AQI validation, dept. documentation) | hardcoded demo strings in `HomeOS.jsx` |
| **Gmail** | Inbox / Important / Sent / Drafts with 2 emails from `Prof. Sharma` | **no Gmail OAuth exists.** "Connect Gmail" only flips local state; it never talks to Google. |
| **Calendar** | "AI Project Progress Review Meeting", "Air Pollution Dataset Validation Workshop" | seeded demo rows in `backend/data/os_store.json` |
| **Tasks / Reminders / Projects / Automations / Activity / Integrations** | pre-filled items (IEEE proposal, AQI model, GitHub sync…) | all seeded demo rows. GitHub, Ollama and the scraper rows are the only ones reflecting something genuinely configured. |
| **Knowledge Graph** | the rich interactive graph (Machine Learning, Prof. Sharma, IEEE paper…) | runs on a **hardcoded sample graph** in `InteractiveKnowledgeGraphEngine.jsx` — *not* your real vault graph, which has 350 real nodes available at `/api/graph/nodes` |
| **Agent Activity log** | "Synthesized Daily Executive Briefing", "Autonomous Git Memory Vault Pushed" | seeded rows, not a real audit trail |
| **Agent / Voice** | fake "Thinking → Searching → Reading Gmail" tool telemetry | simulated with timers in `AgentWorkspace.jsx`; no tools are invoked |
| **Jarvis voice fallback** | speaks "I do not have enough indexed memory context…" | honest no-context path, but it also appears when Ollama simply is not running. It should say *"Local model offline — start Ollama"*. |

**Genuinely real and working:** screen capture + OCR pipeline · memory vault (JSON cards,
hero images, WebP compression) · self-improving wiki compiler (28 articles) · GitHub vault
sync · native free scrapers (YouTube transcript / X / Instagram / web) · the real knowledge
graph data (350 nodes / 500 edges) · local Ollama LLM path · TTS path · the 15-tab OS shell.

**Recommended next pass** (say the word and I'll do it):

1. Replace the hardcoded Home numbers with live values — or show `—` when the source is
   not connected.
2. Turn Gmail/Calendar into honest **"Not Connected"** screens with a real connection flow.
3. Add a visible **`DEMO DATA`** badge to every seeded row.
4. Point the interactive graph at the **real 350-node vault graph**.

---

## 7. What to run on your machine

```powershell
cd "I:\Major projects\Second Brain"
git pull origin main

npm install          # required once - new dev tooling was added

.\verify-jarvis.ps1  # full error check (all 8 gates)

.\start-jarvis.ps1   # launch the app
```

Optional, once, if you want the real-browser route test (downloads Chromium ~150 MB):

```powershell
npm run smoke:setup
```

If anything is still wrong, the terminal prints `[Renderer Console]` lines plus a red
diagnostic panel naming the exact file and line — send me that and I will fix it.
