# Second Brain

Phase 1 through Phase 8 foundation for a beginner-friendly desktop AI assistant.

## Stack

- Electron
- React
- JavaScript
- TailwindCSS
- React Router
- Context API
- Python
- FastAPI
- SQLite
- SQLAlchemy
- WebSockets
- JWT auth
- OpenCV
- mss
- pyautogui
- psutil
- watchdog
- ChromaDB
- Sentence Transformers
- LangChain

## Run

```bash
npm install
npm run dev
```

Backend setup:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
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

The first semantic indexing run downloads `all-MiniLM-L6-v2` through Sentence Transformers.
On Windows, ChromaDB may require Microsoft C++ Build Tools for `chroma-hnswlib`, especially on newer Python versions. A Python 3.11 or 3.12 virtual environment is recommended for the semantic stack.

RAG chat setup:

```bash
cd backend
pip install -r requirements-rag.txt
```

Optional `.env` values:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
RAG_CONTEXT_LIMIT=8
```

Without `OPENAI_API_KEY`, the chat assistant uses a local extractive fallback based on retrieved memories.

Voice setup:

```bash
cd backend
pip install -r requirements-voice.txt
```

Voice dependencies are optional because Whisper and Coqui TTS are heavy native AI packages. Without them, the frontend still supports browser microphone capture, browser speech recognition where available, manual transcript fallback, backend voice sessions, Tamil-aware routing, RAG responses, and browser speech synthesis.

The frontend expects the backend at `http://127.0.0.1:8000`.
Demo login:

```text
username: demo
password: secondbrain
```

## Structure

```text
electron/
  main.js
  preload.js
backend/
  app/
    auth/
    database/
    models/
    routes/
    schemas/
    services/
    capture/
    chunking/
    extraction/
    metadata/
    memory/
    ocr/
    preprocessing/
    prompts/
    rag/
    search/
    semantic_search/
    summarization/
    tagging/
    timeline/
    vectorstore/
    workers/
    llm/
    streaming/
    audio_streaming/
    stt/
    tts/
    translation/
    vad/
    voice/
    wakeword/
    tracking/
    utils/
    websocket/
    main.py
src/
  assets/
  components/
  context/
  hooks/
  layouts/
  pages/
  routes/
  styles/
```

## Current Scope

The desktop shell includes:

- Frameless Electron window
- Secure preload IPC bridge
- Sidebar and top navbar
- Dashboard, chat, timeline, activity, voice, and settings pages
- Fake assistant status, listening status, notifications, and floating assistant button
- Backend connection status UI
- Frontend API service layer
- Frontend WebSocket client

The backend includes:

- FastAPI server
- SQLite database setup
- SQLAlchemy models for users, sessions, activities, timeline events, and settings
- JWT login/logout
- Activity, timeline, settings, sessions, and health APIs
- WebSocket endpoint at `/ws/live`
- Manual live memory capture with screenshots, active window tracking, clipboard tracking, file activity tracking, and privacy exclusions
- OCR processing pipeline with image preprocessing, text cleaning, topic detection, semantic chunks, and processed session knowledge
- Structured memory archive with searchable memories, tags, session summaries, timeline grouping, relationships, and Markdown export
- Semantic vector memory engine with embeddings, ChromaDB indexing, hybrid search, related memories, clusters, and context assembly
- Conversational RAG memory assistant with contextual retrieval, prompt assembly, streaming responses, conversation history, modes, and citations
- Realtime voice assistant with microphone streaming, Tamil-English transcripts, wake words, command routing, memory-aware answers, and spoken browser fallback

## Useful API Endpoints

```text
GET  /api/health
POST /api/auth/login
POST /api/auth/logout
POST /api/sessions
POST /api/activities
GET  /api/activities
GET  /api/timeline
PUT  /api/settings
POST /api/capture/start
POST /api/capture/pause
POST /api/capture/resume
POST /api/capture/stop
GET  /api/capture/status
GET  /api/capture/activity
GET  /api/capture/screenshots
GET  /api/capture/sessions
GET  /api/ocr/status
POST /api/ocr/queue-unprocessed
POST /api/ocr/screenshots/{screenshot_id}/process
POST /api/ocr/sessions/{session_id}/process
GET  /api/ocr/texts
GET  /api/ocr/chunks
GET  /api/ocr/topics
GET  /api/ocr/sessions
POST /api/memory/rebuild
POST /api/memory/sessions/{session_id}/rebuild
GET  /api/memory/search
GET  /api/memory/timeline
GET  /api/memory/memories/{memory_id}
GET  /api/memory/memories/{memory_id}/relationships
GET  /api/memory/sessions
GET  /api/memory/sessions/{session_id}
GET  /api/memory/sessions/{session_id}/memories
GET  /api/memory/export/session/{session_id}
GET  /api/semantic/status
POST /api/semantic/index
POST /api/semantic/reindex
POST /api/semantic/search
POST /api/semantic/hybrid-search
GET  /api/semantic/related/{memory_id}
POST /api/semantic/context
POST /api/semantic/relationships/detect
POST /api/semantic/clusters/rebuild
GET  /api/semantic/clusters
GET  /api/semantic/jobs
GET  /api/semantic/history
GET  /api/chat/conversations
GET  /api/chat/conversations/{conversation_id}/messages
GET  /api/chat/conversations/{conversation_id}/retrieved
POST /api/chat/ask
GET  /api/voice/status
POST /api/voice/sessions
POST /api/voice/sessions/{session_id}/stop
GET  /api/voice/sessions
GET  /api/voice/sessions/{session_id}/transcripts
GET  /api/voice/preferences
PUT  /api/voice/preferences
GET  /api/voice/audio/{audio_id}
GET  /ws/live?token=JWT_TOKEN
GET  /ws/chat?token=JWT_TOKEN
GET  /ws/voice?token=JWT_TOKEN
```

