# Baseline audit and implementation status

This records the state of the repository before and after the first
implementation pass, so every change can be traced to a measured starting
point. Commands are the ones in the README; results are from a clean Linux
sandbox (Python 3.11, Node 22), not from the Windows machine the roadmap targets.

## 1. Repository inventory (before changes)

| Area | Location | State found |
|---|---|---|
| Desktop shell | `electron/main.js`, `electron/preload.js` | Electron main process. Called `setupPermissions()` without defining it, so the app would throw inside `app.whenReady()`. |
| React UI | `src/pages/*.jsx` (8 pages), `src/services/apiClient.js` | Builds with Vite. Three `no-undef` lint errors (see §3). |
| Backend API | `backend/app/main.py`, `backend/app/routes/*.py` | FastAPI, 99 routes. Memory routes were read/search only; no create/edit/delete. |
| Persistence | `backend/app/database/`, SQLAlchemy models in `backend/app/models/` | SQLite via `create_all`. Runtime DB is `backend/data/second_brain.db` (git-ignored). |
| Research layer | `backend/app/research/` | Seven modules: scoring, temporal, contradictions, consolidation, gaps, forgetting, bench, plus neural NLI and a multi-user bench. Implemented, not previously covered by tests. |
| Benchmark | `backend/scripts/run_bench.py`, `backend/benchmark_results.json` | Deterministic (TF-IDF dense backend). Reproduced exactly on this machine (latency excepted). |
| Tests | `backend/tests/` | 5 tests before. 4 failed here because the optional ONNX NLI model cannot be downloaded in this sandbox. |
| API contract | `npm run check:api` | 19/19 frontend endpoints matched before, 22/22 after. |

## 2. Commands and results

| Check | Before | After |
|---|---|---|
| `npm install` (with `ELECTRON_SKIP_BINARY_DOWNLOAD=1`) | Fails without the flag: Electron binary download needs a host outside the sandbox allowlist. | Passes with the flag. |
| `npm run build` | Failed only because `node_modules` was missing. Passes once installed. | Passes. |
| `npm run lint` | 3 errors, 2 warnings | 0 errors, 0 warnings (`--max-warnings=0`). |
| `npm run check:api` | Pass (19/19) | Pass (22/22) |
| `pytest` (backend) | 1 passed, 4 failed | 21 passed, 4 skipped (neural NLI, see §4) |
| Backend start | Fails in this sandbox: `libGL.so.1` missing for `opencv-python`. | Starts with `opencv-python-headless` installed in the test venv. The pinned requirement is unchanged. |
| `run_bench.py` | Reproduces committed metrics | Reproduces committed metrics after the forgetting fix (verified by diff, latency excluded) |

## 3. Defects found and fixed

1. **Electron startup crash.** `setupPermissions()` was called but never defined.
   Fixed: defines a handler that grants only `media` (microphone for voice) and denies the rest.
2. **Gmail message open crash.** `GmailWorkspace.jsx` called an undefined `setTaskNotice`, so opening a message threw a ReferenceError. Removed the stale call.
3. **Integrations notice styling.** `IntegrationsManager.jsx` referenced an undefined `noticeStyle` map. Added the map for `error`, `success` and `info`.
4. **No user-facing memory CRUD.** Added `POST`, `GET` (list), `PUT` and `DELETE` on `/api/memory/memories`, with validation (422), duplicate detection (409), missing ids (404) and an audited soft/hard delete.
5. **Hard delete left orphans.** `ForgettingService.forget(hard=True)` removed the memory row but not its tags, relationships or tombstones. Fixed and covered by a test.
6. **Forgotten memories returned by detail view.** `GET /api/memory/memories/{id}` returned tombstoned memories. Now returns 404.
7. **Stale title after edit.** A title derived from the content kept the old words, so search still matched them after an edit. Derived titles now follow the edit; user-chosen titles are never overwritten.
8. **Tests could touch the real database.** Several research modules reset derived state on the configured database. `tests/conftest.py` now points the whole test session at a temporary SQLite file before any app module is imported.

