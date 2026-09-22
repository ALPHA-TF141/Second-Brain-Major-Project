"""Big report - Volume I (origin, vision, user inputs) and Volume II (architecture)."""
from datetime import datetime

from reportlab.platypus import PageBreak, Paragraph, Spacer

from report_builder_base import BODY_W, B, P, S, Section, Sub, callout, code, esc, table

W = BODY_W


def build():
    f = []

    # ================================================================ COVER
    f.append(Spacer(1, 78))
    f.append(Paragraph("SecondBrain", S["title"]))
    f.append(Paragraph(
        "The Complete Engineering Record<br/>"
        "From an empty folder to a published research contribution",
        S["subtitle"]))
    f.append(Spacer(1, 14))
    f.append(Paragraph(
        "Every idea considered, every direction abandoned, every defect found,<br/>"
        "every constraint imposed, and every concept the system is built upon.",
        S["docmeta"]))
    f.append(Spacer(1, 52))

    meta = [
        ["Project", "SecondBrain \u2014 an autonomous personal cognitive knowledge system"],
        ["Repository", "github.com/ALPHA-TF141/Second-Brain-Major-Project"],
        ["Supervisor", "Dr. P S Anu Rakhi, Assistant Professor, School of Computing"],
        ["Authors", "Maria Immanuel L (vtu24334) \u00b7 Vigneshwaran S (vtu24372)"],
        ["Programme", "B.Tech, Computer Science and Engineering"],
        ["Institution", "Vel Tech Rangarajan Dr. Sagunthala R&D Institute of Science and Technology"],
        ["Compiled", datetime.now().strftime("%d %B %Y")],
        ["Volume structure", "Eight volumes plus four appendices"],
        ["Source of truth", "231 Git commits; every figure in this report was read from the "
                            "repository or from measured benchmark output"],
    ]
    f.extend(table([[Paragraph(f"<b>{k}</b>", S["tabc"]), Paragraph(esc(v), S["tabc"])] for k, v in meta],
                   [105, W - 105], header=False))
    f.append(PageBreak())

    # ============================================================= PREAMBLE
    f.append(Section("Preamble"))
    f.append(P(
        "This is not a user manual and not a research paper. It is the record of how a piece of "
        "software came to be \u2014 including the parts that went wrong. It documents the reasoning "
        "behind decisions, the alternatives that were rejected, the moments where the plan changed "
        "direction, and the theory that underpins each component."))
    f.append(P(
        "It is written this way deliberately, for three reasons. First, a system of this size cannot "
        "be understood from its source code alone: the code shows what was built, never why, and "
        "never what was tried first and discarded. Second, an engineering project is judged on "
        "judgement rather than on adherence, and judgement is only visible in the deviations. Third, "
        "and most practically, the authors needed a document that a supervisor or examiner could read "
        "and understand the whole system from, without reading 17,000 lines of Python."))
    f.append(P(
        "Throughout, a distinction is maintained between three things that are easy to confuse. "
        "<b>What was intended</b> is recorded as stated. <b>What was built</b> is recorded as "
        "verified. <b>What was measured</b> is recorded as measured, with the method named. Where "
        "something was not measured, this document says so rather than estimating."))

    f.extend(callout(
        "On the honesty of this record",
        "Twenty-seven defects are documented here, including one in which a verification test deleted "
        "123 of the authors' genuine memory cards. That incident is recorded in full, with its cause "
        "and its fix, because a defect register that omits the worst defect is not a defect register. "
        "The same principle applies to the research results: the headline finding is a negative one, "
        "and it is reported as such."))
    f.append(PageBreak())

    # ============================================================== TOC (Vol I-II)
    f.append(Section("Table of Contents"))
    f.append(Paragraph(
        "<b>Volume I \u2014 Origin and Vision</b>", S["toc1"]))
    for item in [
        "1. The problem, stated plainly",
        "2. Why the first framing was wrong",
        "3. Personal knowledge management: the theory",
        "4. The reference point, analysed properly",
        "5. The author's brief: every constraint recorded",
    ]:
        f.append(Paragraph(item, S["toc2"]))
    f.append(Paragraph("<b>Volume II \u2014 Architecture</b>", S["toc1"]))
    for item in [
        "6. Design philosophy",
        "7. The seven-stage pipeline",
        "8. The data model in full",
        "9. The agent layer",
        "10. The API surface",
        "11. The desktop shell and interface",
        "12. Technology selection and its trade-offs",
    ]:
        f.append(Paragraph(item, S["toc2"]))
    f.append(Paragraph("<b>Volume III \u2014 Build Chronology</b>", S["toc1"]))
    f.append(Paragraph("Phases 0 through 7, each with the request, the reasoning, and the failures.",
                       S["toc2"]))
    f.append(Paragraph("<b>Volume IV \u2014 Concepts and Theory</b>", S["toc1"]))
    f.append(Paragraph("Fourteen chapters covering the theory the system is built on.", S["toc2"]))
    f.append(Paragraph("<b>Volume V \u2014 Deviations</b>", S["toc1"]))
    f.append(Paragraph("<b>Volume VI \u2014 Defects</b>", S["toc1"]))
    f.append(Paragraph("<b>Volume VII \u2014 Research Contribution</b>", S["toc1"]))
    f.append(Paragraph("<b>Volume VIII \u2014 Engineering Practice</b>", S["toc1"]))
    f.append(Paragraph("<b>Appendices</b>", S["toc1"]))
    f.append(Paragraph("A schema \u00b7 B API \u00b7 C file map \u00b7 D glossary \u00b7 E timeline \u00b7 F input log",
                       S["toc2"]))
    f.append(PageBreak())

    # =============================================================== VOLUME I
    f.append(Section("Volume I \u2014 Origin and Vision"))
    f.append(Spacer(1, 4))

    f.append(Sub("1. The problem, stated plainly"))
    f.append(P(
        "The project began with a specific and unglamorous frustration. The author reads technical "
        "material constantly: documentation, papers, lecture notes, videos, email, lecture slides. "
        "The material was genuinely read \u2014 comprehension was not the problem. The problem was "
        "that it could not be <i>recalled</i> when it later mattered."))
    f.append(P(
        "A concrete version of the problem: six weeks after reading about a technique, a question "
        "arises that the technique would answer. The person <i>knows</i> they have read something "
        "relevant. They cannot remember where, or what it said exactly. They search for it, fail, and "
        "either re-read the whole source or proceed without it. Multiply this by every subject the "
        "person studies and the cost is substantial."))
    f.extend(callout(
        "The distinction that shaped the entire project",
        "The problem is not <b>storage</b>. Storage is free and solved. The problem is not even "
        "<b>search</b>, in the ordinary sense \u2014 a file search would find the document, and a web "
        "search would find a hundred copies of it. The problem is <b>recall under a question</b>: "
        "being able to ask \u2018what did I learn about X?\u2019 and receive an answer assembled from "
        "everything one has encountered, without having predicted in advance that X would matter. "
        "This distinction eliminates most conventional solutions, because all of them require the "
        "user to have foreseen the question."))
    f.append(P(
        "Three properties follow from that framing, and they recur throughout this document as design "
        "constraints."))
    f.extend(table([
        ["Property", "Why it is required", "What it rules out"],
        ["Capture must be automatic",
         "The user cannot decide in advance what will matter, so they cannot be asked to save it.",
         "Manual note-taking, bookmarking, tagging, and any system that begins with an empty page."],
        ["What matters must be inferred",
         "Determining relevance is the work the user is bad at; delegating it back to them recreates "
         "the original problem.",
         "Folder structures, manual categorisation, and any scheme requiring the user to maintain it."],
        ["Questions are natural language",
         "The question is formed at the moment of need, in the user's own words, not as keywords.",
         "Keyword search, filter panels, and query languages."],
    ], [98, 168, W - 266],
        caption="Table 1 \u2014 The three properties that follow from the problem statement, and what "
                "each of them eliminates."))

    f.append(Sub("2. Why the first framing was wrong"))
    f.append(P(
        "The first design was a note-taking application. It had a text editor, a search box, and a "
        "tag system. It would have taken a fortnight to build and would have been abandoned within "
        "that fortnight, for a reason worth stating precisely because it is the reason most personal "
        "knowledge tools fail."))
    f.append(P(
        "Such a system asks the user to perform a judgement each time they encounter something: is "
        "this worth saving? If so, where does it belong? What should it be tagged with? That "
        "judgement is exactly the capability the user lacks \u2014 if they could reliably judge what "
        "would matter in six weeks, they would not have the recall problem. The system therefore "
        "demands the one skill whose absence created the need for it."))
    f.extend(code("""  THE VICIOUS CIRCLE

      user cannot predict what will matter
                 \u2502
                 \u25bc
      so cannot curate reliably
                 \u2502
                 \u25bc
      so the system fills with noise, or stays empty
                 \u2502
                 \u25bc
      so the user stops using it
                 \u2502
                 \u25bc
      and the recall problem remains

  BREAKING IT: move the judgement from the human to the machine.
  That is a much harder engineering problem, and it is the
  problem this project actually solves.""",
                  "Why manual curation defeats the purpose. This realisation is the single most "
                  "important conceptual step in the project, and everything downstream follows from "
                  "it."))
    f.append(P(
        "The reframed goal therefore became: <i>capture everything automatically, decide relevance "
        "algorithmically, and answer questions in natural language afterwards.</i> The user should "
        "never perform a filing action. This moves the entire difficulty of the project into one "
        "place \u2014 the quality of the machine's judgement about what matters \u2014 and that is "
        "where the research contribution later emerged."))

    f.append(Sub("3. Personal knowledge management: the theory"))
    f.append(P(
        "Personal knowledge management (PKM) is a body of practice, developed largely outside "
        "academic computer science, concerned with how an individual captures, organises, retrieves "
        "and expresses what they know. Three frameworks from that tradition shaped this system's "
        "architecture, and each maps onto a concrete implementation decision."))

    f.append(Paragraph("<b>PARA</b> \u2014 Projects, Areas, Resources, Archives", S["h3"]))
    f.append(P(
        "Devised by Tiago Forte, PARA argues that information should be filed by <i>actionability</i> "
        "rather than by subject. A Project is something with a deadline and an outcome. An Area is an "
        "ongoing responsibility with no end date. A Resource is material of future interest. An "
        "Archive is anything inactive. The insight is that subject-based filing decays, because the "
        "same subject appears in multiple contexts, whereas actionability-based filing stays stable."))
    f.append(P(
        "The machine analogue implemented here is the <b>importance score</b>, discussed in detail in "
        "Volume IV. A memory's score includes a <i>future utility</i> term that rewards actionable "
        "content (deadlines, instructions, invoices) and project-linked content, and the "
        "<i>temporal</i> term decays with age so that inactive material sinks naturally. The system "
        "does not maintain folders, but it reproduces the essential distinction PARA makes: active "
        "material ranks above archival material, without the user deciding which is which."))

    f.append(Paragraph("<b>CODE</b> \u2014 Capture, Organise, Distil, Express", S["h3"]))
    f.append(P(
        "Forte's second framework describes a four-stage pipeline through which information passes. "
        "This maps onto the system's seven-stage pipeline almost directly, with the added stages "
        "being machine-specific:"))
    f.extend(table([
        ["CODE stage", "Human activity", "Implemented as"],
        ["Capture", "Record the thing before it is lost",
         "Screenshot capture with OCR; IMAP mail ingestion; iCalendar ingestion; web and social "
         "scrapers"],
        ["Organise", "Put it somewhere it can be found again",
         "Curation scoring, memory cards, the knowledge graph, and the retrieval index"],
        ["Distil", "Reduce it to what actually matters",
         "The wiki compiler, which maintains one article per topic domain and rewrites it as new "
         "evidence arrives"],
        ["Express", "Produce something new from it",
         "Question answering over accumulated memory; generated deliverables; spoken briefings"],
    ], [62, 152, W - 214],
        caption="Table 2 \u2014 The CODE pipeline and its implementation. The two additional "
                "pipeline stages not present in CODE \u2014 Retrieve and Learn \u2014 exist because a "
                "machine system must search its own store and update itself."))

    f.append(Paragraph("<b>Progressive summarisation</b>", S["h3"]))
    f.append(P(
        "The practice of repeatedly condensing a note \u2014 highlight the important sentences, then "
        "bold the important words within those, then extract the essence into a summary. The theory "
        "is that a note becomes more valuable as it becomes shorter, because its information density "
        "rises and it can be re-read quickly."))
    f.append(P(
        "This is implemented as the <b>wiki compiler</b>, and it is worth examining because it "
        "produces a counter-intuitive property. As new material is ingested, the compiler does not "
        "append. It <i>rewrites</i> the topic article, folding the new evidence into the existing "
        "synthesis. The corpus therefore becomes shorter and better as it grows, which is the "
        "opposite of how a conventional archive behaves, and it is what makes question answering over "
        "long-term memory tractable at all \u2014 a bounded set of dense articles is searchable; an "
        "unbounded set of fragments is not."))
    f.extend(code("""  GROWTH BEHAVIOUR COMPARISON

  Conventional archive              SecondBrain wiki compiler
  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500              \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

  1 source    \u2192  1 fragment           1 source    \u2192  1 article
  10 sources  \u2192 10 fragments          10 sources  \u2192  1 article (richer)
  100 sources \u2192 100 fragments         100 sources \u2192  1 article (denser)
                    \u2191                                  \u2191
              search gets noisier            search gets sharper""",
                  "Progressive summarisation applied at corpus scale. The measured result at the time "
                  "of writing was 93 compiled articles from several hundred ingested items."))

    f.extend(callout(
        "What PKM theory supplied, and what it could not",
        "The PKM tradition supplied the <i>stages</i> and the intuition that summarisation adds value. "
        "It could not supply a formal criterion for importance, a mechanism for handling "
        "contradiction, or a way to measure whether any of it worked. Those gaps are precisely where "
        "the project became engineering and research rather than practice, and they are addressed in "
        "Volumes IV and VII."))

    f.append(Sub("4. The reference point, analysed properly"))
    f.append(P(
        "The author's stated design target was JARVIS, the assistant from the Iron Man films, and two "
        "reference videos were supplied: the workshop scene from <i>Iron Man 2</i>, and a compilation "
        "of the abilities of Tony Stark's several artificial intelligences. The author's instruction "
        "was to watch them and report what was understood."))
    f.append(P(
        "It is worth recording that the videos could not be watched directly \u2014 neither carries "
        "subtitles, so transcript extraction returned nothing, and no video playback was available. "
        "The analysis was therefore performed from the titles, descriptions, and a first-principles "
        "examination of what the depicted assistant actually does. Rather than obscure this, the "
        "report states it, and the analysis below stands on its own reasoning."))
    f.append(P(
        "The superficial reading of those films is that JARVIS is a voice assistant with holographic "
        "displays. Acting on that reading produces a system that is a talking interface with "
        "animations \u2014 visually impressive, functionally empty, and a very common failure mode in "
        "student projects that cite this reference. The useful reading examines what the character "
        "<i>does</i> and identifies five behaviours:"))
    f.extend(table([
        ["Behaviour", "What it looks like on screen", "Why it matters"],
        ["There is no interface",
         "Stark walks in and speaks. Nothing is launched, nothing is opened.",
         "The assistant is ambient rather than an application. Any design requiring the user to "
         "navigate to it has already failed this test."],
        ["It speaks first",
         "JARVIS initiates \u2014 reporting status, raising problems, announcing arrivals.",
         "A conventional assistant only ever responds. Initiative is the property that distinguishes "
         "an assistant from a search box."],
        ["It holds state",
         "It knows what Stark was doing before he entered the room.",
         "Requires persistent memory across sessions, which is the entire premise of a second brain."],
        ["It acts",
         "It does not report that the simulation is missing; it runs the simulation.",
         "Turns the system from an advisor into an instrument. Requires write access, which carries "
         "risk and is therefore deliberately constrained here."],
        ["It has judgement",
         "It warns, objects, and occasionally refuses.",
         "Requires the system to hold opinions about its own knowledge \u2014 which is what "
         "confidence scoring, contradiction detection and gap detection provide."],
    ], [78, 158, W - 236],
        caption="Table 3 \u2014 The five behaviours, separated from their visual presentation. The "
                "analysis concluded that the voice is the least essential element."))
    f.append(P(
        "The conclusion drawn from that analysis shaped the later build phases decisively. If the "
        "voice were the essence, effort should go into speech quality and visual effects. If "
        "<i>presence</i> and <i>initiative</i> are the essence, effort should go into being "
        "addressable by name and speaking without being asked. The second reading was adopted, and it "
        "is why the project later implemented offline wake-word detection and proactive spoken "
        "announcements rather than further animation work."))

    f.append(Sub("5. The author's brief: every constraint recorded"))
    f.append(P(
        "Constraints are recorded here in the order they were given, because each eliminated design "
        "options and the elimination is what produced the final architecture. This table is the "
        "closest thing in this report to a requirements specification."))
    f.extend(table([
        ["#", "Constraint as given", "Consequence for the design"],
        ["1", "Use a free local language model; do not pay for OpenAI",
         "All inference runs through Ollama on the laptop's GPU. Removes per-token cost and keeps "
         "data on-device, but caps model size to what fits in 6 GB of VRAM, which in turn motivated "
         "the decision to make every model-dependent feature optional."],
        ["2", "It must not look like a project interface; it must feel like a personal AI",
         "Rejected dashboards, side banners and admin-panel aesthetics. Directly caused three "
         "successive interface rebuilds (deviation D5)."],
        ["3", "Every module must be visible as a real tab; do not hide functionality",
         "Produced the fifteen-tab operating-system shell, and eliminated an earlier design that "
         "used a single dashboard with drawers."],
        ["4", "No fake functionality \u2014 if a service is not connected, say so",
         "Removed all seeded demo data from interactive screens. This single instruction is why the "
         "Gmail and Calendar screens show explicit disconnection states and why the demo rows in the "
         "task list were later removed. It also shaped the research layer: measured results only."],
        ["5", "Build the scraping software yourself; do not pay for Apify or SupaData",
         "Produced a native ingestion stack on free libraries, and established the principle applied "
         "later to mail and calendar (deviation D7) that saved a recurring verification cost."],
        ["6", "The assistant must be reachable by name, with a transparent floating structure",
         "Produced the transparent always-on-top orb window and later the offline wake-word "
         "implementation. 'Transparent' required changes at three layers simultaneously."],
        ["7", "Do not use Marvel-copy material; it should feel futuristic but be original",
         "The assistant is named and addressed distinctively, and the visual language is derived from "
         "generic science-fiction conventions rather than film assets."],
        ["8", "The project must satisfy an IEEE paper requirement",
         "Forced the addition of a research layer: baseline comparison, quantitative measurement, "
         "and honest limitation reporting. This constraint is what turned a good application into a "
         "defensible contribution."],
        ["9", "I need the paper to be genuinely novel, and the project must actually be what the "
              "paper claims",
         "Produced the pre-publication audit which found six of seven claimed contributions "
         "unimplemented, and caused the implementation-first ordering recorded as deviation D9."],
    ], [22, 158, W - 180],
        caption="Table 4 \u2014 The author's constraints and their direct architectural consequences. "
                "Constraint 9 is the one that most changed the project."))
    f.extend(callout(
        "On the relationship between the authors and the implementation",
        "Nine of the thirteen documented deviations were driven by a constraint in this table. The "
        "author's role was consistently to supply the <i>requirement and the judgement</i> \u2014 what "
        "the system must do, what would be unacceptable, and when a result was not convincing \u2014 "
        "while the implementation explored the technical space and reported honestly when it found "
        "that a stated plan was wrong. The most productive interactions were the two questions that "
        "challenged an assumption directly: <i>\u2018why can Grok connect and this cannot?\u2019</i>, "
        "which exposed a US$540\u2013$1,800 recurring cost and led to a completely different "
        "integration strategy; and <i>\u2018why does it answer once and then stop?\u2019</i>, which "
        "exposed a missing event handler that had been invisible in review."))
    f.append(PageBreak())

    # ============================================================== VOLUME II
    f.append(Section("Volume II \u2014 Architecture"))
    f.append(Spacer(1, 4))

    f.append(Sub("6. Design philosophy"))
    f.append(P(
        "Four principles governed every architectural decision. They are stated first because the "
        "specific choices in the following sections are all consequences of them."))

    f.extend(table([
        ["Principle", "Statement", "Consequence if violated"],
        ["Optionality",
         "No single dependency is load-bearing. Every model, index, integration and library is "
         "imported conditionally and degrades to a working fallback.",
         "A single missing package makes the application unusable. This was observed early: the "
         "system would not start because one undeclared package was absent."],
        ["Additivity",
         "New capability is added alongside existing capability, never by rewriting it. The research "
         "layer observes memories through foreign keys and modifies nothing in the capture pipeline.",
         "The working system breaks while being extended, which is the most expensive kind of "
         "failure because the working state is lost."],
        ["Testability by construction",
         "Every component must be exercisable without the components it depends on. Storage, "
         "retrieval, extraction and policy are separated so each can be driven directly.",
         "Components can only be tested end-to-end, so a failure cannot be localised."],
        ["Honest degradation",
         "When something is unavailable, the system says so and continues. It never substitutes "
         "plausible-looking content for a failed operation.",
         "The user cannot distinguish working from broken, which is the defect class that consumed "
         "the most time in this project."],
    ], [86, 190, W - 276],
        caption="Table 5 \u2014 The four architectural principles."))

    f.append(Sub("7. The seven-stage pipeline"))
    f.extend(code("""  \u2460 CAPTURE     \u2192  \u2461 UNDERSTAND  \u2192  \u2462 STORE  \u2192  \u2463 RETRIEVE
                                              \u2502
                                              \u25bc
                        \u2467 LEARN  \u2190  \u2465 EXPLAIN  \u2190  \u2464 REASON""",
                  "The pipeline. Stage \u2467 (\u2018LEARN\u2019) feeds back into stages \u2461 and "
                  "\u2462, which is what makes the memory adaptive rather than a static archive."))
    f.extend(table([
        ["Stage", "Responsibility", "Implemented in", "Failure behaviour if unavailable"],
        ["\u2460 Capture",
         "Acquire raw material: screen frames, email, calendar events, web pages, social posts, "
         "voice input",
         "capture/, integrations/, services/",
         "System runs; other sources continue; the unavailable source reports its state"],
        ["\u2461 Understand",
         "Extract meaning: OCR text, entities, topics, temporal facts, importance scores, "
         "contradictions",
         "agents/, extraction/, entities/, research/",
         "Falls back to keyword extraction; temporal and conflict features disable themselves"],
        ["\u2462 Store",
         "Persist to two independent stores: relational (49 tables) and the Git-backed vault "
         "(JSON cards, images, wiki, graph)",
         "models/, memory/, agents/vault_agent.py",
         "Vault sync is retried in the background; local persistence is unaffected"],
        ["\u2463 Retrieve",
         "Select relevant context. Four interchangeable strategies: dense, hybrid, graph, adaptive",
         "search/, semantic_search/, ranking/, research/pipeline.py",
         "Falls back through dense \u2192 TF-IDF \u2192 keyword; never returns nothing silently"],
        ["\u2464 Reason",
         "Generate an answer from the assembled context",
         "rag/, llm/, prompts/",
         "Falls back to extractive summary of the retrieved context, and says which mode it used"],
        ["\u2465 Explain",
         "Deliver the answer: text, speech, notification, task",
         "routes/, websocket/, voice/, proactive",
         "Each delivery channel fails independently"],
        ["\u2467 Learn",
         "Update importance, detect gaps, consolidate duplicates, close superseded facts",
         "research/",
         "Feature disables itself; retrieval continues with the previous state"],
    ], [48, 128, 112, W - 288],
        caption="Table 6 \u2014 The seven stages, with the modules that implement them and the "
                "degradation path if each is unavailable. The fourth column is the practical "
                "expression of the optionality principle."))

    f.append(Sub("8. The data model in full"))
    f.append(P(
        "The database contains 49 tables. They divide into five groups, and the grouping mirrors the "
        "chronology of the build: capture came first, then knowledge organisation, then conversation, "
        "then platform, and finally the research layer."))
    f.extend(code("""  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
  CAPTURE \u00b7 11 tables
    memory_sessions      a capture period, typed by activity
    screenshots          raw frames, pruned after the hero is elected
    activity_logs        window and application focus events
    app_usage            per-application time within a session
    clipboard_logs       copied text as a knowledge signal
    extracted_text       OCR output per frame
    ocr_metadata         OCR engine state and confidence
    processed_sessions   sessions whose OCR pass is complete
    detected_topics      topics identified within a session
    semantic_chunks      the unit of embedding and retrieval
    settings             per-user configuration

  KNOWLEDGE \u00b7 17 tables
    memories             the central record: title, content, hash, source, topic
    memory_tags          tags attached to a memory
    memory_relationships typed links between memories
    search_index         the full-text surface used by keyword retrieval
    session_summaries    a summary per capture session
    graph_nodes          entities in the knowledge graph
    graph_edges          typed relationships between entities
    concept_clusters     grouped nodes
    graph_metadata       build state of the graph
    topic_relationships  topic-level links
    learning_progression ordered topic sequences
    vector_memories      the embedding record per memory
    memory_clusters      semantic clusters over memories
    semantic_relationships  similarity-derived links
    embedding_jobs       the embedding work queue
    search_history       every query, for evaluation and personalisation
    timeline_events      chronological event log

  CONVERSATION \u00b7 11 tables
    conversations        a question-answering thread
    messages             individual turns
    retrieved_memories   which memories were used for which answer (provenance)
    conversation_context assembled context per turn
    ai_summaries         generated summaries
    ai_feedback          user ratings, the personalisation signal
    voice_sessions       spoken interaction sessions
    transcripts          speech-to-text output with confidence
    conversation_audio   generated speech artefacts
    language_preferences language, voice and wake-word configuration
    voice_commands       recognised commands and their outcomes

  RESEARCH \u00b7 7 tables  \u2190 added last; observes memories, never owns them
    memory_scores        the eight-term importance score per memory
    temporal_facts       (subject, predicate, object) with validity intervals
    memory_conflicts     detected contradictions and their resolution policy
    memory_consolidations clusters merged, with member identifiers retained
    forgotten_memories   tombstones for unlearned content
    knowledge_gaps       detected exposure-without-depth concepts
    research_runs        benchmark executions and their metrics

  PLATFORM \u00b7 3 tables
    users                accounts
    sessions             authentication sessions
    activities           the audit log
  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500""",
                  "The complete schema. The research group is shown last because it was built last, "
                  "and because its position in the design is deliberately peripheral: it observes "
                  "the knowledge group and is removable without affecting it."))

    f.extend(callout(
        "The dual-store decision",
        "Every memory is written to two independent stores. The relational store is fast, queryable "
        "and holds the derived research state. The Git-backed vault holds immutable JSON cards, "
        "compressed hero images, compiled wiki articles and the knowledge graph, and is synchronised "
        "to a remote repository every sixty seconds. The duplication is deliberate and the reasoning "
        "is durability: if the database is corrupted, the vault reconstructs it; if the vault is "
        "lost, the database survives. Neither is a backup of the other \u2014 they are genuinely "
        "independent representations with different shapes, and the system is designed so that either "
        "can be rebuilt from the other."))

    f.append(Sub("9. The agent layer"))
    f.append(P(
        "Intelligence is distributed across ten specialised agents rather than concentrated in one "
        "monolithic service. Each agent has a single responsibility, its own failure mode, and no "
        "knowledge of the others' internals. The reasoning is the same as for the pipeline stages: a "
        "large component that does everything cannot be tested, instrumented or replaced."))
    f.extend(table([
        ["Agent", "Trigger", "Responsibility", "If it fails"],
        ["Curation", "Every capture", "Score captured text for information density; reject "
                                       "low-value frames before they are stored",
         "Every frame is stored; storage grows and retrieval noise increases"],
        ["Vault", "On card creation", "Write JSON cards, compress hero images, commit and push to "
                                      "the remote repository",
         "Memory exists only locally; a background retry loop attempts sync"],
        ["Wiki compiler", "On card creation", "Fold new evidence into the per-topic article, "
                                              "rewriting rather than appending",
         "Knowledge accumulates as fragments and is never distilled"],
        ["Insight", "Periodic sweep", "Detect collisions between separate topics; raise proactive "
                                      "alerts",
         "The system answers but never volunteers anything"],
        ["Social ingestion", "On demand or scheduled", "Extract transcripts and articles from video, "
                                                       "social and web sources",
         "Those sources must be read manually"],
        ["Mail ingestion", "Scheduled interval", "Read new mail read-only; create memories, tasks, "
                                                 "notifications and spoken alerts",
         "The inbox remains separate from the knowledge base"],
        ["Deliverable", "On demand", "Generate documents synthesised from accumulated memory",
         "The system can explain but cannot produce artefacts"],
        ["Proactive voice", "On agent event", "Apply priority, quiet-hours, cooldown and dedupe "
                                              "policy, then speak",
         "Alerts are filed silently and the assistant loses initiative"],
        ["Wake word", "Always listening", "Score audio frames; fire a wake event on the target "
                                          "phrase",
         "The hotkey still summons the assistant; hands-free is lost"],
        ["Embedding worker", "On memory creation", "Queue and compute embeddings in the background",
         "Semantic retrieval falls back to TF-IDF; the system continues"],
    ], [72, 62, 168, W - 302],
        caption="Table 7 \u2014 The ten agents. Note that every entry in the final column is a "
                "degradation rather than a failure: this is the optionality principle applied at the "
                "agent level."))

    f.append(Sub("10. The API surface"))
    f.append(P(
        "The backend exposes 162 endpoints across 150 paths, grouped into 19 route modules. The "
        "surface is larger than a typical application of this size because it is the boundary at "
        "which every capability is testable \u2014 and the test strategy depends on being able to "
        "drive each capability independently."))
    f.extend(table([
        ["Group", "Purpose", "Representative endpoints"],
        ["health, auth, sessions", "Liveness, login, session lifecycle",
         "GET /api/health \u00b7 POST /api/auth/login \u00b7 POST /api/sessions"],
        ["capture", "Screen capture control and retrieval",
         "POST /api/capture/start \u00b7 GET /api/capture/status \u00b7 GET /api/capture/live-preview"],
        ["ocr", "Text extraction pipeline",
         "GET /api/ocr/texts \u00b7 POST /api/ocr/sessions/{id}/process \u00b7 GET /api/ocr/topics"],
        ["memory", "The archive: sessions, memories, relationships, timeline",
         "GET /api/memory/search \u00b7 GET /api/memory/timeline \u00b7 POST /api/memory/rebuild"],
        ["semantic", "Embedding search and clustering",
         "POST /api/semantic/hybrid-search \u00b7 GET /api/semantic/status \u00b7 GET /api/semantic/clusters"],
        ["graph", "Knowledge graph and vault",
         "GET /api/graph/nodes \u00b7 GET /api/graph/vault/wiki \u00b7 POST /api/graph/vault/sync"],
        ["chat", "Question answering with provenance",
         "POST /api/chat/ask \u00b7 GET /api/chat/conversations/{id}/retrieved"],
        ["voice", "Speech sessions, transcripts, preferences",
         "POST /api/voice/sessions \u00b7 GET /api/voice/status \u00b7 PUT /api/voice/preferences"],
        ["activities, timeline, settings", "Audit log and configuration",
         "GET /api/activities \u00b7 GET /api/timeline \u00b7 PUT /api/settings"],
        ["social", "Native content ingestion",
         "POST /api/social/ingest-url \u00b7 GET /api/social/status"],
        ["os", "Tasks, reminders, calendar, projects, automations, activities, notifications",
         "GET/POST /api/os/tasks \u00b7 GET /api/os/intelligence \u00b7 GET /api/os/notifications"],
        ["google", "OAuth-connected Gmail and Calendar",
         "POST /api/google/connect \u00b7 GET /api/google/callback \u00b7 GET /api/google/gmail/messages"],
        ["mail", "Unified mail and calendar, provider-agnostic",
         "POST /api/mail/imap/connect \u00b7 GET /api/mail/messages \u00b7 POST /api/mail/sync"],
        ["proactive", "Wake word and proactive voice control",
         "GET /api/proactive/status \u00b7 POST /api/proactive/wake/test \u00b7 POST /api/proactive/announce"],
        ["research", "The seven research contributions",
         "POST /api/research/benchmark \u00b7 POST /api/research/forget \u00b7 GET /api/research/temporal"],
        ["WebSocket", "Live push: capture events, agent activity, wake, speech",
         "/ws/live \u00b7 /ws/voice \u00b7 /ws/chat"],
    ], [92, 150, W - 242],
        caption="Table 8 \u2014 The API surface by group. The 'mail' and 'google' groups are "
                "deliberately parallel: the first abstracts over both connection methods, the second "
                "exposes the OAuth path directly for accounts where it is the only option."))

    f.append(Sub("11. The desktop shell and interface"))
    f.append(P(
        "The application is an Electron desktop shell containing a React interface. Electron was not "
        "a preference but a requirement: the floating assistant must be a borderless, transparent, "
        "always-on-top window positioned over the desktop, and a browser cannot create one. Given "
        "that constraint, the interface is ordinary React with hash routing."))
    f.extend(table([
        ["Surface", "Implementation", "Notes"],
        ["Main window", "Framed Electron window, hash-routed React application",
         "Nineteen routes. Fifteen are primary navigation tabs; the remainder are aliases and the "
         "standalone orb."],
        ["Assistant orb", "Second BrowserWindow: frameless, transparent, always-on-top, not in the "
                          "taskbar, bottom-right",
         "Transparency required simultaneous changes to Electron's window flags, the document root "
         "CSS and the body background (see defect D16)."],
        ["Tray icon", "Persistent with a visibility toggle",
         "Added after the application became invisible when hidden with no way to restore it."],
        ["Command palette", "Ctrl+K overlay with backend search",
         "Provides keyboard access to every destination without navigating the rail."],
        ["Live channel", "WebSocket from backend to renderer",
         "Carries capture events, agent activity, wake events and speech requests. The renderer holds "
         "no policy \u2014 it renders what the backend decides."],
    ], [86, 190, W - 276],
        caption="Table 9 \u2014 The interface surfaces. The division of responsibility matters: the "
                "backend decides <i>what</i> should happen, the renderer decides <i>how it looks</i>, "
                "and neither duplicates the other's logic."))

    f.append(Sub("12. Technology selection and its trade-offs"))
    f.append(P(
        "Each choice below is recorded with the alternative that was rejected, because the reason for "
        "a decision is only visible against what it displaced."))
    f.extend(table([
        ["Decision", "Chosen", "Rejected alternative", "Reason"],
        ["Language model", "Ollama with a small local model",
         "Hosted API (paid)",
         "Author constraint 1. Local inference also keeps all personal data on-device, which matters "
         "because the corpus is a life record."],
        ["Model transport", "Ollama's native API",
         "Its OpenAI-compatible endpoint",
         "The compatibility layer returned 'model not found' for models that existed. A shim adds a "
         "failure mode without adding capability."],
        ["Primary store", "SQLite",
         "PostgreSQL or MySQL",
         "Single-user, single-machine. A server database would add deployment complexity for no "
         "benefit at this scale."],
        ["Vector store", "ChromaDB, optional",
         "FAISS, Qdrant, Pinecone",
         "Local and persistent by default. Made optional so the system runs without it."],
        ["Dense retrieval fallback", "TF-IDF cosine",
         "Require an embedding model",
         "Determinism and zero-download startup. It also made the benchmark reproducible, which the "
         "research required."],
        ["Mail access", "IMAP with app passwords, plus OAuth as a secondary path",
         "Google OAuth only",
         "The default path must not require a Google Cloud project, a consent screen, or an annual "
         "security assessment. See deviation D7."],
        ["Calendar access", "Private iCalendar address",
         "Google Calendar API",
         "Requires no authentication at all, and is read-only by construction."],
        ["Wake word", "openWakeWord, offline",
         "Cloud keyword spotting (Porcupine, Google)",
         "No audio leaves the machine, no account, no per-request cost. The trade-off is that it is a "
         "keyword spotter, not speech recognition."],
        ["Speech recognition", "Browser Web Speech API",
         "Whisper on-device",
         "Zero setup and no model download. Whisper remains available through the optional pack for "
         "offline accuracy."],
        ["Interface framework", "React 18 with hash routing",
         "Server-rendered or vanilla",
         "Electron requires a static bundle; hash routing avoids file-protocol path issues."],
        ["Desktop shell", "Electron",
         "Tauri or a native application",
         "Required for a transparent overlay window. Tauri was considered but the transparency "
         "requirements were better supported by Electron at the time."],
    ], [76, 108, 92, W - 276],
        caption="Table 10 \u2014 Every significant technology decision, with the rejected alternative "
                "and the reason. This table is the clearest single statement of the project's "
                "engineering philosophy."))
    f.extend(callout(
        "The pattern across every decision",
        "In almost every case the rejected alternative was the <i>more capable</i> option, and it was "
        "rejected for a reason of ownership, cost, or failure visibility. A hosted language model is "
        "more capable than a 3B local model. Google's Calendar API is more capable than an iCalendar "
        "feed. Cloud speech recognition is more accurate than the browser's. In each case the less "
        "capable option was chosen because it could be owned outright, could not generate a recurring "
        "bill, and could not fail in a way the user would not understand. For a personal system "
        "holding a life record, those properties outweighed capability."))
    f.append(PageBreak())

    return f
