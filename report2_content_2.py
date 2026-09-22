"""Big report - Volume III (chronology with code) and Volume IV (theory, 14 chapters)."""
from reportlab.platypus import PageBreak, Paragraph, Spacer

from report_builder_base import BODY_W, B, P, S, Section, Sub, callout, code, table

W = BODY_W


def build():
    f = []

    # ============================================================ VOLUME III
    f.append(Section("Volume III \u2014 Build Chronology"))
    f.append(Spacer(1, 4))
    f.append(P(
        "Eight phases. For each: what the author asked for, what was built, the reasoning behind the "
        "approach, and \u2014 deliberately \u2014 what went wrong. The failures are included because "
        "the defects of each phase reveal what was not yet understood, and several of them directly "
        "motivated the phase that followed."))

    phases = [
        ("Phase 0", "Foundations", "August 2026",
         "Build a personal knowledge system that captures what I do on my laptop and lets me search "
         "it later.",
         ["FastAPI backend with SQLAlchemy and Pydantic schemas.",
          "SQLite schema with users, sessions, activities and capture tables.",
          "JWT authentication with password hashing.",
          "Screenshot capture scaffolding and text-to-speech plumbing.",
          "WebSocket scaffolding for live updates."],
         "The decision that mattered was to build capture as a first-class pipeline rather than as a "
         "feature of a notes application. A notes application begins with an empty page and waits; a "
         "capture pipeline begins with a screen and a clock. Everything downstream \u2014 curation, "
         "scoring, retrieval \u2014 only makes sense when there is a steady supply of raw material.",
         ["The virtual environment was not located reliably when the backend was launched from Node. "
          "The backend appeared to start but had no dependencies installed. This produced a confusing "
          "failure where the server was running but every import failed.",
          "Exceptions were swallowed in several endpoints, so operations that had failed returned "
          "empty results rather than errors. This is the first appearance of the defect class that "
          "would eventually consume more time than any other."]),

        ("Phase 1", "Capture, Curation and the Vault", "17 September",
         "Make the captured knowledge persistent, visual and safe from loss; put it in GitHub; and "
         "make the stored material actually meaningful rather than a dump of screenshots.",
         ["An agentic curation layer scoring captured text for information density.",
          "A best-shot hero image engine electing one representative frame per information period, "
          "compressed to WebP.",
          "Ephemeral screen pruning: raw frames deleted after the hero is extracted, so persistent "
          "storage for visual data approaches zero.",
          "A Git vault agent committing memory cards and images automatically.",
          "A self-improving wiki compiler maintaining one article per topic domain.",
          "A three-dimensional neural visualisation on canvas.",
          "Native Ollama streaming, replacing a compatibility endpoint that was returning 404s."],
         "Three decisions here proved consequential. The hero image approach inverts the storage "
         "problem: rather than keeping all evidence, keep the best evidence, and make 'best' a "
         "measurable criterion (text density). The wiki compiler produces the counter-intuitive "
         "property that the corpus becomes shorter and better as it grows. And routing the model "
         "through Ollama's native API rather than its compatibility shim established a principle "
         "applied repeatedly afterwards: when talking to your own infrastructure, avoid adapters.",
         ["The vault agent resolved the repository root incorrectly, committing to the wrong "
          "directory \u2014 a path-resolution defect that recurred in other components.",
          "Titles were lost for web and video captures because title extraction depended on OCR text "
          "that is sparse for those source types. Fixed by falling back to page metadata."]),

        ("Phase 2", "The Intelligence Layer", "18 September",
         "Stop using paid scraping services \u2014 build that capability yourself. Also, the system "
         "should notice things and tell me, rather than waiting to be asked.",
         ["A native ingestion stack replacing the paid services: video transcripts via a free "
          "library, social posts via a public endpoint, image-sharing sites via an open-source "
          "client with a metadata fallback, and general web articles via HTML parsing.",
          "A proactive insight layer detecting collisions between otherwise unrelated topics.",
          "A morning briefing compiled from accumulated state and spoken aloud.",
          "A deliverable generator producing documents from memory.",
          "An ambient command overlay bound to a global shortcut."],
         "The author's instruction contained a generalisable principle: replace a recurring cost with "
         "a one-off engineering effort. The paid services were the obvious path and the author "
         "rejected them; the replacement was built. The same reasoning was later applied without "
         "prompting to mail and calendar, where it avoided a recurring verification cost entirely "
         "(deviation D7). Performance work here also demonstrated that the bottleneck was "
         "architectural rather than computational: parallelising independent network fetches took "
         "ingestion from several seconds to 0.98 seconds without changing any algorithm.",
         ["Repeated hero-image extraction meant raw frames could be deleted while a live preview "
          "still referenced them, producing broken images. Fixed with a dedicated preview buffer "
          "excluded from pruning. The general principle: never let a cleanup process delete the last "
          "reference to something a view depends on.",
          "Window-title tracking was eagerly initialised at import time, which slowed startup and "
          "caused failures on machines without the necessary platform bindings. Made lazy."]),

        ("Phase 3", "The Interface", "21 September",
         "This does not feel like a personal AI. It feels like a project dashboard. Make it feel like "
         "the reference, and do not hide any of the functionality.",
         ["Three successive interface rebuilds in one day.",
          "The first transformed the shell into a graph-oriented workspace matching a reference "
          "screenshot the author supplied.",
          "The second removed the project sidebars entirely and introduced a living holographic core "
          "that tracks the mouse, with an ambient voice intercom.",
          "The third produced the definitive fifteen-tab operating-system shell with a universal "
          "command terminal.",
          "A transparent, borderless, always-on-top orb window positioned at the bottom-right of the "
          "desktop.",
          "Procedural audio for interface feedback."],
         "The iterative rebuilds were convergence, not indecision. The requirement could not be "
         "specified in advance because the author could not articulate the difference between a "
         "dashboard and an assistant without seeing the alternatives. The first attempt established "
         "that the visual language was wrong; the second established that removing navigation "
         "entirely makes functionality unfindable; the third reconciled both. This is a general "
         "pattern in interface work: the requirement is discovered by building the wrong thing "
         "quickly.",
         ["A missing component import produced a blank screen on the home route. An error boundary "
          "was added in response, which displayed the exact cause and became a permanent safety net.",
          "Making a window genuinely transparent on Windows required simultaneous changes at three "
          "layers \u2014 the Electron window flags, the document-root CSS, and the body background. "
          "Changing any one alone produced the dark rectangle the author reported.",
          "The auto-launch registration pointed at the bare runtime executable in development mode, "
          "so a Windows boot produced a raw framework splash screen rather than the application."]),

        ("Phase 4", "Stabilisation", "22 September, morning",
         "\u201cIt's an error. I need you to fully do an error check environment and fix every "
         "error.\u201d",
         ["No features. Instrumentation only.",
          "The first audit: a linter configured to fail on undefined identifiers, plus eight static "
          "integration checks covering imports, component existence, client method definitions, "
          "route-module existence, frontend-to-backend URL agreement, preload surface completeness, "
          "Python compilation, and route file resolution.",
          "The second audit: a live endpoint sweep that boots the server, logs in, and calls every "
          "registered route, reporting status and timing.",
          "A route-render smoke test that renders and mounts every interface route.",
          "An API contract checker comparing every URL the interface calls against every route the "
          "backend serves."],
         "The difference between the two audits is the most important methodological lesson in this "
         "project. The first audit was correct and useful and could not possibly have found the most "
         "serious defect, because a login function that raises before comparing a password is "
         "syntactically valid code. Only running the system and attempting to log in revealed it. "
         "This is why the verification system described in Volume VIII ends with a live sweep rather "
         "than a linter.",
         ["<b>Authentication had never worked.</b> A service referenced a configuration object "
          "without importing it, so the login function raised before comparing any password. The "
          "frontend swallowed the resulting error, so the application ran with no token and 52 "
          "protected endpoints returned 401 \u2014 which the interface rendered as empty states. "
          "Everything looked fine and nothing worked.",
          "Thirty-three call sites used a raw browser fetch which does not attach the authentication "
          "token, so even a correct login would not have authenticated most screens.",
          "A test was passing while the system it tested was offline, because it checked only the "
          "status code of an endpoint that always returns success."]),

        ("Phase 5", "Connectivity", "22 September",
         "Connect these three email accounts to my Second Brain. And then, separately: why can a "
         "commercial assistant connect directly while this cannot?",
         ["Google OAuth with multi-account support, encrypted token storage and strictly read-only "
          "scopes.",
          "Then, after research into what publishing such an application requires: a second "
          "connection path using IMAP with app passwords for mail and the private iCalendar address "
          "for calendars.",
          "A unified mail and calendar API abstracting over both providers, so the interface never "
          "needs to know how an account was connected.",
          "Encrypted credential storage that refuses to write inside the synchronised vault "
          "directory.",
          "An ingestion agent reading new mail read-only and turning each message into a memory, a "
          "task, a notification and \u2014 where a deadline is detected \u2014 a spoken alert."],
         "This phase contains the project's most consequential decision, and it came directly from "
         "the author's question. Investigating why a commercial assistant appears to connect "
         "'directly' revealed that it does not: it performs the same consent flow, and appears "
         "effortless only because the vendor has absorbed the cost of a mandatory third-party "
         "security assessment that runs to several hundred dollars annually with re-certification "
         "every year. For an application with one user that cost is indefensible, and staying "
         "unverified is worse in practice because refresh tokens expire weekly. The resolution was "
         "to recognise that OAuth is not the only way to read a mailbox: IMAP with an app password "
         "is what desktop mail clients have used for decades, is free, does not expire, and is "
         "read-only by construction when the correct commands are used.",
         ["The author's institutional account cannot use app passwords, because the provider disabled "
          "them for managed domains in May 2025 and the institution may block third-party access "
          "regardless. Documented honestly rather than worked around; the system was designed to "
          "function with any subset of accounts connected.",
          "The ingestion test initially registered the author's real address, which later caused a "
          "serious incident described in Volume VI.",
          "An error-mapping defect caused six endpoints to report an upstream failure when the real "
          "problem was a non-existent identifier."]),

        ("Phase 6", "Presence", "22 September",
         "The floating orb answers one question and then stops. Also: here are two reference videos "
         "\u2014 report what you understand from them.",
         ["An analysis of the two videos separating their surface (voice, holograms) from their "
          "substance (presence, initiative, state, action, judgement).",
          "An offline wake-word implementation so the assistant can be addressed by name.",
          "Proactive speech with a policy layer: priority threshold, quiet hours, per-source "
          "cooldown, and sentence deduplication.",
          "A repair of the orb's voice loop, which had no handler to restart recognition after the "
          "browser ended the session."],
         "The orb defect was diagnosed as a missing re-arm: the browser's speech recogniser ends its "
         "session by itself, and the code had no handler to restart it, so the microphone came up "
         "exactly once. Critically, the summon gesture only spoke a greeting and never restarted the "
         "recogniser, so summoning the assistant repeatedly produced repeated greetings from a dead "
         "microphone. The wake word required validating a real audio model rather than a mock: "
         "synthetic speech was generated, decoded to the correct sample rate, and pushed through the "
         "project's own scoring function, producing a measured separation between the positive case "
         "and every negative control.",
         ["Three further ways the assistant could become unresponsive, two of which had never been "
          "observed and were found by writing the tests: a turn the model never answers leaves the "
          "microphone paused indefinitely; the text-to-speech completion event is not guaranteed in "
          "Electron when the window is hidden; and the existing wake handler toggled window "
          "visibility rather than showing it, so waking an already-visible orb would hide it.",
          "The wake-word library's loading interface differed between the installed version and the "
          "documented version, so the first implementation would have failed silently on the target "
          "machine."]),

        ("Phase 7", "The Research Layer", "22 September",
         "I need a paper that is genuinely novel, and the project must actually be what the paper "
         "claims.",
         ["An audit of the paper's claims against the codebase before any paper text was written.",
          "Seven components implementing the claimed contributions: adaptive memory scoring, a "
          "temporal knowledge graph, contradiction-aware retrieval, memory consolidation, "
          "knowledge-gap detection, retrieval-enforced forgetting, and a benchmark.",
          "A synthetic corpus and question set covering six categories.",
          "A four-system comparative evaluation with custom metrics for staleness, leakage and "
          "duplication.",
          "An IEEE-format paper generated from measured output rather than hand-written numbers."],
         "Before writing any paper text, the seven claimed contributions were audited against the "
         "codebase. One partially existed; six did not exist at all. Writing the paper first would "
         "have produced a document describing software that had not been written. Building the "
         "components then produced the project's most interesting finding, which was not the one "
         "anticipated: the research layer did not improve retrieval accuracy, because accuracy was "
         "already saturated at 1.000. What it improved was the ordering of results and the staleness "
         "of the top-ranked item \u2014 and that is a far more interesting result, because it means "
         "the conventional metric would have reported that seven components accomplished nothing.",
         ["Nine defects found by the research tests, including a temporal modelling error that caused "
          "the exact failure the paper is about, and a substring-matching defect that flagged any "
          "note mentioning 'notes' as a logical contradiction.",
          "The benchmark was not reproducible between runs because derived state from a previous run "
          "perturbed the following one.",
          "The mail-ingestion test was discovered to have deleted 123 of the author's genuine memory "
          "cards. Caught before commit, restored from version control, and the test made "
          "structurally incapable of touching unmarked data."]),
    ]

    for label, title, when, request, built, reasoning, wrong in phases:
        f.append(Sub(f"{label} \u2014 {title}", number=None))
        f.append(Paragraph(f"<i>{when}</i>", S["caption"]))
        f.append(Paragraph(f"<b>Request.</b> {request}", S["body"]))
        f.append(Paragraph("<b>What was built.</b>", S["body"]))
        f.extend(B(built))
        f.append(Paragraph(f"<b>Reasoning.</b> {reasoning}", S["body"]))
        f.append(Paragraph("<b>What went wrong.</b>", S["body"]))
        f.extend(B(wrong))
        f.append(Spacer(1, 4))

    f.extend(callout(
        "The chronology in one observation",
        "Phases 4 to 7 all occurred on the same day. The pace was not the result of hurrying; it was "
        "the result of the verification system built in Phase 4. Before it existed, changes were "
        "risky and had to be validated by hand. After it existed, a change could be made, checked "
        "against fifteen gates in under a minute, and committed with confidence. Tooling compounds: "
        "the afternoon of an engineering project is faster than the morning only if the morning was "
        "spent building the means to verify."))
    f.append(PageBreak())

    # ============================================================= VOLUME IV
    f.append(Section("Volume IV \u2014 Concepts and Theory"))
    f.append(Spacer(1, 4))
    f.append(P(
        "Fourteen chapters covering the theory the system rests on. Each is written for a reader who "
        "does not already know the terminology: the concept is introduced from first principles, its "
        "mathematics is given where it is short enough to be useful, and it is then connected to the "
        "specific place in this codebase where it is applied."))

    # ---- Ch 1
    f.append(Sub("13. Information retrieval: from keywords to meaning"))
    f.append(P(
        "Information retrieval is the discipline of finding documents relevant to a query. It is "
        "older than machine learning, and its classical results remain the foundation of modern "
        "systems."))
    f.append(Paragraph("<b>The lexical tradition.</b>", S["h3"]))
    f.append(P(
        "Early retrieval systems matched query terms against document terms. The naive version "
        "\u2014 count how often each query word appears \u2014 fails badly, because common words "
        "appear everywhere and carry no information. The classical remedy is <b>inverse document "
        "frequency</b> (IDF), which weights a term by how rare it is across the corpus:"))
    f.extend(code("""  idf(t) = log( (1 + N) / (1 + df(t)) ) + 1

      where N  = number of documents
            df = number of documents containing the term

  Weight each term:  w(t, d) = tf(t, d) \u00b7 idf(t)
  Score a document:  cosine similarity between query and document weight vectors""",
                  "TF-IDF. A term appearing in every document contributes almost nothing; a term "
                  "appearing in three documents is highly informative. This is implemented in "
                  "SecondBrain as the dense-retrieval fallback when no embedding model is present."))
    f.append(P(
        "The weakness of the lexical approach is <b>vocabulary mismatch</b>: a query for "
        "\u201cvehicle\u201d will not retrieve a document about \u201ccars\u201d, because the two "
        "share no terms, even though a human considers them the same question. This is the problem "
        "that vector representations solve."))
    f.append(Paragraph("<b>The probabilistic tradition.</b>", S["h3"]))
    f.append(P(
        "A second classical line treats retrieval as probability estimation: rank documents by the "
        "probability they are relevant to the query. The practical outcome of that line is BM25, "
        "which adds term-frequency saturation (the tenth occurrence of a word adds less than the "
        "second) and document-length normalisation to the TF-IDF weighting. BM25 remained a strong "
        "baseline for decades and is still competitive with neural methods on many benchmarks."))
    f.append(Paragraph("<b>The neural tradition.</b>", S["h3"]))
    f.append(P(
        "Neural retrieval replaces term weighting with learned representations. Instead of counting "
        "words, a network maps both query and document into a vector space in which proximity means "
        "similarity of meaning. Because the mapping is learned from data rather than derived from "
        "term statistics, it handles vocabulary mismatch: \u201cvehicle\u201d and \u201ccars\u201d "
        "land near each other because they appear in similar contexts during training."))
    f.append(Paragraph("<b>Hybrid retrieval.</b>", S["h3"]))
    f.append(P(
        "Lexical and neural retrieval fail in different circumstances. Neural retrieval misses exact "
        "matches \u2014 a query for an error code or a proper noun may not benefit from semantic "
        "generalisation. Lexical retrieval misses paraphrase. Hybrid retrieval fuses both rankings, "
        "typically by weighted score combination or rank fusion. SecondBrain's hybrid retriever "
        "combines a dense candidate list with a keyword candidate list and re-ranks, which is the "
        "second of the four pipelines evaluated in Volume VII."))
    f.extend(table([
        ["Approach", "Strengths", "Weaknesses", "Where it is used here"],
        ["Boolean / exact", "Precise, predictable, no model needed",
         "No ranking, no partial match", "Not used directly"],
        ["TF-IDF / BM25", "Fast, deterministic, no training, interpretable",
         "Vocabulary mismatch, no synonymy", "The dense-retrieval fallback; also the deterministic "
                                              "basis of the reproducible benchmark"],
        ["Dense neural", "Handles paraphrase and synonymy",
         "Needs a model, misses exact tokens, can be non-deterministic across versions",
         "The primary dense path when an embedding model is configured"],
        ["Hybrid", "Best of both; robust to query type",
         "Two systems to tune and maintain", "The baseline against which the proposed pipeline is "
                                              "measured"],
    ], [72, 132, 138, W - 342],
        caption="Table 11 \u2014 The retrieval traditions. The project spans all four for a specific "
                "reason: the research evaluation requires a fair baseline, and a baseline that "
                "degenerates to zero when a model is absent would flatter the proposed method."))

    # ---- Ch 2
    f.append(Sub("14. Embeddings and the geometry of meaning"))
    f.append(P(
        "An <b>embedding</b> is a function mapping text to a fixed-length vector of real numbers, "
        "trained so that texts with related meanings map to nearby points. The space typically has "
        "between 128 and 1536 dimensions."))
    f.extend(code("""  "I want to learn Java"          \u2192  [ 0.21, -0.83,  0.44, \u2026 ]  \u2510
  "What language am I studying?"  \u2192  [ 0.19, -0.79,  0.41, \u2026 ]  \u251c close
  "Which language am I learning?" \u2192  [ 0.22, -0.81,  0.46, \u2026 ]  \u2518
  "The cat sat on the mat"        \u2192  [-0.55,  0.12, -0.90, \u2026 ]   far

  Similarity:   cos(\u03b8) = (A \u00b7 B) / (|A| \u00b7 |B|)      in [-1, 1]

  The cosine is used rather than Euclidean distance because it measures
  direction only, ignoring magnitude \u2014 so a short and a long passage
  about the same subject still compare as similar.""",
                  "Embeddings convert semantic similarity into geometry. This is the enabling "
                  "abstraction behind retrieval by meaning."))
    f.append(P(
        "Three properties matter in practice. <b>Dimensionality</b> trades representational capacity "
        "against memory and search cost. <b>Normalisation</b> \u2014 dividing each vector by its "
        "length to unit magnitude \u2014 makes the cosine equal to the dot product, which is "
        "computationally cheaper and is why the sentence-transformer models used here are configured "
        "with normalisation enabled. <b>Anisotropy</b> is the tendency of learned embeddings to "
        "occupy a narrow cone rather than filling the space; this depresses absolute similarity "
        "values and is why absolute thresholds must be calibrated per model rather than copied "
        "between systems \u2014 a fact that directly caused defect D22 in this project."))
    f.extend(callout(
        "Why absolute similarity thresholds are dangerous",
        "The consolidation component must decide when two memories are the same. The threshold "
        "commonly recommended in practice is 0.90 cosine similarity. Measuring the actual "
        "distribution in this corpus showed that genuinely reworded duplicates \u2014 the common "
        "real case \u2014 score around 0.82, while unrelated memories score below 0.30. A 0.90 "
        "threshold missed <i>every</i> reworded duplicate. The lesson is general: <i>a similarity "
        "threshold is a property of a particular embedding space, not a universal constant.</i> It "
        "must be calibrated from the measured distribution of the data it will be applied to."))

    # ---- Ch 3
    f.append(Sub("15. Chunking, context windows and the retrieval budget"))
    f.append(P(
        "A language model can only attend to a bounded amount of text at once \u2014 its <b>context "
        "window</b>. A personal corpus is far larger than any context window, so retrieval must "
        "select what to include. The amount of text a retriever supplies is therefore a <b>budget</b>, "
        "and every retrieved item consumes part of it."))
    f.append(P(
        "This produces three consequences that shape the design. First, <b>chunk size</b> is a "
        "trade-off: small chunks embed more precisely but fragment meaning and require more of them; "
        "large chunks preserve context but dilute the embedding, since one vector must represent "
        "everything in the passage. Second, <b>duplicate content is not free</b> \u2014 three copies "
        "of the same paragraph consume three times the budget and contribute one unit of "
        "information. This is the argument for consolidation, and it is measured in this project as "
        "the duplicate rate. Third, <b>irrelevant but plausible</b> content is actively harmful, "
        "because it consumes budget and can mislead the generation step, which is the argument for "
        "the staleness and contradiction penalties."))
    f.extend(code("""  THE RETRIEVAL BUDGET

   context window  \u2502\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2502
   spent on        \u2502 instructions \u2502 retrieved passages            \u2502
                   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518

   In a naive retriever the passages region fills with:
      \u2022 three copies of the same page        \u2192 duplicate rate
      \u2022 a fact that was true eight months ago \u2192 stale@1
      \u2022 content the user asked to delete      \u2192 leak rate

   Each is measurable, and each is what the three custom metrics report.""",
                  "Why duplication, staleness and leakage are not merely inefficiencies but budget "
                  "theft. This framing is what motivated the custom metrics."))

    # ---- Ch 4
    f.append(Sub("16. Knowledge representation and graphs"))
    f.append(P(
        "A vector store answers \u201cwhat resembles this?\u201d A knowledge graph answers "
        "\u201chow are things related?\u201d These are different questions and neither store "
        "subsumes the other."))
    f.append(P(
        "A <b>graph</b> consists of <b>nodes</b> (entities) and <b>edges</b> (typed relationships). "
        "The formal apparatus is graph theory; the practical significance is that certain questions "
        "are answerable only by traversal. If a document states that a project uses a dataset, and "
        "another states that the dataset was used to train a model, then \u201cwhich model relates "
        "to my project?\u201d requires following a path through two nodes and finding no single "
        "document that contains the answer. This is a <b>multi-hop</b> question, and it is why "
        "graph-based retrieval exists."))
    f.extend(code("""  A MULTI-HOP QUESTION

   "Which model is compared on my pollution project's dataset?"

        Air Pollution Project
                 \u2502 uses
                 \u25bc
           AQI Dataset \u2500\u2500\u2500used to train\u2500\u2500\u25b6  Random Forest Regressor
                                                            \u2502 improves
                                                            \u25bc
                                                    AQI Forecasting Result

   No single passage contains the answer. Retrieval over the graph
   traverses: project \u2192 dataset \u2192 model.""",
                  "The class of question that motivates graph retrieval. SecondBrain's graph holds "
                  "350 nodes and 500 edges, built incrementally from ingested material."))
    f.append(P(
        "Two design questions arise. First, how are nodes created \u2014 by extraction from text, by "
        "a fixed ontology, or both? SecondBrain extracts entities during curation and links them, "
        "which risks duplicate nodes for the same concept but requires no ontology maintenance. "
        "Second, how is the graph used at retrieval time? Here it is used as a <b>re-ranking "
        "signal</b>: a memory whose concepts are well connected in the graph is more central to the "
        "user's interests and ranks higher. That is the third evaluated pipeline."))

    # ---- Ch 5
    f.append(Sub("17. Temporal representation and validity intervals"))
    f.append(P(
        "A conventional database records current state. Updating a row overwrites its previous "
        "value, and history is lost. This is correct for most applications and wrong for a personal "
        "memory system, which must answer both \u201cwhat am I working on?\u201d and \u201cwhat was I "
        "working on in January?\u201d"))
    f.append(P(
        "The technique is <b>validity-interval</b> (or <b>bitemporal</b>) modelling. Every assertion "
        "carries a time range during which it holds, written [valid_from, valid_to). The interval is "
        "half-open: it includes the start and excludes the end, so adjacent intervals tile without "
        "overlap. A null valid_to means \u201cstill true\u201d, which is the sentinel for an open "
        "assertion."))
    f.extend(code("""  BEFORE supersession               AFTER a state change
  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
  \u2502 object \u2502 from       \u2502 to         \u2502      \u2502 object \u2502 from       \u2502 to         \u2502
  \u251c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2524      \u251c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2524
  \u2502 python \u2502 2026-01-25 \u2502 (null)     \u2502      \u2502 python \u2502 2026-01-25 \u2502 2026-09-18 \u2502 \u2190 closed
  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518      \u2502 java   \u2502 2026-09-18 \u2502 (null)     \u2502 \u2190 current
                                            \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518

  Query "current"  \u2192 WHERE valid_to IS NULL              \u2192 java
  Query "history"  \u2192 ORDER BY valid_from                 \u2192 python, then java
  Query "in Jan?"  \u2192 WHERE from <= Jan < to              \u2192 python""",
                  "Validity intervals make the current and the historical question answerable from "
                  "one store. Deletion would answer the first and destroy the second."))
    f.extend(callout(
        "The normalisation defect that defeated the model",
        "A temporal model is only as correct as the normalisation feeding it. In the first "
        "implementation, \u201cI am learning Python\u201d was stored under the predicate "
        "<i>learning</i> and \u201cI am now focusing on Java\u201d under <i>focus</i>. Because the "
        "predicates differed, neither assertion was recognised as superseding the other, and the "
        "graph reported both as current \u2014 reproducing precisely the failure the temporal model "
        "exists to prevent. The fix was to canonicalise both into a single predicate "
        "<i>current_focus</i> before applying supersession. The wider lesson: <i>a data model is "
        "only as correct as its normalisation, and the failure is silent.</i>"))

    # ---- Ch 6
    f.append(Sub("18. Truth maintenance and belief revision"))
    f.append(P(
        "<b>Truth maintenance</b> is the problem of keeping a store of beliefs consistent as new "
        "information arrives. The general problem is undecidable; practical systems therefore detect "
        "specific, tractable classes of inconsistency rather than attempting full consistency."))
    f.append(P(
        "The classical formulation distinguishes <b>justification-based</b> systems, which record "
        "why each belief is held and retract beliefs whose justifications are invalidated, from "
        "<b>assumption-based</b> systems, which track which combinations of assumptions are "
        "consistent. Both are more machinery than a personal assistant needs. This project "
        "implements a pragmatic subset: detect three specific conflict classes, and apply a policy "
        "rather than a full revision."))
    f.extend(table([
        ["Conflict class", "Detection signal", "Policy applied"],
        ["Temporal supersession",
         "Two assertions share a normalised predicate and differ in object; the earlier is closed",
         "Damp the older by severity; never delete"],
        ["Lexical negation",
         "Shared topic signature; one text contains a word-boundary negation the other does not",
         "Prefer the later assertion; record the conflict"],
        ["Value change",
         "Shared topic signature with high salient-word overlap, but different extracted dates or "
         "numbers",
         "Prefer the later value; damp the earlier"],
    ], [98, 210, W - 308],
        caption="Table 12 \u2014 The three conflict classes and their resolution policies. The third "
                "class was absent from the original design and was added after testing showed the "
                "first two missed the most common real case."))
    f.append(P(
        "The resolution policy deserves scrutiny. The obvious response to a contradiction is to "
        "remove the outdated item. This resolves the stale-answer problem and destroys the ability "
        "to answer historical questions \u2014 and both capabilities are legitimate. The system "
        "therefore <b>damps rather than deletes</b>: a conflict of severity <i>s</i> multiplies the "
        "item's ranking weight by (1 \u2212 0.7<i>s</i>), bounded to the range [0.3, 1.0]. The "
        "outdated item sinks below the current one without leaving the store."))
    f.extend(callout(
        "Why damping alone was not enough \u2014 and made things worse",
        "The first implementation of damping multiplied the damped score by the memory's "
        "<i>importance</i>. This promoted memories that were important in the abstract above the "
        "memory that actually answered the question, and on several benchmark questions it ranked "
        "the correct answer below an irrelevant one \u2014 so the proposed method scored worse than "
        "its baselines. The fix was to make re-ranking <b>rank-preserving</b>: the fused retrieval "
        "order supplies a prior of 1/(1+i), the damping multipliers adjust it, and importance acts "
        "only as a light tie-breaker. The principle generalises: <i>a re-ranking layer should refine "
        "an ordering, not replace it, unless it has strong evidence to do so.</i>"))

    # ---- Ch 7
    f.append(Sub("19. Memory: from cognitive science to software"))
    f.append(P(
        "The term \u2018memory\u2019 is used differently in psychology, neuroscience and computing, "
        "and the borrowings between them are often loose. It is worth being precise about which "
        "distinctions are load-bearing here."))
    f.extend(table([
        ["Distinction", "In psychology", "Computational analogue in this system"],
        ["Short-term vs long-term",
         "A small, rapidly decaying working store versus durable storage",
         "The conversation context window versus the persisted memory table and vault"],
        ["Episodic vs semantic",
         "Memory of specific events versus memory of general facts",
         "Timestamps and session records versus compiled wiki articles and graph entities"],
        ["Procedural",
         "Memory of how to perform an action",
         "Not modelled. The agents encode procedure; the memory does not learn it."],
        ["Consolidation",
         "Stabilisation and integration of memories, associated with sleep",
         "Merging near-duplicate memories into a canonical record with provenance retained"],
        ["Forgetting",
         "Adaptive decay and interference, mostly passive",
         "Deliberate, user-initiated and enforced at every retrieval surface"],
        ["Reconsolidation",
         "A recalled memory becomes labile and can be updated",
         "Not modelled. Memories are immutable; new assertions supersede rather than edit."],
    ], [88, 148, W - 236],
        caption="Table 13 \u2014 Cognitive distinctions and what the system does with each. The two "
                "deliberate omissions are as informative as the implementations: this is an "
                "engineering system, not a cognitive model, and claiming otherwise would be "
                "overreach."))
    f.append(P(
        "The strongest borrowing is consolidation, and the analogy is genuinely useful rather than "
        "decorative: a system that stores every observation separately becomes dominated by "
        "redundancy in the same way a mind that retained every perception would be overwhelmed. The "
        "weakest borrowing is forgetting, where the analogy misleads \u2014 human forgetting is "
        "passive and lossy, whereas the operation here is deliberate, precise, auditable and "
        "reversible. The system does not 'forget' in any cognitive sense; it removes content from "
        "retrieval by explicit and recorded instruction."))

    # ---- Ch 8
    f.append(Sub("20. Machine unlearning"))
    f.append(P(
        "<b>Unlearning</b> is the problem of removing the influence of specific data from a system "
        "that has already incorporated it. Its prominence is driven by privacy regulation granting a "
        "right to erasure, combined with the impracticality of retraining a large model on every "
        "such request."))
    f.append(P(
        "A retrieval-augmented system faces a narrower version of the same problem, and the "
        "narrowness is deceptive. Deleting the record from the primary table appears sufficient. It "
        "is not, because the content exists in at least five independent places, each of which can "
        "return it to a result set:"))
    f.extend(code("""  WHERE A DELETED RECORD CAN SURVIVE

   1  full-text search index        a row keyed to the memory id
   2  vector store                  an embedding, retrievable by similarity
   3  knowledge graph               nodes derived from the memory, with incident edges
   4  temporal fact store           facts extracted from the memory, still open
   5  derived research tables       importance score, conflict records, consolidation membership

   Deleting only from the primary table leaves five retrieval surfaces intact.
   The measured result: baselines leaked at rate 0.022; the adaptive
   pipeline, which enforces all five, leaked at 0.000.""",
                  "The five surfaces. The measured contrast between baselines and the adaptive "
                  "pipeline is the empirical evidence that this is a real problem and not a "
                  "theoretical one."))
    f.append(P(
        "SecondBrain's implementation tombstones the memory \u2014 keeping the row with a marker "
        "rather than deleting it, so identifiers stay stable and the removal is auditable \u2014 and "
        "then enforces exclusion at all five surfaces. Restoration re-indexes and re-admits, so the "
        "operation is reversible. The finding that <i>every baseline continued to return explicitly "
        "unlearned content</i> generalises beyond this project: any system that promises deletion "
        "while maintaining a derived index has an unlearning hole, and the hole is invisible from "
        "the primary table."))

    # ---- Ch 9
    f.append(Sub("21. Signal processing for keyword spotting"))
    f.append(P(
        "A <b>wake word</b> system must listen continuously while remaining cheap enough to run "
        "indefinitely on a laptop. It is therefore not speech recognition. It is <b>keyword "
        "spotting</b>: a small model that scores short audio frames and fires when a target phrase "
        "is recognised. Transcription happens only after the wake event."))
    f.append(P(
        "The signal chain is as follows. Audio is sampled at 16 kHz in mono, because speech "
        "recognition models generally expect that rate and the frequencies above 8 kHz contribute "
        "little to intelligibility. It is divided into fixed frames \u2014 here 80 ms, or 1280 "
        "samples \u2014 because the model expects a fixed input shape, and the frame length must "
        "match exactly or the model receives a malformed input. Each frame is scored by a small "
        "neural network, typically producing features derived from a spectrogram, and the resulting "
        "probability is thresholded."))
    f.extend(code("""  THE AUDIO PIPELINE

    microphone
        \u2502   16 kHz, mono, signed 16-bit
        \u25bc
    frames of 1280 samples (80 ms)         \u2190 must match the model exactly
        \u25bc
    mel-spectrogram features               \u2190 time-frequency representation
        \u25bc
    small ONNX network \u2192 probability per frame
        \u25bc
    threshold 0.5  \u2500\u2500\u2500\u2500\u2500\u25b6  debounce 2.5 s  \u2500\u2500\u2500\u2500\u25b6  wake event
        \u2502
        \u2514\u2500 below \u2192 discard frame

  Measured:  "Hey Jarvis" 0.9968 | silence 0.0000 | noise 0.0007 | tone 0.0018""",
                  "The keyword-spotting chain. The measured separation between the positive case and "
                  "every negative control is what justifies the 0.5 threshold."))
    f.append(P(
        "Three engineering concerns dominate. <b>Frame size</b> must match the model's expectation "
        "precisely. <b>Threshold</b> trades missed detections against false activations, and should "
        "be chosen from the measured score distribution rather than assumed. <b>Debounce</b> "
        "prevents a single spoken phrase from firing the event repeatedly as its trailing energy "
        "decays through the threshold."))
    f.extend(callout(
        "Why the negative controls matter more than the positive one",
        "A detector that fires on everything would pass a test that only checks whether it fires on "
        "the wake phrase. The informative measurements are silence, broadband noise and a pure tone "
        "\u2014 all of which scored below 0.002 while the phrase scored 0.9968. That margin is what "
        "makes the threshold defensible, and it is why the regression suite asserts the negative "
        "cases explicitly."))

    # ---- Ch 10
    f.append(Sub("22. Authentication, authorisation and scopes"))
    f.append(P(
        "<b>Authentication</b> establishes who is making a request; <b>authorisation</b> determines "
        "what they may do. This system uses both, at two levels, and the two levels are frequently "
        "confused."))
    f.extend(table([
        ["Level", "Mechanism", "What it protects"],
        ["Application access", "JWT bearer token, issued at login, attached to every request",
         "The user's own data from anyone else on the machine or network"],
        ["External service access", "OAuth tokens or app passwords, stored encrypted",
         "The user's mail and calendar accounts"],
    ], [98, 170, W - 268],
        caption="Table 14 \u2014 Two authentication layers. A defect in the first layer is what made "
                "52 endpoints return 401 while the interface showed empty panels (Volume VI)."))
    f.append(P(
        "<b>OAuth</b> lets a user grant an application limited access without revealing a password. "
        "The user authenticates with the provider; the application receives a token. Access is "
        "described by <b>scopes</b>, and providers tier scopes by sensitivity because the "
        "consequences of misuse differ enormously."))
    f.extend(code("""  SCOPE TIERS AND THEIR COSTS

   NON-SENSITIVE     openid, email, profile
                     \u2192 self-assessment only; publishing is immediate

   SENSITIVE         send mail, modify calendar events
                     \u2192 provider verification review

   RESTRICTED        read a mailbox, modify a mailbox, full mailbox access
                     \u2192 third-party security assessment (CASA)
                     \u2192 paid, several hundred dollars annually
                     \u2192 annual re-certification
                     \u2192 weeks of review

   Reading an inbox is a RESTRICTED scope. This single fact determined the
   project's entire mail strategy (deviation D7).""",
                  "The scope tiering that made the Google API route uneconomic for a single-user "
                  "application, and which the author's question about a commercial assistant "
                  "surfaced."))
    f.append(P(
        "<b>App passwords</b> are an older mechanism: once two-factor authentication is enabled, the "
        "provider issues a long random password valid only for legacy protocols such as IMAP. There "
        "is no consent screen, no verification requirement and no expiry. Their security properties "
        "differ rather than being strictly worse: they are scoped to a protocol rather than to an "
        "API, and they are revoked by the user rather than by a token service."))
    f.append(P(
        "The read-only guarantee in this project is not a configuration flag but a property of which "
        "commands are issued. IMAP distinguishes <span face='Courier'>EXAMINE</span> (open a mailbox "
        "without altering it) from <span face='Courier'>SELECT</span> (open it read-write), and "
        "<span face='Courier'>BODY.PEEK[]</span> (fetch without setting the read flag) from "
        "<span face='Courier'>BODY[]</span> (fetch and mark read). An implementation using the "
        "latter would silently mark the user's entire inbox as read the first time it synchronised "
        "\u2014 a failure the user would notice only indirectly, and one that the test suite "
        "therefore asserts against explicitly."))

    # ---- Ch 11
    f.append(Sub("23. Evaluation theory and the design of metrics"))
    f.append(P(
        "A claim that system A is better than system B is meaningless without a measurement, and the "
        "choice of measurement determines what can be concluded. This chapter explains the metrics "
        "used and, more importantly, why three of them had to be invented."))
    f.extend(table([
        ["Metric", "Definition", "Sensitivity", "Purpose"],
        ["Hit@k", "Does a relevant item appear in the top k?",
         "Position-insensitive", "Standard recall. Answers \u2018did we find it?\u2019"],
        ["MRR", "Mean of 1/rank of the first relevant item",
         "Rank-sensitive", "Answers \u2018did we find it first?\u2019"],
        ["Precision@k", "Fraction of returned items that are relevant",
         "Set-based", "Measures context efficiency"],
        ["nDCG", "Graded relevance discounted by rank",
         "Rank-sensitive, graded", "Not used: this corpus has binary relevance"],
        ["Stale@1", "Is the top-ranked item superseded or forbidden?",
         "Rank-1 specific", "Custom. Rank one is what a generator leads with"],
        ["Leak rate", "Fraction of returned items that were explicitly forgotten",
         "Set-based", "Custom. Detects unlearning holes"],
        ["Duplicate rate", "Fraction of within-query pairs that are near-identical",
         "Set-based", "Custom. Measures wasted context budget"],
    ], [76, 158, 96, W - 330],
        caption="Table 15 \u2014 Metrics and their sensitivities. The custom metrics were necessary "
                "because the standard ones proved unable to distinguish the systems."))
    f.extend(callout(
        "The result that made the custom metrics necessary",
        "The expectation before measuring was that the research layer would improve Hit@5. It did "
        "not: all four pipelines reached 1.000. Every system found the relevant memory somewhere in "
        "its top five. Had the evaluation stopped there, the honest conclusion would have been that "
        "seven components accomplished nothing measurable \u2014 and that conclusion would have been "
        "wrong. What differed was the <i>ordering</i> and the <i>staleness of what came first</i>. "
        "The general lesson: <i>a metric that saturates conveys no information, and saturation "
        "should be investigated rather than reported.</i>"))
    f.append(P(
        "Two further methodological points apply. First, <b>metrics must be computed over the "
        "appropriate population</b>: including abstention and removal questions, which have no "
        "correct answer by construction, would depress every system equally and conceal real "
        "differences, so Hit@k and MRR are computed over answerable questions only. Second, "
        "<b>reproducibility is a precondition, not a nicety</b>: two consecutive runs of a "
        "non-deterministic harness cannot support a comparison, and this project's benchmark was "
        "made deterministic by clearing derived state between runs and by using a deterministic "
        "retrieval fallback."))

    # ---- Ch 12
    f.append(Sub("24. Software verification theory"))
    f.append(P(
        "Verification is the discipline of establishing that software does what is claimed. The "
        "techniques used here map onto the classical levels, and the project's central methodological "
        "lesson concerns the boundary between them."))
    f.extend(table([
        ["Level", "Technique used here", "What it can establish"],
        ["Static analysis", "A linter failing on undefined identifiers and unused symbols",
         "That every referenced name is defined. Cannot establish that defined names are correct."],
        ["Static integration checks", "Eight checks: imports resolve, icons exist, client methods "
                                      "exist, route modules exist, URLs match, preload surface "
                                      "complete, Python compiles",
         "That the parts agree on names and shapes. Cannot establish that a request succeeds."],
        ["Contract checking", "Frontend URLs matched against backend routes, including both branches "
                              "of ternary expressions",
         "That no call targets a non-existent route. Cannot establish that the route works."],
        ["Render and mount testing", "Every interface route rendered and mounted so effects execute",
         "That components do not crash on construction or on effect. Cannot establish that data is "
         "correct."],
        ["Functional suites", "Eleven backend suites plus eight specialised suites, roughly 400 "
                              "assertions",
         "That specified behaviours hold under specified conditions."],
        ["Live endpoint sweep", "Boot the server, authenticate, call every route, report status and "
                                "timing",
         "That every route answers without a server error under real conditions."],
    ], [98, 210, W - 308],
        caption="Table 16 \u2014 The verification levels used, ordered by what they can establish. "
                "This ordering is the report's most important methodological claim."))
    f.extend(callout(
        "The lesson that cost the most time",
        "The first error audit used correct and useful techniques. It found the visible crash and one "
        "more of the same class, and it produced permanent tooling that has caught defects since. It "
        "could not possibly have found the project's most serious defect, because <i>a login function "
        "that raises before comparing a password is syntactically valid code.</i> No amount of static "
        "analysis detects a connection that is missing rather than wrong. Only executing the system "
        "and attempting to log in revealed it, in minutes. The general principle: <i>static analysis "
        "finds what is written incorrectly; only execution finds what is written plausibly but "
        "connected to nothing.</i>"))

    # ---- Ch 13
    f.append(Sub("25. Local inference and resource constraints"))
    f.append(P(
        "Running a language model locally rather than calling a hosted service changes the design "
        "space in ways that are easy to underestimate. The constraint is memory: a model's weights "
        "must fit in GPU memory alongside the activations needed for inference."))
    f.extend(code("""  WHY MODEL SIZE IS BOUNDED HERE

   GPU memory available              \u2248 6 GB   (RTX 3050 Laptop)
   weights at 16-bit precision       \u2248 2 bytes per parameter
   activation and context overhead   \u2248 1\u20132 GB at typical context lengths

   \u2234 practical ceiling            \u2248 2\u20133 billion parameters at 16-bit
   \u2234 a 3B model was selected, and the design assumes it may be absent

   QUANTISATION trades precision for size:
      16-bit  \u2192  8-bit   roughly halves memory, small quality loss
       8-bit  \u2192  4-bit   halves again, larger quality loss

   The consequence for architecture: every model-dependent feature was made
   OPTIONAL, and each degrades to a deterministic non-neural fallback.""",
                  "The resource constraint and its architectural consequence. The ceiling on model "
                  "size is why the optionality principle is not merely tidiness."))
    f.append(P(
        "Three practical lessons emerged. First, <b>token streaming matters more locally than "
        "remotely</b>, because a small model's first token can be slow while subsequent tokens flow "
        "quickly; showing text as it arrives makes the latency tolerable. Second, <b>a configured "
        "model may be absent</b> \u2014 a model can be re-pulled under a different tag, or a "
        "different machine may have a different set \u2014 so the system queries what is actually "
        "installed and selects accordingly rather than failing with a 404. Third, and most "
        "importantly, <b>a local model is a dependency that can be unavailable</b>, and the "
        "architecture must therefore treat every model call as fallible."))

    # ---- Ch 14
    f.append(Sub("26. Engineering practice: what the project taught"))
    f.append(P(
        "This final chapter of the theory volume abstracts the practical lessons, because they "
        "generalise beyond this codebase."))
    f.extend(table([
        ["Principle", "Stated plainly", "Evidence from this project"],
        ["A build proves compilation, not execution",
         "Succeeding to build is necessary and nowhere near sufficient.",
         "A missing component import passed every build and crashed the application at runtime. "
         "Twice."],
        ["A silent failure is worse than a loud one",
         "The cost of a defect is proportional to how long it remains undetected, not to its "
         "severity.",
         "Broken authentication produced empty panels rather than errors, and remained undetected "
         "through a full audit."],
        ["An error code is a claim about causation",
         "Choosing a status code is choosing where the reader will look for the fault.",
         "Reporting a missing record as an upstream failure sent investigation in exactly the wrong "
         "direction."],
        ["Test the claim, not the code",
         "If a claim cannot be tested, it should not be made.",
         "Writing one assertion per paper claim forced the question \u2018what would this look like "
         "if it were broken?\u2019 and found several domain-model defects."],
        ["Prefer negative controls",
         "A test that only checks the positive case passes on a system that does nothing.",
         "Silence must not trigger the wake word; unrelated memories must not be duplicates; a "
         "forgotten memory must not appear in any retrieval mode."],
        ["Prove that the check can fail",
         "A green result is only meaningful if red is possible.",
         "The crash-class defect was deliberately re-introduced to confirm the gate refused it. "
         "Doing this also exposed three false positives in the checkers themselves."],
        ["Destructive operations must prove ownership",
         "A cleanup routine must be able to demonstrate that what it is deleting is its own.",
         "A test deleted 123 of the author's real memory cards because it could not distinguish its "
         "own artefacts from genuine data."],
        ["Centralise cross-cutting concerns",
         "Duplicated plumbing drifts, and the drift is invisible.",
         "33 call sites each independently failed to attach an authentication token."],
        ["A model is only as good as its normalisation",
         "Correct code over an incorrectly normalised model is silently wrong.",
         "Two facts describing one state were stored under different predicates, so neither "
         "superseded the other \u2014 reproducing exactly the failure the component existed to "
         "prevent."],
        ["Instrumentation compounds",
         "The value of verification is realised on every subsequent change, not on the change that "
         "motivated it.",
         "Four phases of work were completed in a single day once the fifteen gates existed, because "
         "each change could be validated in under a minute."],
    ], [104, 158, W - 262],
        caption="Table 17 \u2014 Ten engineering principles, each with the evidence from this project "
                "that produced it. These are the most transferable output of the work."))
    f.append(PageBreak())

    return f
