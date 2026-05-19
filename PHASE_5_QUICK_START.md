# Phase 5: Quick Start Guide

## What is Phase 5?

Phase 5 transforms your captured screenshots and OCR text into a **searchable digital memory archive** with intelligent session reconstruction and chronological timelines.

---

## System Architecture

```
Screenshot Capture
    ↓
OCR Processing
    ↓
Text Extraction & Chunking
    ↓
MEMORY ARCHIVE (Phase 5)
    ├── Create Memory objects
    ├── Auto-tag with keywords
    ├── Categorize (coding/learning/research/browsing)
    └── Build cross-session relationships
    ↓
Timeline Display & Search
    ↓
Searchable Memory Feed
```

---

## Getting Started

### 1. Start the System

```bash
# Terminal 1: Start backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Start frontend
cd .
npm run dev
```

### 2. Access the UI

1. Open http://localhost:5173 in your browser
2. Click "Timeline" in the sidebar
3. You'll see the Memory Timeline page

### 3. Populate Memory System

```bash
# In Terminal 2 (another shell):

# 1. Start capturing screenshots
curl -X POST http://localhost:8000/api/capture/start

# 2. Do some work (or wait ~30 seconds)

# 3. Stop capture
curl -X POST http://localhost:8000/api/capture/stop

# 4. Process OCR (extract text from screenshots)
curl -X POST http://localhost:8000/api/ocr/queue-unprocessed

# 5. Rebuild memory archive (IMPORTANT!)
curl -X POST http://localhost:8000/api/memory/rebuild

# 6. Refresh your browser to see memories
```

---

## Phase 5 Features

### 1. Memory Timeline

**Location:** Timeline.jsx

A three-column interface showing:

- **Left Column**: Reconstructed sessions with summaries
- **Center Column**: Memory feed (day/week grouped)
- **Right Column**: Memory detail with screenshot, tags, content

**Actions:**
- Search memories with keywords
- Filter by topic, app, source type
- Group by day or week
- Click memory to view detail
- Export session to Markdown

### 2. Memory Organization

**Automatic Session Creation:**

Sessions are grouped by activity type:
- **Coding** - VSCode, terminals, code snippets
- **Learning** - Tutorials, courses, documentation
- **Research** - Articles, papers, analysis
- **Browsing** - Web pages, YouTube, social media
- **Clipboard** - Copied content

**Each Session Shows:**
- Title (auto-generated from topics)
- Summary (time, apps used, topics covered)
- Memory count
- Screenshot count
- Session type

### 3. Memory Search

**Search Operators:**

```
# Full-text search
?q=python ocr

# Filter by app
?app=VSCode

# Filter by source
?source_type=screen
?source_type=code
?source_type=youtube
?source_type=clipboard

# Filter by topic
?topic=Python

# Filter by date
?date=2024-05-15

# Filter by session
?session_id=42

# Combine filters
?q=python&app=VSCode&date=2024-05-15
```

**Search Results:**
- Ranked by relevance (exact matches first)
- Recently modified get priority
- Filter-specific matches boosted

### 4. Memory Tagging

**Automatic Tags Generated From:**
- Content keywords
- Detected topics
- Application name
- Source type

**Example:**
```
Content: "Python OCR with Tesseract"
Source: VSCode
Topic: OCR

Generated Tags:
[Python] [OCR] [Tesseract] [VSCode] [Code]
```

### 5. Related Memories

**Automatic Relationships:**
- Same topic (strongest)
- Same category
- Same application
- Same time window (24 hours)

**Use:** Click a memory to see related memories nearby

### 6. Session Summaries

**Auto-Generated For Each Session:**

```
"User spent 45 minutes in a coding session using 
VSCode and Chrome, focused on Python OCR and 
Tesseract implementation."

Session Type: coding
Dominant Apps: VSCode, Chrome, Tesseract
Topics: Python, OCR, Image Processing
Memory Count: 23
Screenshot Count: 45
```

### 7. Export System

**Export Memories as Markdown:**

```bash
# Via URL (browser)
GET http://localhost:8000/api/memory/export/session/42?token=YOUR_TOKEN

# Via API
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/memory/export/session/42 \
  > session-42.md
```

**Exported Format:**
```markdown
# Session Title

Session summary here...

Type: coding
Apps: VSCode, Chrome
Topics: Python, OCR

## Memory 1 Title

Content of memory 1...

## Memory 2 Title

Content of memory 2...
```

---

## Key Concepts

### Memory

A single piece of information captured from the system:
- Origin: Screenshot, OCR chunk, clipboard, app usage
- Content: Text from screen capture or clipboard
- Metadata: Timestamp, app, source, topic, tags
- Hash: SHA1 of content (prevents duplicates)

### Session

A logical grouping of related activities:
- Automatically created and categorized
- Time-bounded (start → end)
- Contains multiple memories
- Has a summary (title + description)

### Relationship

A link between two memories indicating relevance:
- Same topic (strongest: 85/100)
- Same category (65/100)
- Same app (55/100)
- Cross-session same topic (75/100)
- Cross-session same category (50/100)

### Timeline

Chronological organization of memories:
- Can group by day or week
- Can filter by any field
- Sticky headers for date grouping
- Scrollable feed

---

## Database Schema

### Core Tables