## Phase 4 OCR Notes

OCR converts captured screenshots into structured knowledge:

- Preprocesses images with grayscale, denoising, contrast enhancement, sharpening, and thresholding
- Uses Tesseract through `pytesseract` for English and Tamil text
- Keeps PaddleOCR as an optional fallback adapter
- Cleans duplicate/noisy UI text
- Splits content into semantic chunks such as code, article, document, YouTube, and screen notes
- Stores extracted text, chunks, topics, OCR metadata, and processed session summaries in SQLite

The Python package `pytesseract` is only a wrapper. The native `tesseract` executable must also be installed on the machine.

## Phase 5 Memory Archive Notes

The memory archive converts OCR chunks and captured activity into permanent searchable records:

- `memories` stores deduplicated OCR chunks and clipboard memories
- `memory_tags` stores automatic keyword/category/source tags
- `session_summaries` stores reconstructed coding, learning, research, browsing, and study sessions
- `memory_relationships` links nearby memories with shared topics or categories
- `search_index` stores plain keyword-search text for fast retrieval

Open the Timeline page and use **Rebuild Archive** after OCR processing. The page includes search, filters, grouped sessions, expandable memory cards, screenshot previews, and session export.

## Phase 6 Semantic Memory Notes

The semantic engine converts structured memories into vector memories:

- Generates embeddings with `sentence-transformers/all-MiniLM-L6-v2`
- Stores vectors persistently in ChromaDB under `backend/data/chroma/`
- Tracks indexing in `vector_memories` and `embedding_jobs`
- Records semantic search usage in `search_history`
- Builds repeated-topic clusters in `memory_clusters`
- Stores semantic similarity links in `semantic_relationships`
- Provides hybrid search by combining keyword memory search with semantic vector similarity

Workflow:

1. Capture activity in Live Activity.
2. Process screenshots in OCR Knowledge.
3. Rebuild the archive in Timeline.
4. Install semantic dependencies.
5. Open Semantic Memory and click **Index**.
6. Search by meaning, inspect related memories, then click **Cluster** to group recurring concepts.

## Phase 7 RAG Chat Notes

The AI Chat page is now a memory-aware assistant:

- Retrieves relevant memories through the hybrid semantic search layer
- Builds compact prompts with conversation history and memory citations
- Streams responses over `/ws/chat`
- Stores conversations, messages, retrieved memory citations, context, summaries, and feedback-ready rows
- Supports summary, detailed, timeline, teaching, and coding response modes
- Uses OpenAI when configured, with a local fallback when no API key is available

Suggested flow:

1. Capture activity.
2. Process OCR.
3. Rebuild the memory archive.
4. Index semantic memories.
5. Open AI Chat and ask questions like `What was I studying yesterday?`.

## Phase 8 Voice Assistant Notes

The Voice Assistant page is now a realtime voice interface:

- Streams microphone chunks to `/ws/voice`
- Uses browser speech recognition for low-latency English/Tamil transcript events when available
- Stores voice sessions, transcripts, commands, audio metadata, and language preferences
- Supports continuous, push-to-talk, and wake-word modes
- Supports wake phrases like `Second Brain` and `Hey Brain`
- Detects Tamil text and adds Tamil/mixed-language response instructions to the RAG assistant
- Uses Coqui TTS when installed and browser speech synthesis as a fallback
- Routes voice commands such as start capture, stop recording, timeline, AI chat, and search

Suggested Tamil test:

```text
நேற்று நான் என்ன படித்தேன்?
```

## Phase 3 Capture Notes

Capture is manual only. Open the Live Activity page, login with the demo account if needed, then press Start. Screenshots are stored locally under `backend/data/screenshots/` and metadata is stored in SQLite.

Privacy defaults:

- Capture starts only from the UI or authenticated API call
- Pause and Stop are supported
- Sensitive app names can be excluded
- Browser tab titles are detected from the active window title only
- Browser history scraping, OCR, embeddings, and AI understanding are not implemented in this phase

## Testing

Start the backend and visit:

```text
http://127.0.0.1:8000/docs
```

Future phases can add real AI memory, voice, OCR, RAG, semantic search, and Tamil interaction.
