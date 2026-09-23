# System Architecture Diagram

Files in this folder, all generated from one source so they cannot drift apart:

| File | Use |
|---|---|
| `system_architecture.svg` | Vector master. Infinite zoom, edits cleanly in Inkscape / Illustrator / draw.io. Best quality for a report or print. |
| `system_architecture.png` | 2600 × 1960 raster (2× for retina). Drop straight into Word, PowerPoint or a poster. |
| `system_architecture.pdf` | Single page, vector. For LaTeX (`\includegraphics`) or a print pipeline. |

## What it shows

Seven tiers, top to bottom:

1. **Client** — Electron shell: React UI (24 pages / 20 routes), the floating
   always-on-top JARVIS orb window, the `main`+`preload` IPC bridge, browser
   speech synthesis/recognition in the renderer, and the two context providers.
2. **API layer** — FastAPI: REST (`/api/*`, 150 paths / 162 operations across 20
   route modules), the three WebSocket channels (`/ws/live`, `/ws/voice`,
   `/ws/chat`), JWT authentication, and the asyncio background loops.
3. **Capture & ingestion** — every source (screen OCR, IMAP, Google OAuth, iCal,
   web/social, voice via VAD+STT, clipboard, file watchers) and the normalisation
   step that writes a memory row plus its search-index row.
4. **Research layer** — the seven components C1–C7 from the paper, drawn as one
   distinct band because it is the contribution under evaluation.
5. **Proactive / hands-free** — wake word, the proactive voice policy, the
   turn-based microphone loop, and the shutdown path.
6. **Retrieval & generation** — the four switchable pipelines, fusion and
   ranking, context assembly, and the provider-agnostic LLM client.
7. **Persistence** — the six stores: SQLite (49 tables), search index, vector
   store, git-backed memory vault, encrypted credential store.

`External dependencies` lists what leaves the machine: Google APIs, IMAP,
iCal, GitHub (vault sync) and the local Ollama model.

## Line conventions

- **Solid arrow** = synchronous call in the request path.
- **Dashed arrow** = background work or an outbound network call.

## Note on accuracy

Every component name and count in the diagram was read from the source tree
(`backend/app/routes`, `app.main`'s OpenAPI schema, `sqlite_master`,
`src/pages`, `electron/*.js`), not from memory.

Two claims were removed during checking because the code does not support them,
and they are worth recording so they are not re-introduced:

- An earlier draft described the card/wiki curation agents as "LLM-assisted".
  They are rule-based text assembly, so the wording was corrected to
  *deterministic text from memory*.
- An earlier draft claimed the proactive voice never announces forgotten
  content. `app/agents/proactive_voice.py` has no notion of forgetting — its
  policy is only a priority gate, quiet hours and a dedupe window. The claim was
  removed rather than left in as an aspiration.

The API count is the generated OpenAPI schema's own figure (150 paths, 162
operations). An earlier project write-up quoted 162 endpoints over 150 paths,
which is the same measurement described the other way round.