```
memories
├── id (PK)
├── session_id (FK)
├── screenshot_id (FK, nullable)
├── semantic_chunk_id (FK, nullable)
├── title, content
├── content_hash (unique, dedup)
├── source_type (screen/code/youtube/clipboard)
├── app_source
├── topic_label
├── category (coding/learning/research/browsing)
└── created_at

memory_tags
├── id (PK)
├── memory_id (FK)
└── tag

session_summaries
├── id (PK)
├── session_id (FK, unique)
├── title
├── summary
├── session_type
├── dominant_apps
├── detected_topics
├── memory_count
├── screenshot_count
└── started_at, ended_at

memory_relationships
├── id (PK)
├── source_memory_id (FK)
├── target_memory_id (FK)
├── relationship_type
└── strength (0-100)

search_index
├── id (PK)
├── memory_id (FK, unique)
├── searchable_text (full-text indexed)
├── tags_text
├── app_source
├── source_type
├── topic_label
└── created_at
```

---

## API Reference

### Search Memories

```bash
GET /api/memory/search \
  ?q=text \
  &source_type=screen \
  &topic=Python \
  &app=VSCode \
  &date=2024-05-15

Response: [{ id, title, content, tags, category, created_at, ... }]
```

### Get Timeline

```bash
GET /api/memory/timeline \
  ?group=day \
  &q=text \
  &source_type=screen

Response: [{ label: "2024-05-15", memories: [...] }, ...]
```

### List Sessions

```bash
GET /api/memory/sessions

Response: [{ id, title, summary, session_type, memory_count, ... }]
```

### Get Memory Detail

```bash
GET /api/memory/memories/42

Response: { id, title, content, tags, screenshot_id, relationships, ... }
```

### Get Related Memories

```bash
GET /api/memory/memories/42/related

Response: [{ id, title, content, tags, ... }]
```

### Rebuild Archive

```bash
POST /api/memory/rebuild

Response: { sessions: 5, memories: 42 }
```

---

## Common Workflows

### Workflow 1: Capture and Reconstruct

```bash
# 1. Start capturing (5-second screenshot interval)
curl -X POST http://localhost:8000/api/capture/start

# 2. Work for a while (5-10 minutes)

# 3. Stop capture
curl -X POST http://localhost:8000/api/capture/stop

# 4. Extract text with OCR
curl -X POST http://localhost:8000/api/ocr/queue-unprocessed

# 5. Rebuild memory archive
curl -X POST http://localhost:8000/api/memory/rebuild

# 6. View timeline (browser at http://localhost:5173)
```

### Workflow 2: Search and Find

```bash
# Search all memories about Python
GET /api/memory/search?q=python

# Search VSCode memories
GET /api/memory/search?app=VSCode

# Search today's memories
GET /api/memory/search?date=2024-05-15

# Search this week's coding session
GET /api/memory/search?q=coding&source_type=screen

# Get related memories to memory #42
GET /api/memory/memories/42/related
```

### Workflow 3: Analyze Sessions

```bash
# List all sessions
GET /api/memory/sessions

# Get session #5 details
GET /api/memory/sessions/5

# Get all memories in session #5
GET /api/memory/sessions/5/memories

# Export session #5 as Markdown
GET /api/memory/export/session/5?token=YOUR_TOKEN
```

### Workflow 4: View Timeline

1. Open http://localhost:5173/timeline
2. Use search box to find memories
3. Use filters (topic, app, source, date)
4. Switch between daily/weekly grouping
5. Click memory to view details
6. Click session to see all memories in session
7. Click "Export Session" to download as Markdown

---

## Performance Tips

1. **Rebuild Archive Regularly**: After processing new OCR
2. **Use Specific Filters**: Narrow down search before text search
3. **Export Large Sessions**: Avoid loading thousands of memories at once
4. **Check Memory Stats**: `GET /api/memory/stats` to see system size

---

## Troubleshooting

### No Memories Appearing?

1. Check capture is running: `GET /api/capture/status`
2. Process OCR: `POST /api/ocr/queue-unprocessed`
3. Rebuild archive: `POST /api/memory/rebuild`
4. Check database: `SELECT COUNT(*) FROM memories`

### Search Returns Nothing?

1. Verify memories exist: `SELECT COUNT(*) FROM memories`
2. Check searchable_text is populated: `SELECT COUNT(*) FROM search_index`
3. Rebuild archive: `POST /api/memory/rebuild`

### Sessions Not Grouping Correctly?

1. Check SessionSummary exists: `SELECT COUNT(*) FROM session_summaries`
2. Rebuild session: `POST /api/memory/sessions/{id}/rebuild`
3. Check app detection: `SELECT DISTINCT app_source FROM memories`

---

## What's Next?

Phase 5 is **memory storage and organization**. Future phases:

- **Phase 6**: Semantic search with embeddings and vector database
- **Phase 7**: AI-powered reasoning agents and insights
- **Phase 8**: Voice assistant and natural language interface

---

## Summary

Phase 5 provides:
- ✅ Permanent memory storage
- ✅ Automatic session reconstruction
- ✅ Chronological timelines
- ✅ Full-text search with ranking
- ✅ Smart tagging and categorization
- ✅ Related memory discovery
- ✅ Session export
- ✅ Frontend timeline UI

Your digital memory is now organized, searchable, and ready for semantic capabilities!
