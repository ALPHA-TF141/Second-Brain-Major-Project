# JARVIS OS — FULL ERROR AUDIT REPORT

**Date:** 2026-09-22
**Commit:** `1a90d25` (branch `main`)
**Scope:** complete frontend + backend + environment error sweep, with new automated
tooling so this can never silently regress again.

---

## 1. Errors found and fixed

### A. Crashes that caused your red "JARVIS NEURAL CORE DIAGNOSTIC EXCEPTION" screen

| # | File | Error | Root cause |
|---|------|-------|-----------|
| 1 | `src/pages/HomeOS.jsx:185` | `ReferenceError: Activity is not defined` | The Home screen rendered `<Activity />` but `Activity` was never imported from `lucide-react`. This is the exact crash in your screenshot. |
| 2 | `src/pages/AgentWorkspace.jsx:99` | `ReferenceError: Brain is not defined` | The AI Agent tab built its tool-status list with `icon: Brain`, but `Brain` was never imported. This was the **next** crash — waiting for you the moment you opened the AI Agent tab. |

Both are now imported. Verified with ESLint `no-undef` + `react/jsx-no-undef`.

### B. Backend bugs

| # | Endpoint | Problem | Fix |
|---|----------|---------|-----|
| 3 | `GET /api/graph/deliverables/content` | Returned **500** (`IsADirectoryError`) when `filename` was empty — it tried to `read_text()` the deliverables *folder*. | Empty name now returns **400** with a clear message. |
| 4 | `GET /api/graph/deliverables/content` + `GET /api/graph/vault/wiki/article` | **Path traversal.** `filename=../../app/config.py` would read files outside the vault. | New `_safe_child()` guard resolves the path and rejects anything escaping its root. |
| 5 | 15 endpoints in `backend/app/routes/graph.py` | A missing node/cluster returned **`500` with a body saying `"404: Node not found"`**, because `except Exception` swallowed the `HTTPException` and re-wrapped it as a 500. The UI could never tell "not found" from "server exploded". | Added `except HTTPException: raise` before the generic handler, so real 404s reach the frontend. |

### C. Environment / dependency errors

| # | Problem | Fix |
|---|---------|-----|
| 6 | **`httpx` was imported at module level in `llm_client.py` but is not in `requirements.txt`.** Any fresh machine crashed on startup with `ModuleNotFoundError: No module named 'httpx'` — your machine only worked because it had it installed manually. | Added `httpx==0.27.2` to `backend/requirements.txt`. |
| 7 | `pillow` (PIL) and `numpy` also imported directly but undeclared | Added to `backend/requirements.txt`. |
| 8 | The heavy optional engines (`chromadb`, `sentence-transformers`, `whisper`, `paddleocr`, `neo4j`, `edge-tts`, `openai`) were undocumented — no way to know what you were missing. | New `backend/requirements-optional.txt` documents each pack, what feature it unlocks, and its size. The backend already degrades gracefully without them. |

**Proof:** a brand-new empty virtual environment installed from `requirements.txt` alone
now boots the backend — `FRESH INSTALL BOOT: OK — 124 routes`. Before the fix it died on `httpx`.

---

## 2. New permanent error-check system

Five tools, all committed to the repo. Nothing requires the internet.

| Command | What it catches |
|---------|-----------------|
| `npm run lint` | Undefined variables, unimported JSX components, duplicate props, hook-rule violations — the whole "blank screen" family of bugs. |
| `npm run health:check` | 8 static checks: every relative import resolves · every `lucide-react` icon exists · every `apiClient.x()` call has a definition · every backend module in `main.py` exists · **every `/api/...` URL the frontend calls matches a real backend route** · every `window.secondBrain.*` call is exposed by `preload.js` · every Python file compiles · every route in `AppRoutes.jsx` points at a real file. |
| `npm run build` | Production bundle must compile. |
| `npm run smoke` | Boots the real backend + frontend and loads **all 18 routes in a real Chromium**, failing on any uncaught exception, console error, ErrorBoundary panel, or empty render. Saves screenshots to `artifacts/smoke/`. *(Needs a one-time `npm run smoke:setup`.)* |
| `python scripts/api_sweep.py` | Probes **every GET endpoint** of the live backend and fails on any 5xx (`0` = no crashes). |
| `backend/test_all_endpoints.py` | The original 11-suite live backend test. |

### One-command version (Windows)

```
verify-jarvis.bat      <- double-click this
.\verify-jarvis.ps1    <- or run from PowerShell
```

It runs all five stages in order and stops with a clear `[FAIL]` marker.

---

## 3. Verification results (this commit)

```
1. ESLint ...................... 0 errors, 47 warnings (benign unused vars)
2. Static health check ......... ALL 8 CHECKS PASSED - 0 ERRORS
3. Production build ............ ✓ built in 3.66s
4. Backend API sweep ........... 71 endpoints probed, 0 CRASHING
5. Browser smoke test .......... ALL 18 ROUTES RENDERED CLEAN
6. Backend test file ........... ALL 11 TEST SUITES PASSED, 0 ERRORS
7. Fresh venv install .......... boots OK, 124 routes
```

Routes proven clean in a real browser: `/jarvis-orb  /  /agent  /chat  /gmail  /calendar
/tasks  /notifications  /reminders  /knowledge  /knowledge-graph  /files  /projects
/automations  /activity  /integrations  /voice  /settings`

Screenshots of every route are in `artifacts/smoke/` — open them to see exactly how each
tab renders.

---

## 4. What you must run on your machine

```powershell
cd "I:\Major projects\Second Brain"
git pull origin main

# new dev tools were added (eslint) - this is required once:
npm install

# optional: enable the real-browser route test (downloads Chromium once, ~150 MB)
npm run smoke:setup

# prove the whole project is clean:
.\verify-jarvis.bat
```

Then start the app as usual:

```powershell
.\start-jarvis.ps1
```

If anything is still wrong, the terminal will now print lines beginning
`[Renderer Console]` plus a red diagnostic panel naming the exact file and line.

---

## 5. Not errors — but they violate your own "no fake data" rule

These are **product decisions, not bugs**, so I did not change them without your go-ahead:

1. **Gmail workspace shows 2 sample emails** (Prof. Sharma / deadline) with no real OAuth
   connection. Your spec said: *"If a service is not connected, show Not Connected and
   provide connection flow."* Right now it half-pretends.
2. **Home "While You Were Away" shows 7 emails processed / 2 calendar updates** — these
   are seeded numbers in `backend/data/os_store.json`, not real counts.
3. **Projects / Tasks / Automations / Reminders contain seeded demo records.** Fine as a
   first-run example, but they should be labelled *sample* or replaced with real data.
4. **The Jarvis core can speak a fallback line** ("I do not have enough indexed memory
   context…") — that is the honest no-context path, but it currently shows even when
   Ollama is simply not running. It should say *"Local model offline — start Ollama"*
   instead, which is a different, more useful message.
5. **Wake word** is still Web Speech inside the Electron window. It works while the app
   is running, but true always-on "Hey Jarvis" from a cold desktop needs a native engine
   (openWakeWord / Porcupine) as a background service.

Say the word and I will convert 1–4 to honest "Not Connected / sample data" states and
build the real connection flows next.
