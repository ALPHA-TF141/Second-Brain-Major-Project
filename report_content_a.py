"""Development report - front matter and Parts I-III (vision, architecture, chronology)."""
from datetime import datetime

from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, Spacer
from reportlab.platypus.tableofcontents import TableOfContents

from report_builder_base import ACCENT, BODY_W, B, P, S, Section, Sub, callout, code, esc, table

W = BODY_W


def build():
    f = []

    # ==================================================================== COVER
    f.append(Spacer(1, 90))
    f.append(Paragraph("SecondBrain", S["title"]))
    f.append(Paragraph(
        "A Personal AI Operating System with Adaptive Temporal Memory",
        S["subtitle"]))
    f.append(Spacer(1, 16))
    f.append(Paragraph(
        "Complete Development Report<br/>"
        "Conception, architecture, every deviation, every defect, and the research contribution",
        S["subtitle"]))
    f.append(Spacer(1, 60))

    cover = [
        ["Project", "SecondBrain \u2014 Autonomous Personal Cognitive Knowledge Synthesizer"],
        ["Repository", "github.com/ALPHA-TF141/Second-Brain-Major-Project"],
        ["Supervisor", "Dr. P S Anu Rakhi, Assistant Professor, School of Computing"],
        ["Authors", "Maria Immanuel L \u00b7 Vigneshwaran S, B.Tech Computer Science and Engineering"],
        ["Institution", "Vel Tech Rangarajan Dr. Sagunthala R&D Institute of Science and Technology"],
        ["Report compiled", datetime_stamp()],
        ["Code volume", "17,149 lines Python \u00b7 12,449 lines JavaScript/JSX"],
        ["Database", "49 tables \u00b7 SQLite + optional vector store"],
        ["Commits", "231 total (69 substantive, 162 automated vault synchronisations)"],
        ["Verification", "15 automated gates \u00b7 8 test suites \u00b7 0 server errors across every route"],
    ]
    t = table([[Paragraph(f"<b>{k}</b>", S["tabc"]), Paragraph(esc(v), S["tabc"])] for k, v in cover],
              [95, W - 95], header=False)
    f.extend(t)
    f.append(PageBreak())

    # ============================================================ EXEC SUMMARY
    f.append(Section("Executive Summary"))
    f.append(P(
        "SecondBrain began as a straightforward question: <i>can a personal computer be made to "
        "remember, and reason over, everything its owner reads, writes and is told?</i> The answer "
        "turned out to be yes, but not in the way the question implies. Storing information is easy. "
        "The engineering difficulty lies in deciding what is worth keeping, recognising when new "
        "information contradicts old, and ensuring that what the user has asked to forget stays "
        "forgotten. Those three problems became the intellectual core of the project."))
    f.append(P(
        "The system was built in seven phases over approximately six weeks. It captures screen "
        "activity through OCR, ingests email and calendar data from three accounts, compiles a "
        "self-improving wiki, maintains a knowledge graph, answers questions over the accumulated "
        "memory with a local language model, speaks and listens, and exposes all of this through a "
        "fifteen-tab desktop interface with a transparent floating assistant orb. It runs entirely on "
        "the authors' laptop, with no paid API and no data leaving the machine."))
    f.append(P(
        "The most significant development was not the accumulation of features but the recognition of "
        "a class of failure that conventional evaluation does not measure. A personal memory store "
        "accumulates contradictory statements as its owner changes their mind. It accumulates "
        "outdated facts whose validity has lapsed. It captures the same material repeatedly. And it "
        "is asked, sometimes explicitly, to forget. A standard retrieval pipeline treats all stored "
        "information as equally current evidence, so it can produce an answer that is confidently "
        "wrong while every retrieved passage remains faithful to its source. This report documents "
        "how that insight was reached, how seven architectural components were built to address it, "
        "and how the result was measured."))

    kpis = [
        ["Measure", "Result"],
        ["Memories ingested from real mail", "123 knowledge cards, growing automatically"],
        ["Wiki articles compiled", "93 articles across six domains"],
        ["Knowledge graph", "350 nodes, 500 edges"],
        ["Retrieval quality (personal benchmark)", "MRR 0.833 \u2192 1.000 versus dense baseline"],
        ["Answers leading with outdated facts", "36.4% \u2192 0.0%"],
        ["Forgotten content still returned", "Eliminated (all baselines still leak it)"],
        ["Benchmark reproducibility", "Two consecutive runs byte-identical"],
        ["Server errors across all 100+ routes", "Zero"],
    ]
    f.extend(table(kpis, [150, W - 150],
                   caption="Table 1 \u2014 Headline outcomes. Every figure is measured, not estimated."))

    f.extend(callout(
        "How to read this report",
        "Parts I to III are narrative: the idea, the architecture, and what was built in what order, "
        "including the reasoning at each step and every change of direction. Part IV explains the "
        "underlying theory, written so that a reader who knows none of the terminology can follow the "
        "design decisions. Part V is a register of deviations \u2014 every place the plan changed and "
        "why. Part VI is a register of defects with root causes. Part VII explains how the system is "
        "verified. Parts VIII and IX cover the research contribution and the current state. The "
        "appendices contain the raw history."))
    f.append(PageBreak())

    # ====================================================================== TOC
    f.append(Section("Contents"))
    toc = TableOfContents()
    toc.levelStyles = [S["toc1"], S["toc2"]]
    f.append(toc)
    f.append(PageBreak())

    # ================================================================ PART I
    f.append(Section("Part I \u2014 Vision and Problem", number=None))
    f.append(Spacer(1, 4))

    f.append(Sub("The original idea"))
    f.append(P(
        "The project started from a personal frustration rather than a research question. The author "
        "reads technical material constantly \u2014 documentation, papers, videos, lecture notes, email "
        "\u2014 and repeatedly encountered the same problem: <i>the information had been seen, but could "
        "not be recalled when it mattered.</i> The material existed somewhere, but not in a form that "
        "could answer a question months later."))
    f.append(P(
        "The first framing was therefore conventional: build a note-taking system with search. That "
        "framing was abandoned almost immediately, for a reason worth stating because it shaped "
        "everything that followed. A note-taking system requires the user to decide what to save, "
        "when to save it, and how to tag it. That decision-making is the very thing the user is bad "
        "at \u2014 if they were good at it, they would not have the problem. Any system whose value "
        "depends on disciplined manual curation will be abandoned within a fortnight."))
    f.append(P(
        "The reframed idea was that the system should capture automatically, decide for itself what "
        "matters, and be asked questions in plain language afterwards. The user should never have to "
        "perform a filing action. This is a much harder problem, because it moves the judgement from "
        "the human to the machine, and it means the quality of the system's judgement becomes the "
        "central engineering challenge."))

    f.append(Sub("What a \u201cSecond Brain\u201d means"))
    f.append(P(
        "The term comes from personal knowledge management (PKM), a body of practice concerned with "
        "how an individual captures, organises and retrieves their own information. Three established "
        "frameworks influenced the design and are worth naming, because the system implements a "
        "machine analogue of each."))
    f.extend(table([
        ["Framework", "Human practice", "Machine analogue in SecondBrain"],
        ["PARA", "Organise everything into Projects, Areas, Resources, Archives",
         "Memory scoring separates active project material from archival recollection; consolidation "
         "merges redundant copies; the vault stores permanently."],
        ["CODE", "Capture, Organise, Distil, Express",
         "The seven-stage pipeline: capture \u2192 understand \u2192 store \u2192 retrieve \u2192 reason "
         "\u2192 explain \u2192 learn."],
        ["Progressive summarisation", "Repeatedly condense a note until only the essence remains",
         "The wiki compiler re-summarises each topic as new evidence arrives, producing a shorter "
         "article from a growing corpus."],
    ], [78, 175, W - 253],
        caption="Table 2 \u2014 How established PKM frameworks map onto the implemented architecture."))
    f.append(P(
        "The important observation is that all three frameworks place the burden of judgement on the "
        "human. SecondBrain's contribution is to automate that judgement, which requires \u2014 and this "
        "is the pivot that led to the research layer \u2014 a formal notion of what makes one piece of "
        "knowledge more important than another."))

    f.append(Sub("The JARVIS reference, read correctly"))
    f.append(P(
        "The author's stated design target was JARVIS, the assistant from the Iron Man films, and "
        "supplied two reference videos: the workshop scene from <i>Iron Man 2</i>, and a compilation "
        "of the abilities of Tony Stark's several AIs. It is worth being precise about what these "
        "actually depict, because the superficial reading and the useful reading are different."))
    f.append(P(
        "The superficial reading is that JARVIS is a voice assistant with holographic displays. That "
        "reading leads to a project that is a talking interface with animations \u2014 visually "
        "impressive and functionally empty. The useful reading, obtained by examining what the "
        "character does rather than how it looks, identifies five behaviours:"))
    f.extend(B([
        "<b>There is no interface.</b> Stark never launches JARVIS. Nothing is opened, nothing is "
        "loaded. The assistant is simply present.",
        "<b>It speaks first.</b> JARVIS initiates. A conventional assistant only ever responds.",
        "<b>It holds state.</b> It knows what Stark was doing before he walked into the room.",
        "<b>It acts.</b> It does not report a problem; it runs the simulation and reports the result.",
        "<b>It has judgement.</b> It warns, objects, and occasionally declines.",
    ]))
    f.append(P(
        "The voice is the least important element. Remove the speech and the character remains "
        "recognisable; keep only the speech and one has a talking menu. This realisation is what drove "
        "the later work on wake-word detection and proactive announcement \u2014 the behaviours that "
        "correspond to <i>it speaks first</i> \u2014 rather than further investment in visual effects."))

    f.append(Sub("Constraints established by the user"))
    f.append(P(
        "Several constraints were set explicitly during development. They are recorded here because "
        "each one eliminated a design option, and understanding what was ruled out explains much of "
        "the final architecture."))
    f.extend(table([
        ["Constraint", "Consequence for the design"],
        ["Use a free local language model; no paid API",
         "All inference runs through Ollama on the laptop GPU. Removes cost and keeps data local, but "
         "caps model size to what fits in 6 GB of VRAM."],
        ["The application must feel like a personal AI, not a project interface",
         "Rejected dashboards, side banners and admin-panel aesthetics. Drove the later full interface "
         "rebuilds."],
        ["All modules must be visible as real tabs, not hidden",
         "Produced the fifteen-tab operating-system shell and left the knowledge graph, semantic "
         "search and OCR tools permanently reachable."],
        ["No fake functionality \u2014 if a service is not connected, say so",
         "Removed all seeded demo data from interactive screens. Every panel now shows real state or "
         "an explicit disconnection message."],
        ["Build scraping software rather than paying for Apify or SupaData",
         "Led to a native ingestion stack using free libraries, and later to the same reasoning being "
         "applied to mail, where it avoided a recurring Google verification cost."],
        ["A working voice assistant triggered by name, with a transparent floating orb",
         "Drove the holographic orb window, and later the offline wake-word implementation."],
        ["The project must satisfy an IEEE paper",
         "Forced the addition of a research layer: measurement, baselines and honest limitation "
         "reporting."],
    ], [148, W - 148],
        caption="Table 3 \u2014 User constraints and their architectural consequences."))
    f.append(PageBreak())

    # =============================================================== PART II
    f.append(Section("Part II \u2014 Architecture"))
    f.append(Spacer(1, 4))

    f.append(Sub("The seven-stage pipeline"))
    f.append(P(
        "The system is organised as a pipeline in which each stage has a single responsibility and a "
        "defined contract with the next. The framing is deliberate: a pipeline can be tested stage by "
        "stage, replaced stage by stage, and reasoned about when it produces a bad result. A "
        "collection of features cannot."))
    f.extend(code(
        "  CAPTURE  \u2192  UNDERSTAND  \u2192  STORE  \u2192  RETRIEVE  \u2192  REASON  \u2192  EXPLAIN  \u2192  LEARN",
        "The seven stages. Each is independently testable and independently replaceable."))
    f.extend(code("""  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
  \u2502      USER       \u2502   voice  \u00b7  text  \u00b7  screen  \u00b7  mail  \u00b7  web
  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
           \u2502
  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u25bc\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
  \u2502   1 CAPTURE     \u2502  screenshot + OCR  \u00b7  IMAP  \u00b7  iCal  \u00b7  scrapers
  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
           \u2502
  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u25bc\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
  \u2502  2 UNDERSTAND   \u2502  curation  \u00b7  entity  \u00b7  topic  \u00b7  scoring  \u00b7  triples
  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
           \u2502
  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u25bc\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510        \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
  \u2502   3 STORE       \u2502\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u25b6\u2502  memory_vault \u2502  JSON cards
  \u2502  SQLite 49 tbl  \u2502        \u2502  + wiki + graph\u2502  git-synced
  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518        \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
           \u2502
  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u25bc\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
  \u2502   4 RETRIEVE    \u2502  vanilla  \u00b7  hybrid  \u00b7  graph  \u00b7  ADAPTIVE
  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
           \u2502
  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u25bc\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
  \u2502   5 REASON       \u2502  local LLM (Ollama) over assembled context
  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
           \u2502
  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u25bc\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
  \u2502  6 EXPLAIN      \u2502  answer  \u00b7  provenance  \u00b7  spoken aloud  \u00b7  notified
  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
           \u2502
  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u25bc\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
  \u2502   7 LEARN        \u2502  feedback \u2192 scores \u00b7 consolidation \u00b7 gap detection
  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518""",
                  "The end-to-end pipeline. Stage 7 feeds back into stages 2 and 3, which is what makes "
                  "the memory adaptive rather than a static archive."))

    f.append(Sub("Technology selection and rationale"))
    f.append(P(
        "Every dependency was chosen to satisfy three conditions: it must be free, it must run locally, "
        "and it must be replaceable without redesigning the system. The third condition is the one most "
        "often neglected in student projects and the one that proved most valuable, because it later "
        "allowed the entire retrieval layer to be swapped four ways for the comparative evaluation."))
    f.extend(table([
        ["Layer", "Choice", "Reasoning"],
        ["Language model", "Ollama with Qwen 2.5 3B",
         "Runs on the laptop's RTX 3050 within 6 GB VRAM. No per-token cost, no data egress. Model "
         "auto-detection was later added because a configured model can be absent."],
        ["Backend", "FastAPI with SQLAlchemy",
         "Asynchronous where it matters, synchronous where it does not. Pydantic models give request "
         "validation and OpenAPI documentation for free, which the contract checker later exploited."],
        ["Primary store", "SQLite (49 tables)",
         "Single-file, zero configuration, and adequate for a single-user corpus. Relational integrity "
         "matters here: memory, score, conflict and consolidation records reference each other."],
        ["Vector store", "ChromaDB (optional)",
         "Optional by design. When absent, retrieval falls back to TF-IDF, which keeps the system "
         "fully functional and the benchmark deterministic."],
        ["Embeddings", "sentence-transformers (optional)",
         "Loaded lazily in a background thread. Optional for the same reason: a personal assistant "
         "that will not start without a 90 MB download is a fragile assistant."],
        ["Desktop shell", "Electron + React 18",
         "Required for a transparent always-on-top overlay window, which a browser cannot provide."],
        ["Speech", "Web Speech API in, edge-tts or Web Speech out",
         "Free and offline-capable. The recogniser's habit of ending sessions by itself became a "
         "significant defect (Section VI)."],
        ["Wake word", "openWakeWord (optional)",
         "A small ONNX model scoring 80 ms frames on the CPU. No cloud, no account, no per-request "
         "cost."],
        ["Mail", "IMAP with app passwords, plus OAuth",
         "Two paths on purpose: the free path works without any Google Cloud project, the OAuth path "
         "covers accounts where app passwords are no longer permitted."],
    ], [62, 108, W - 170],
        caption="Table 4 \u2014 Technology choices. The recurring principle is optionality: no single "
                "dependency is load-bearing, so any one can fail without stopping the system."))

    f.append(Sub("The agent layer"))
    f.append(P(
        "Intelligence is distributed across specialised agents rather than concentrated in one "
        "monolithic service. Each agent has one job, its own failure mode, and no knowledge of the "
        "others. This is the same reasoning that later motivated the multi-component research layer: "
        "a single large component that does everything cannot be tested, instrumented or replaced."))
    f.extend(table([
        ["Agent", "Responsibility", "Failure mode if absent"],
        ["Curation", "Scores captured text for information density; elects the representative frame",
         "Every screenshot stored; the vault fills with noise"],
        ["Vault", "Writes JSON cards, compresses hero images, commits to GitHub",
         "Memory exists only locally and cannot be versioned"],
        ["Wiki compiler", "Maintains the self-improving encyclopedia per domain",
         "Knowledge accumulates but is never distilled"],
        ["Insight", "Detects collisions between separate topics; raises proactive alerts",
         "The system answers but never volunteers"],
        ["Social ingestion", "Extracts transcripts and articles from YouTube, X, Instagram, web",
         "Reading must be manual"],
        ["Mail ingestion", "Turns new email into memories, tasks and notifications",
         "The inbox is a separate world"],
        ["Deliverable", "Generates documents from accumulated memory",
         "The system can explain but not produce"],
    ], [86, 190, W - 276],
        caption="Table 5 \u2014 The agent layer. Each agent is independently removable."))

    f.append(Sub("Data model"))
    f.append(P(
        "The database has 49 tables. They divide into four groups, and the grouping reflects the "
        "chronology of the build: capture tables came first, then knowledge tables, then conversation "
        "tables, and finally the research tables added at the very end."))
    f.extend(code("""  CAPTURE (11)     sessions, screenshots, activity_logs, app_usage, clipboard_logs,
                   extracted_text, ocr_metadata, processed_sessions, detected_topics,
                   semantic_chunks, settings

  KNOWLEDGE (17)   memories, memory_tags, memory_relationships, search_index,
                   session_summaries, graph_nodes, graph_edges, concept_clusters,
                   graph_metadata, topic_relationships, learning_progression,
                   vector_memories, memory_clusters, semantic_relationships,
                   embedding_jobs, search_history, timeline_events

  CONVERSATION (9) conversations, messages, retrieved_memories, conversation_context,
                   ai_summaries, ai_feedback, voice_sessions, transcripts,
                   conversation_audio, language_preferences, voice_commands

  RESEARCH (7)     memory_scores, temporal_facts, memory_conflicts,
                   memory_consolidations, forgotten_memories, knowledge_gaps,
                   research_runs

  PLATFORM (5)     users, sessions, activities, settings, memory_sessions""",
                  "The data model grouped by purpose. The research group is additive: it observes "
                  "existing memories through foreign keys and never modifies the capture pipeline."))
    f.extend(callout(
        "Design decision: the research layer is additive",
        "The seven research components were added as entirely new tables keyed to existing memory "
        "identifiers. Nothing in the capture, curation or vault pipeline was modified. This was a "
        "deliberate risk-reduction choice: the application was already working and in daily use, and "
        "a research layer that broke the working system would have been worthless. It also made the "
        "comparative evaluation possible, because the research layer could be switched off to yield "
        "the baseline pipeline exactly as it existed before."))
    f.append(PageBreak())

    # ============================================================== PART III
    f.append(Section("Part III \u2014 Build Chronology"))
    f.append(Spacer(1, 4))
    f.append(P(
        "The system was built in seven phases. For each phase this section records what the user asked "
        "for, what was built, the reasoning behind the approach, and what went wrong. The failures are "
        "included deliberately: the defects of each phase reveal what was not yet understood, and "
        "several of them directly motivated the next phase."))

    # ---- Phase 0
    f.append(Sub("Phase 0 \u2014 Foundations (August 2026)"))
    f.append(P("<b>User request.</b> Build a personal knowledge system that captures what I do on my "
               "laptop and lets me search it later."))
    f.append(P(
        "<b>What was built.</b> The initial skeleton: FastAPI backend, SQLite schema, authentication "
        "with JWT, a session model, screenshot capture, and text-to-speech plumbing. The earliest "
        "commits concern mundane but load-bearing details \u2014 asynchronous handling in speech "
        "synthesis, token validity on socket connections \u2014 which is characteristic of a project "
        "finding its foundations rather than its features."))
    f.append(P(
        "<b>Reasoning.</b> The decision here that mattered most was to build capture as a first-class "
        "pipeline rather than as a feature of a notes application. A notes application begins with an "
        "empty page and waits; a capture pipeline begins with a screen and a clock. Everything "
        "downstream \u2014 curation, scoring, retrieval \u2014 only makes sense if there is a steady "
        "supply of raw material."))
    f.append(P(
        "<b>What went wrong.</b> Two problems surfaced that would recur throughout the project. First, "
        "the virtual environment was not being located reliably when the backend was launched from "
        "Node, which produced a confusing failure where the backend appeared to start but had no "
        "dependencies. Second, and more seriously, the backend silently swallowed exceptions in "
        "several places, so endpoints returned empty results instead of errors. Both were early "
        "instances of a theme that dominates Part VI: <i>a system that fails quietly is far more "
        "expensive than one that fails loudly.</i>"))

    # ---- Phase 1
    f.append(Sub("Phase 1 \u2014 Capture, Curation and the Vault (17 September)"))
    f.append(P("<b>User request.</b> Make the captured knowledge persistent, visual and shareable; put "
               "it in GitHub so it cannot be lost; and make the stored material actually meaningful "
               "rather than a dump of screenshots."))
    f.append(P(
        "<b>What was built.</b> This is the phase in which the system became recognisable. Seven "
        "components landed:"))
    f.extend(B([
        "An agentic curation layer that scores captured text for information density and rejects "
        "low-value frames before storage.",
        "A best-shot hero image engine that elects one representative frame per information period, "
        "compressed to WebP, instead of keeping every screenshot.",
        "Ephemeral screen pruning: raw screenshots are deleted after the hero is extracted, so the "
        "system consumes approximately zero persistent disk for visual data.",
        "A Git vault agent that commits memory cards and hero images to GitHub automatically.",
        "A self-improving wiki compiler that maintains one article per topic domain and rewrites it "
        "as new evidence arrives.",
        "A three-dimensional neural brain visualisation rendered on a canvas.",
        "Native Ollama streaming, replacing an OpenAI-compatibility layer that was returning 404s.",
    ]))
    f.append(P(
        "<b>Reasoning.</b> Three decisions here were consequential. The first was the hero image "
        "approach: storing every screenshot is the obvious implementation and it fails, because "
        "storage grows without bound and retrieves nothing useful. Electing a single representative "
        "frame per period inverts the problem \u2014 the system keeps the <i>best</i> evidence rather "
        "than <i>all</i> evidence, and the criterion for best is measurable (text density)."))
    f.append(P(
        "The second was routing the language model through Ollama's native API rather than its "
        "OpenAI-compatible endpoint. The compatible endpoint was returning \u201cmodel not found\u201d "
        "for a model that existed, and diagnosing this took longer than it should have; the native "
        "endpoint simply works. The general principle extracted was that compatibility shims add a "
        "failure mode without adding capability, and should be avoided when talking to your own "
        "infrastructure."))
    f.append(P(
        "The third, and the one with the greatest long-term significance, was the wiki compiler. "
        "Rather than storing each ingestion as an isolated record, the compiler folds it into a "
        "per-topic article that is rewritten as evidence accumulates. This means the corpus gets "
        "<i>shorter and better</i> as it grows, which is the opposite of the usual behaviour and is "
        "what makes question-answering over long-term memory tractable at all."))
    f.append(P(
        "<b>What went wrong.</b> The vault agent initially resolved the repository root incorrectly, "
        "so it committed to the wrong directory. Separately, titles were being lost for web and "
        "YouTube captures because the title extraction depended on OCR text that was sparse for those "
        "sources; this was fixed by falling back to the page title and video metadata."))

    # ---- Phase 2
    f.append(Sub("Phase 2 \u2014 The Intelligence Layer (18 September)"))
    f.append(P("<b>User request.</b> Stop using paid scraping services; build the scraping capability "
               "yourself. Also: the system should notice things and tell me, not wait to be asked."))
    f.append(P(
        "<b>What was built.</b> A native ingestion stack replacing Apify and SupaData entirely: "
        "YouTube transcripts via a free library, X posts via a public JSON endpoint, Instagram via an "
        "open-source client with an Open Graph fallback, and general web articles via HTML parsing. "
        "Alongside it, a proactive insight layer that detects collisions between otherwise unrelated "
        "topics and raises an alert unprompted, plus a morning briefing that is spoken aloud."))
    f.append(P(
        "<b>Reasoning.</b> The user's instruction contained a generalisable principle: <i>replace a "
        "recurring cost with a one-off engineering effort.</i> The scraping stack initially used paid "
        "APIs because that is the obvious path; the authors identified it as unacceptable and the "
        "replacement was built. The same reasoning was later applied, unprompted, to mail and "
        "calendar, where it saved a recurring Google verification cost \u2014 see Part V, deviation 7."))
    f.append(P(
        "Performance work in this phase is worth recording because it demonstrates that the bottleneck "
        "was architectural rather than computational. The first implementation of URL ingestion "
        "fetched metadata, transcript and thumbnail sequentially, taking several seconds. Parallelising "
        "the independent fetches brought it below one second (0.98 s measured) without changing any "
        "algorithm. The lesson is that <i>most apparent slowness in I/O-bound pipelines is sequential "
        "waiting, not computation</i>, and that the fix is usually concurrency rather than optimisation."))
    f.append(P(
        "<b>What went wrong.</b> Repeated hero image extraction meant the raw screen files could be "
        "deleted while a preview still referenced them, producing broken images in the live view. The "
        "fix was a dedicated preview buffer that is never pruned \u2014 an instance of a general "
        "principle: <i>never let a cleanup process delete the last reference to something a view "
        "depends on.</i>"))

    # ---- Phase 3
    f.append(Sub("Phase 3 \u2014 The Interface (21 September)"))
    f.append(P("<b>User request.</b> This does not feel like a personal AI. It feels like a project "
               "dashboard. Make it feel like Jarvis, and do not hide any of the functionality."))
    f.append(P(
        "<b>What was built.</b> Three successive interface rebuilds in a single day, which is itself "
        "instructive. The first transformed the application shell into an Obsidian-style workspace to "
        "match a screenshot the authors supplied. The second removed the project sidebars entirely and "
        "introduced a living holographic core that tracks the mouse and provides an ambient voice "
        "intercom. The third produced the definitive fifteen-tab operating-system shell with a "
        "universal command terminal, and a transparent always-on-top golden orb window that floats in "
        "the bottom-right corner of the desktop."))
    f.append(P(
        "<b>Reasoning.</b> The iterative rebuilds were not indecision; they were the authors converging "
        "on a requirement that could not be specified in advance. The first attempt established that "
        "the visual language was wrong. The second established that removing navigation entirely made "
        "functionality unfindable. The third reconciled both: persistent visible navigation with a "
        "command centre, which is what the authors had wanted all along but could not articulate "
        "without seeing the alternatives."))
    f.append(P(
        "The orb deserves specific note. Making a window genuinely transparent on Windows required "
        "simultaneous changes at three layers: Electron's window flags, the CSS on the document root, "
        "and the body background. Changing any one alone produced the characteristic dark rectangle "
        "the authors reported. This is a recurring pattern in cross-layer work: <i>when a visual defect "
        "survives a fix, the fix is usually correct but incomplete across layers.</i>"))
    f.append(P(
        "<b>What went wrong.</b> The interface rebuilds broke the application twice. First, a missing "
        "icon import produced a blank screen on the home route; an error boundary added in response "
        "revealed the exact cause and became a permanent safety net. Second, the server's "
        "hot-reload behaviour had to be made resilient to window reloads. Both are covered in Part VI."))

    # ---- Phase 4
    f.append(Sub("Phase 4 \u2014 Stabilisation (22 September, morning)"))
    f.append(P("<b>User request.</b> \u201cIt's an error. I need you to fully do an error check "
               "environment and fix every error.\u201d"))
    f.append(P(
        "<b>What was built.</b> Not features but instrumentation. Two full audits were performed, and "
        "the difference between them is the most important methodological lesson in this report."))
    f.append(P(
        "The <b>first audit</b> fixed the error the authors could see \u2014 a missing React import "
        "that crashed a page \u2014 and found one more instance of the same class of defect waiting to "
        "be triggered. It added a linter to catch undefined identifiers, and several static checks."))
    f.append(P(
        "The <b>second audit</b> found something far more serious that the first had missed entirely, "
        "because it required <i>running</i> the system rather than reading it: authentication had never "
        "worked. A service used a configuration object without importing it, so the login function "
        "raised before comparing any password. Because the frontend swallowed the resulting error, the "
        "application ran with no token at all, and 52 protected endpoints returned 401 while the "
        "interface rendered them as empty states. Everything looked fine and nothing worked."))
    f.extend(callout(
        "The single most valuable lesson in the project",
        "Static analysis catches what is written wrong. Only execution catches what is written "
        "plausibly but connects to nothing. The first audit\u2019s tools were correct and useful, and "
        "they could not possibly have found a broken login, because a login that returns 500 is "
        "syntactically valid code. The second audit found it in minutes by starting the server, "
        "logging in, and calling every endpoint. This is why the verification system described in "
        "Part VII ends with a live endpoint sweep rather than a linter."))
    f.append(P(
        "<b>What went wrong.</b> A related defect compounded the damage: 33 call sites used a raw "
        "browser fetch which does not attach the authentication token, so even a correct login would "
        "not have authenticated those screens. The fix was a single authenticated fetch helper plus a "
        "mechanical replacement across 18 files. It is worth noting that this defect was invisible in "
        "review precisely because the code <i>looked</i> correct."))

    # ---- Phase 5
    f.append(Sub("Phase 5 \u2014 Connectivity (22 September)"))
    f.append(P("<b>User request.</b> Connect these three email accounts to my Second Brain. Then, "
               "separately: why can Grok connect directly and this cannot?"))
    f.append(P(
        "<b>What was built.</b> Two complete integration paths. The first was Google OAuth with "
        "multi-account support, encrypted token storage and read-only scopes. The second, built after "
        "research into what publishing such an application actually requires, was Gmail over IMAP with "
        "app passwords and Google Calendar via its private iCalendar address \u2014 neither of which "
        "requires a Google Cloud project, a consent screen, or verification."))
    f.append(P(
        "<b>Reasoning.</b> This phase contains the most consequential decision in the project, and it "
        "came directly from the authors' question about Grok. Investigating that question revealed "
        "that reading a Gmail inbox requires a scope Google classifies as <i>restricted</i>, and that "
        "publishing an application using it requires a third-party security assessment costing roughly "
        "US$540\u2013$1,800 annually with re-certification every year. For an application with exactly "
        "one user, that cost is indefensible. The research also revealed that staying unverified is "
        "worse in practice, because refresh tokens expire every seven days, forcing weekly reconnection "
        "of every account."))
    f.append(P(
        "The resolution was to recognise that OAuth is not the only way to read a mailbox. IMAP with "
        "an app password is what desktop mail clients have used for decades. It is free, permanent, and "
        "read-only by construction when the correct IMAP commands are used. The same reasoning applied "
        "to calendar data: Google publishes a private iCalendar address per calendar which requires no "
        "authentication whatsoever."))
    f.extend(code("""  GOOGLE OAUTH PATH                    IMAP + iCAL PATH  (chosen)
  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500     \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
  Cloud project required               No project required
  Consent screen required              No consent screen
  Verification for restricted scope    No verification
  CASA assessment ~$540-$1800 / year   Free, permanently
  Refresh token expires in 7 days      Never expires
  (while app is unverified)
  Works for Workspace accounts         Works for personal accounts
                                       (Workspace needs the OAuth path)""",
                  "Why the IMAP path was adopted as the default. The OAuth path was retained rather "
                  "than removed, because it remains the only option for some accounts."))
    f.append(P(
        "<b>What went wrong.</b> The author's Workspace (college) account cannot use app passwords, "
        "because Google disabled them for Workspace domains in May 2025, and the institution's "
        "administrator may block third-party access regardless. This was documented honestly rather "
        "than worked around, and the system was designed to function with any subset of accounts "
        "connected."))

    # ---- Phase 6
    f.append(Sub("Phase 6 \u2014 Presence (22 September)"))
    f.append(P("<b>User request.</b> The floating orb answers one question and then stops. Also: here "
               "are two videos about Jarvis \u2014 what do you understand from them?"))
    f.append(P(
        "<b>What was built.</b> An analysis of the two reference videos that distinguished their "
        "surface (voice, holograms) from their substance (presence, initiative, state, action, "
        "judgement), and two implementations corresponding to the two traits the system lacked: an "
        "offline wake word, and proactive speech."))
    f.append(P(
        "<b>Reasoning.</b> The orb defect was diagnosed as a missing re-arm: the browser's speech "
        "recogniser ends its session by itself, and the code had no handler to restart it, so the "
        "microphone came up exactly once and then never again. Critically, the wake trigger only spoke "
        "a greeting and never restarted the recogniser, so summoning the assistant repeatedly would "
        "produce repeated greetings from a dead microphone."))
    f.append(P(
        "The wake word required validating a real audio model rather than trusting a mock. Synthetic "
        "speech was generated, decoded to the correct sample rate, and pushed through the project's own "
        "scoring function. The measured separation was decisive: spoken \u201cHey Jarvis\u201d scored "
        "0.9968 while silence, white noise and a pure tone scored below 0.002. This both confirmed the "
        "frame size and threshold and produced a reusable regression test."))
    f.append(P(
        "<b>What went wrong.</b> Three distinct defects, all described in Part VI. The most subtle is "
        "that if the language model never responds, the orb would wait forever with the microphone "
        "paused, appearing to be broken. A watchdog was added. The second is that text-to-speech "
        "completion events are not guaranteed in Electron when the window is hidden, which would leave "
        "the orb permanently muted; a second watchdog was added for that. The third is that the "
        "existing wake handler <i>toggled</i> the orb window rather than showing it, so a wake event "
        "arriving while the orb was already visible would hide it \u2014 precisely the opposite of the "
        "intent."))

    # ---- Phase 7
    f.append(Sub("Phase 7 \u2014 The Research Layer (22 September)"))
    f.append(P("<b>User request.</b> I need a paper that is genuinely novel, and the project must "
               "actually be what the paper claims."))
    f.append(P(
        "<b>What was built.</b> Seven components implementing the paper's seven claimed contributions, "
        "wired into retrieval, plus PersonalBrain-Bench and a four-system comparative evaluation. The "
        "detailed accounts are in Parts IV and VIII."))
    f.append(P(
        "<b>Reasoning, and the honest starting point.</b> Before writing any paper text, the claims "
        "were audited against the codebase. The result: one contribution partially existed, and six "
        "did not exist at all. Writing the paper first would have produced a document describing "
        "software that had not been written. This is stated plainly because it is the correct order of "
        "operations for any research project \u2014 <i>the paper is a description of what was done and "
        "measured, not a specification of what one intends to do.</i>"))
    f.append(P(
        "Building the components then revealed that the interesting result was not the one anticipated. "
        "The expectation was that the research layer would improve retrieval accuracy. It did not: "
        "Hit@5 was already 1.000 for every pipeline, including the simplest baseline. Every system "
        "found the relevant memory somewhere in its top five. What separated them was the <i>ordering</i> "
        "of the results and the <i>staleness</i> of what came first \u2014 and that is a much more "
        "interesting finding, because it means the conventional metric would have reported that the "
        "entire research layer accomplished nothing."))
    f.append(P(
        "<b>What went wrong.</b> Nine defects were found by the research tests, including a temporal "
        "modelling error that caused the exact failure the paper is about, and a substring-matching bug "
        "that flagged any note mentioning \u201cnotes\u201d as a logical contradiction. Both are "
        "recorded in Part VI. Additionally, a defect in the earlier mail-ingestion test was discovered "
        "to have deleted 123 of the authors' genuine memory cards; this was caught before committing, "
        "restored from version control, and the test was made structurally incapable of touching "
        "unmarked data. That incident is recorded in full because it is the most serious defect of the "
        "project and the lesson it carries is not a technical one."))
    f.append(Spacer(1, 6))
    f.append(P(
        "The remaining parts of this report examine what was built from four different angles: the "
        "theory behind it (Part IV), the deviations from plan (Part V), the defects (Part VI), and how "
        "correctness is established (Part VII)."))
    f.append(PageBreak())

    return f


def datetime_stamp():
    return datetime.now().strftime("%d %B %Y")
