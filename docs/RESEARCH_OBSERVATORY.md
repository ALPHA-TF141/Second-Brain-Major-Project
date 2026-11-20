# Research Observatory — measurements before application features

The default route (`#/`) now opens the research workspace. The previous dashboard remains at `#/workspace`, and `#/memory-lab` retains pipeline controls. App startup no longer silently starts screen capture. The React/Electron application is preserved.

## Three evidence classes (never mixed)

1. **Paper reference:** Table II values transcribed from the supplied `Ieee_paper_Final8.pdf`, rounded as published. These are constants, never inserted into measured fields.
2. **Recorded artifacts:** existing repository JSON for core, five personas, ablations, scaling, statistics, conflict development and holdout. Marked historical, not freshly executed. The explorer exposes every numeric leaf by exact JSON path and the complete raw artifact.
3. **Measured runs / live state:** actual code execution, with configuration, denominator calculations and provenance. Exportable JSON and saved run history.

A small difference between a four-decimal measured value and a three-decimal paper target can be rounding, not a changed experimental outcome. This is visible rather than silently rounded away.

## IEEE benchmark tab

**Run core experiment** runs all five existing modes (`vanilla`, `hybrid`, `graph`, `adaptive`, `adaptive_graph`) at k=5 using the real repository benchmark and TF-IDF implementation.

Safety: `BenchmarkRunner.load_corpus(reset=True)` clears derived rows. The Observatory therefore never supplies the live database to it. It launches `app.research.observatory_worker` in a new process with a fresh temporary SQLite file and temporary working directory. Only the resulting synthetic JSON is stored in the live `research_runs` table (`kind=observatory`). Locking rejects a second run in the same server process; child timeout is 300 seconds. Run one API worker locally. This is not a distributed job queue.

The API's child is offline for HuggingFace; it uses optional models already cached locally, or records fallback availability/errors. It does not silently download new models to chase reference numbers.

### Calculation ledger

| Metric | Numerator | Denominator |
|---|---|---|
| Hit@5 | answerable questions with any gold result | answerable questions |
| MRR | sum of reciprocal first-gold ranks (0 for misses) | answerable questions |
| stale@1 | queries whose first result is in that query's forbidden set | all questions |
| forgotten leakage | forgotten items returned | all returned items |
| v1 duplicate rate | within-query pairs with term-frequency cosine >= .90 | all returned items, **not pairs** |
| evidence recall | sum of per-query unique-gold coverage fractions | answerable questions |
| staleness rate | forbidden items returned | all returned items |
| mean context characters | content characters returned | all questions |

Empty denominators are displayed as undefined, not falsely perfect or zero. The ledger reconciles with the runner's rounded output. Evidence recall preserves the existing runner's per-query rounding for reconciliation; the newly added `evidence_recall_exact` field exposes the unrounded fraction separately. Older artifacts without duplicate-pair counts cannot reconstruct that numerator: the UI says to rerun instead of inferring it from a rounded rate.

Each question now records gold/forbidden keys, ranks, returned scores, forgotten flags, duplicate-pair counts and a deep copy of the actual pipeline trace. Traces include lexical candidate scores, hybrid fusion, graph outputs, input ranks, importance factors, damping products and dedup decisions. Algorithm internals not emitted by the pipeline are not fabricated.

**Fixed an existing reporting defect:** non-vanilla retrieval used to return a constant score of `0.0` despite ranking with real values. It now returns the hybrid/graph/adaptive score actually used. Candidate ordering and metric formulas are unchanged.

Run provenance includes the Python/package versions, source SHA-256, Git revision/dirty state, graph extractor, NLI availability/error, evaluated clock, and deletion-policy caveat. An available model is not proof its weights equal the paper artifact; the existing loader does not pin that revision, and this is disclosed.

## Live calculations tab

