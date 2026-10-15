# Second Brain

A desktop personal-knowledge assistant built around the research layer of the
companion IEEE paper: *An Adaptive Temporal Personal Knowledge Graph with
Memory Consolidation and Contradiction-Aware Retrieval-Augmented Generation*.

The app keeps exactly the components the paper describes or evaluates:

- **Capture / ingest** - screen OCR, mail (IMAP / Gmail OAuth), web and social
  ingestion into one SQLite memory store.
- **Memory + retrieval** - semantic chunking, embeddings, hybrid dense +
  keyword retrieval, the RAG answer pipeline.
- **The seven research components** - Adaptive Memory Scoring, Temporal
  Personal Knowledge Graph, Contradiction-Aware Hybrid Retrieval, Memory
  Consolidation, Knowledge-Gap Detection, retrieval-enforced Forgetting, and
  PersonalBrain-Bench. Each is additive and individually switchable.
- **Voice** - wake word, streaming microphone, spoken replies.
- **Desktop shell** - Electron + React + Tailwind.

Features that never appeared in the paper (calendar, tasks, reminders,
automations, notifications centre, activity tracking, vault cards / wiki /
deliverables, recommendation and translation layers, pitch UI) have been
removed so that every remaining component supports a claim in the paper.

## Stack

Electron, React, JavaScript, TailwindCSS, React Router, Context API,
Python, FastAPI, SQLite, SQLAlchemy, WebSockets, JWT auth, OpenCV, mss,
pyautogui, psutil, watchdog, ChromaDB, Sentence Transformers, LangChain.

## Run

```bash
npm install
npm run dev
```

Backend setup:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
copy .env.example .env        # or: cp .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

OCR setup:

```text
Install the Tesseract desktop app and add it to PATH.
Install English and Tamil language data for best results.
Optional PaddleOCR fallback: pip install -r requirements-ocr-optional.txt
```

Semantic memory setup:

```bash
cd backend
pip install -r requirements-semantic.txt
```

## Tests and checks

```bash
npm run lint && npm run build && npm run check:api   # frontend
cd backend && python -m pytest -q                    # backend (uses a temp database)
```

The neural NLI tests are skipped, with a reason printed, when the optional
model is not installed. See `docs/BASELINE.md` for the audit, the defects
fixed, and the open items.

## Research layer and benchmark

The Memory Lab page (`/memory-lab`) demonstrates every mechanism and runs the
benchmark from the UI. The same benchmark runs head-less:

```bash
cd backend
python scripts/run_bench.py            # single user, four pipelines
python scripts/run_multi_user_bench.py # five personas, paired statistics
```

`run_bench.py` resets derived research state, ingests the synthetic
PersonalBrain-Bench corpus, evaluates vanilla / hybrid / graph / adaptive at
k = 5 and writes `backend/benchmark_results.json`. Two consecutive executions
produce identical metrics (latency excepted).

## Workspace map

```text
backend/app/research/     the seven components + PersonalBrain-Bench
backend/app/retrieval/    hybrid dense + keyword retrieval
backend/app/memory/       memory store, archive, error handling
backend/app/capture/      screenshot service feeding the OCR worker
backend/app/ocr/          Tesseract / PaddleOCR pipelines
backend/app/integrations/ IMAP mail, Google OAuth, wake word, token store
backend/app/voice/        speech I/O orchestration
src/pages/                dashboard, chat, mail, knowledge, memory lab,
                          integrations, voice, settings
electron/                 desktop shell (main + preload)
docs/                     IEEE paper (Typst / PDF / DOCX) and diagrams
```

## Accounts

The backend seeds a demo user on first start (see `backend/.env.example` for
the credentials). Mail connections are read-only: nothing here sends,
deletes or modifies remote data.