## 4. Known gaps (not yet resolved)

- **Neural NLI tests are skipped in this sandbox.** They need `requirements-semantic.txt` and a HuggingFace download. They pass or skip with an explicit reason; they are not counted as passing.
- **Benchmark is small.** 15 memories and 11 questions. Hit@5 is 1.000 for all four pipelines, so the benchmark cannot separate them on recall. Expansion is required before any benchmark claim in the paper is treated as strong evidence.
- **`ForgettingService.forget()` deletes every `KnowledgeGap` row**, not just those tied to the forgotten memory. Gaps are derived, so this is recoverable, but it is broader than the policy suggests.
- **Baseline pipelines leak forgotten items by design** (vanilla/hybrid/graph leak rate 0.022). This is the "no suppression" comparison arm; the adaptive pipeline enforces exclusion.
- **Personal data is tracked in Git.** `data/second_brain.db` (repository root) is committed and contains an account e-mail address and connector identifiers. `memory_vault/` (cards, images, wiki, deliverables) is also committed. The runtime database `backend/data/` is git-ignored, so the tracked root copy is stale and unused. Removing tracked data is a repository decision and has not been made here.
- **README drift.** The README says vault cards, wiki and deliverables were removed, but `memory_vault/` is still tracked.
- **Contradiction and temporal tests use rule-based paths only.** The neural NLI detector is skipped here. The benchmark corpus does not contain the new cases, so its published numbers do not reflect them.
- **Temporal subject is always `user`.** Facts are not modelled as entity-to-entity relationships.
- **Roadmap phases 3–9 are not complete.** Retrieval-scoring tests, consolidation test cases, graph/timeline/conflict UI, benchmark expansion, ablations with uncertainty, and the final demonstration are still open.

## 5. Roadmap status

| Phase | Status | Evidence |
|---|---|---|
| 01 Repository setup and audit | Done | This document; `npm run lint`, `npm run build`, `npm run check:api`, `pytest`. |
| 02 Core application and database | Largely done | CRUD, validation, error responses and restart persistence tested (`backend/tests/test_memory_crud.py`). Concurrency tests not yet written. |
| 03 Temporal knowledge graph | Largely done | Point-in-time queries (`facts_as_of`, half-open interval), supersession with history, retraction, coexistence, source references. 10 tests in `backend/tests/test_temporal_graph.py`. Entity graph beyond a single user subject not done. |
| 04 Retrieval and adaptive scoring | Not started in this pass | Existing code; benchmark is deterministic but small. |
| 05 Contradiction and consolidation | Contradiction part done | 14 tests in `backend/tests/test_contradictions.py`. Same-date/different-time conflicts detected; hedged claims not recorded as conflicts; resolved conflicts preserved on re-scan; negation conflicts name the older memory. Consolidation (duplicates, paraphrase thresholds) not yet tested. |
| 06 Knowledge gaps and forgetting | Partly done | Forgetting paths covered by `backend/tests/test_forgetting_paths.py` and the hard-delete test. Gap-detection tests not written. |
| 07 Desktop integration | Partly done | Memories screen now creates, edits and deletes through the backend. Graph, timeline, conflicts, consolidation and evaluation screens not audited. |
| 08 Benchmarking | Not started in this pass | Existing benchmark reproduces; needs a larger dataset and ablations. |
| 09 Final checks and submission | Not started | — |

## 6. How to reproduce this baseline

```bash
# Frontend
ELECTRON_SKIP_BINARY_DOWNLOAD=1 npm ci   # the env var is only needed where Electron's download host is blocked
npm run lint
npm run build
npm run check:api

# Backend (Linux sandboxes may need: pip install opencv-python-headless==4.10.0.84)
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
python scripts/run_bench.py
```