- Read-only snapshots, polled every five seconds while the page is visible and on focus/manual refresh.
- SHA-256-derived revision changes on edits and derived-record updates even when counts stay constant.
- Session-only sampled change log. It can combine multiple operations between polls. It is **not** a durable every-operation event stream.
- Corpus counts, tombstones, persisted scores, temporal facts, conflicts, consolidation groups, graph nodes/edges and gap rows.
- All active memories are rescored in memory at the sample clock, using the existing `AdaptiveMemoryScorer`. Nothing is written by a GET.
- Every scoring component displays its value, signed weight, contribution, definition, summation, clipping, age/recency, stored score, recalculated delta, and exact input dictionaries in the JSON inspector. Values are corpus-relative and heuristic, not learned predictions.
- Live query probe reuses the real retrieval code. Submit a query once and it reruns on each observed database revision. It shows the actual returned ranking score and the full pipeline trace. All probe modes exclude tombstones; this deliberately differs from the original benchmark's baseline deletion policy.
- The query probe uses existing persisted research annotations. If a score/graph/conflict extraction operation has not run, the dashboard exposes that absence rather than inventing derived records. Recalculated importance is displayed separately from stored importance used by retrieval.
- Temporal intervals and source-active flags; severity-to-damping arithmetic; consolidation before/after counts and reduction fractions; gap formula expanded from stored rounded inputs.

There is **no live MRR or accuracy** without gold query labels. Changing personal notes cannot legitimately change the fixed synthetic benchmark's accuracy. Run that experiment to measure the benchmark; use the live probe to observe outcomes on personal notes.

Graph mean degree is `2E/N` over all stored node/edge types, not a causal retrieval benefit. Gap suggestions remain unvalidated heuristics. Derived facts/conflicts/gaps are the latest persisted operations and may lag raw ingestion. State is sampled, not an atomic transaction with concurrent ingestion.

## Research-only run profile (recommended)

Use Python 3.11–3.13. From repository root:

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux / macOS: source .venv/bin/activate
pip install -r requirements-research.txt
python -m uvicorn app.research_main:app --host 127.0.0.1 --port 8000
```

In another terminal, from repository root:

```bash
npm ci
npm run dev:react
```

Open http://localhost:5173. The research profile exposes auth, memory CRUD, research controls and the Observatory, with **no OCR/capture workers, voice, automatic mail ingestion or fabricated connector seeding**. Legacy application-only pages may call routes unavailable in this profile; use `app.main:app` and the original full dependency packs for those features.

The profile uses the configured application SQLite path by default. To use a separate database, set `DATABASE_URL` before starting (PowerShell `$env:DATABASE_URL='sqlite:///./data/research.db'`; shell `export DATABASE_URL=sqlite:///./data/research.db`). No copy of the tracked root database is needed.

Browser API calls are same-origin through Vite's `/api` and `/ws` proxies. Override `SECONDBRAIN_BACKEND_TARGET` for a non-default backend port. Electron's file:// build still defaults to the local API. A deployed web build needs an equivalent reverse proxy or explicit `VITE_API_URL`.

## Scope and remaining research work

- Core suite is rerunnable from this module. Persona, ablation, scaling, bootstrap and conflict-suite artifacts are inspectable/exportable but are not rerun by the core button.
- The old `/api/research/benchmark` and `/benchmark/multi-user` routes and CLI runners still have legacy reset behaviour. Use the **Observatory run button**, not those old runners against personal data. Full migration is a follow-up.
- No code is tuned to force a match to the paper. Optional spaCy/ONNX paths must be installed/cached and independently verified before claiming a neural reproduction.
- Original baseline/adaptive forgetting policies differ. The core result table is not an equal-deletion-policy retrieval comparison.
- Local authenticated research profile, not hardened multi-tenant hosting. Existing global corpus scoping and demo authentication remain; do not expose it publicly or put sensitive data in the preview.
- Existing tracked database/vault files were not copied, published in new artifacts, or removed from Git history by this change. A separate privacy cleanup remains necessary.

## Validation

```bash
npm run check
cd backend
python -m pytest tests/test_observatory.py tests/test_temporal_graph.py tests/test_contradictions.py tests/test_neural_research.py -q
```

The optional neural tests skip with a reason when models are absent; skips are not passes.

Browser smoke (requires Playwright + Chromium and running API/Vite, with a **throwaway** DB):

```bash
npm install --no-save --package-lock=false playwright
npx playwright install --with-deps chromium
node scripts/observatory_smoke.mjs
```

It checks the real page, executes a core run, creates a synthetic note, observes its live score, opens the artifact explorer, and checks no uncaught page exception or automatic capture request. Screenshots go under ignored `artifacts/observatory/`.
