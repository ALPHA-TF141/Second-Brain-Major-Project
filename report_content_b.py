"""Development report - Parts IV-IX and appendices (theory, deviations, defects, verification, research)."""
from reportlab.platypus import PageBreak, Paragraph, Spacer

from report_builder_base import BODY_W, B, P, S, Section, Sub, callout, code, table

W = BODY_W


def build():
    f = []

    # ================================================================ PART IV
    f.append(Section("Part IV \u2014 Concepts and Theory"))
    f.append(Spacer(1, 4))
    f.append(P(
        "This part explains the ideas the system is built from. It is written for a reader who knows "
        "none of the terminology; each concept is introduced from first principles, then connected to "
        "the specific place in SecondBrain where it is used. The order follows the pipeline."))

    # ---- 1 retrieval
    f.append(Sub("Retrieval-augmented generation"))
    f.append(P(
        "A language model knows what was in its training data and nothing else. It cannot know what "
        "the user read this morning. The naive remedy is to paste the relevant material into the "
        "prompt, which works but requires knowing what is relevant \u2014 and that is the hard part, "
        "because the model's context window is finite."))
    f.append(P(
        "<b>Retrieval-augmented generation</b> (RAG) solves this by splitting the problem in two. A "
        "retrieval stage selects a small number of relevant passages from a large store; a generation "
        "stage passes only those passages, together with the question, to the language model. The model "
        "is therefore never asked to remember the corpus \u2014 only to reason over the handful of "
        "passages it has been handed."))
    f.extend(code("""  Question
     \u2502
     \u25bc
  [ retrieve k relevant passages from the store ]     \u2190 the hard problem
     \u2502
     \u25bc
  Prompt = instructions + retrieved passages + question
     \u2502
     \u25bc
  [ language model ]  \u2192  answer + citation of which passages were used""",
                  "The RAG pattern. Note that answer quality is bounded by retrieval quality: if the "
                  "right passage is not retrieved, no amount of model capability can recover it."))
    f.extend(callout(
        "The assumption that fails in a personal store",
        "Textbook RAG assumes the retrieved passages are consistent, current and mutually "
        "compatible. In a personal memory store none of those hold. The author wrote in January that "
        "they were learning Python and in September that they had moved to Java. Both statements are "
        "in the store, both are true <i>of their time</i>, and a retriever that ranks by similarity to "
        "the query \u201cwhat am I working on?\u201d has no mechanism to prefer the later one. The "
        "answer is confidently wrong, and every retrieved passage is faithful to its source \u2014 so "
        "no faithfulness metric detects the error. This is the failure the research layer exists to "
        "address."))

    # ---- 2 embeddings
    f.append(Sub("Embeddings and vector search"))
    f.append(P(
        "To retrieve by meaning rather than by keyword, text must be converted into a mathematical "
        "object that captures meaning. An <b>embedding</b> is a list of numbers \u2014 typically a few "
        "hundred \u2014 produced by a neural network trained so that texts with similar meaning "
        "produce similar lists. The list is a point in a high-dimensional space; \u201csimilar "
        "meaning\u201d becomes \u201cnearby points\u201d."))
    f.extend(code("""  "I want to learn Java"        \u2192  [ 0.21, -0.83,  0.44, \u2026 ]
  "What language am I studying?" \u2192  [ 0.19, -0.79,  0.41, \u2026 ]   \u2190 close together
  "The cat sat on the mat"       \u2192  [-0.55,  0.12, -0.90, \u2026 ]   \u2190 far away

  Similarity is measured by cosine of the angle between the vectors:
      cos(\u03b8) = (A \u00b7 B) / (|A| \u00b7 |B|)     ranges from -1 to 1""",
                  "Embeddings turn semantic similarity into geometry, which is why retrieval by "
                  "meaning is possible at all."))
    f.extend(table([
        ["Term", "Meaning", "Where it appears in SecondBrain"],
        ["Dimension", "Length of the vector; more dimensions capture finer distinctions",
         "Sentence-transformers produces 384-dimensional vectors"],
        ["Cosine similarity", "Normalised dot product; measures angle, ignores magnitude",
         "The basis of both vector search and consolidation clustering"],
        ["Chunk", "A passage small enough to embed meaningfully",
         "Semantic chunks are formed at ingestion and stored in `semantic_chunks`"],
        ["Vector store", "An index optimised for nearest-neighbour search",
         "ChromaDB, optional; TF-IDF serves as a deterministic fallback"],
        ["Top-k", "How many candidates retrieval returns",
         "Eight by default, four times the final result count"],
    ], [78, 190, W - 268],
        caption="Table 6 \u2014 Embedding vocabulary and its concrete instantiation."))
    f.append(P(
        "A practical consequence worth stating: embeddings are <i>optional</i> in SecondBrain. When no "
        "embedding model is available, retrieval falls back to TF-IDF, a classical information-retrieval "
        "weighting scheme that needs no neural network. The fallback is worse at synonymy but entirely "
        "serviceable, and its determinism is what made the benchmark reproducible. A design that "
        "requires a 90 MB download before it can answer any question is a fragile design."))

    # ---- 3 knowledge graph
    f.append(Sub("Knowledge graphs"))
    f.append(P(
        "A vector store answers \u201cwhich passages resemble this question?\u201d It cannot answer "
        "\u201chow are these things related?\u201d because it has no notion of relation \u2014 only of "
        "similarity. A <b>knowledge graph</b> supplies the missing structure: information is "
        "represented as <i>nodes</i> (entities) connected by <i>edges</i> (typed relationships). "
        "Where a vector captures resemblance, a graph captures structure."))
    f.extend(code("""        Air Pollution Project
                 \u2502
        \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
        \u25bc        \u25bc        \u25bc
  AQI Dataset  Random Forest  IEEE Paper
                 \u2502
              \u25bc
           Python 3.12

  A question spanning two branches \u2014 "compare the model used on my
  pollution project against the paper's method" \u2014 requires traversing
  the graph. No single passage contains the answer.""",
                  "Why a graph is necessary. Multi-hop questions have answers that exist only in the "
                  "structure, not in any one document."))
    f.append(P(
        "SecondBrain maintains a graph of 350 nodes and 500 edges, built incrementally by the curation "
        "and vault agents as material is ingested. The graph is used for two purposes: as a "
        "re-ranking signal (a memory whose concepts are well connected is more central to the user's "
        "interests) and as the substrate for knowledge-gap detection, described below."))

    # ---- 4 temporal
    f.append(Sub("Temporal knowledge representation"))
    f.append(P(
        "Standard databases record what is true <i>now</i> \u2014 updating a row overwrites its "
        "previous value and history is lost. A personal memory system needs the opposite: it must "
        "answer both \u201cwhat am I working on?\u201d and \u201cwhat was I working on in "
        "January?\u201d, so it must retain the fact that a value <i>changed</i>."))
    f.append(P(
        "The technique is <b>bitemporal</b> or <b>validity-interval</b> modelling: every assertion "
        "carries a time range [valid_from, valid_to) during which it was true. A null valid_to means "
        "\u201cstill true\u201d. When a new assertion arrives that conflicts with an open one, the old "
        "assertion is <i>closed</i> \u2014 its valid_to is set and it is linked to its replacement "
        "\u2014 rather than deleted."))
    f.extend(code("""  Facts about the user, as stored:

  \u2502 predicate       \u2502 object                \u2502 valid_from \u2502 valid_to \u2502
  \u251c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2524
  \u2502 current_focus   \u2502 python                \u2502 2026-01-25 \u2502 2026-09-18 \u2502  \u2190 closed
  \u2502 current_focus   \u2502 java                  \u2502 2026-09-18 \u2502   (open)   \u2502  \u2190 current
  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518

  "What am I working on?"        \u2192 selects the OPEN row   \u2192 java
  "What was I working on before?" \u2192 selects the closed row \u2192 python""",
                  "Validity intervals make both the current and the historical question answerable "
                  "from one store."))
    f.extend(callout(
        "A subtlety that cost a measurable amount of accuracy",
        "Facts must be grouped by <i>state class</i>, not by the words used to express them. In the "
        "first implementation, \u201cI am learning Python\u201d was recorded under the predicate "
        "<i>learning</i> and \u201cI am now focusing on Java\u201d under <i>focus</i>. Because the "
        "predicates differed, neither superseded the other and the graph reported both as current "
        "\u2014 reproducing exactly the failure the temporal model exists to prevent. The fix was to "
        "canonicalise both into a single predicate <i>current_focus</i> before applying supersession. "
        "The lesson generalises: <i>a data model is only as correct as its normalisation.</i>"))

    # ---- 5 contradiction
    f.append(Sub("Contradiction and truth maintenance"))
    f.append(P(
        "In artificial intelligence, <b>truth maintenance</b> is the problem of keeping a knowledge "
        "base consistent as beliefs change. The general problem is undecidable; practical systems "
        "detect specific, tractable classes of conflict. SecondBrain detects three."))
    f.extend(table([
        ["Conflict class", "Definition", "Example from the corpus"],
        ["Temporal supersession", "A memory asserts something a later memory has replaced",
         "\u201clearning Python\u201d then \u201cnow focusing on Java\u201d"],
        ["Lexical negation", "Two memories share a topic and one denies what the other asserts",
         "\u201cthe October deadline was cancelled\u201d"],
        ["Value change", "Two memories share a topic and carry different dated or numeric values",
         "\u201cdeadline 15 October\u201d vs \u201cdeadline now 30 September\u201d"],
    ], [98, 168, W - 266],
        caption="Table 7 \u2014 The three detectable conflict classes. The third was not in the "
                "original design; it was added after testing showed the first two missed the most "
                "common real case."))
    f.append(P(
        "The design decision that matters is what to do once a conflict is found. The obvious response "
        "is to delete the outdated item. This solves the stale-answer problem but destroys the ability "
        "to answer historical questions \u2014 and both capabilities are legitimate. SecondBrain "
        "therefore <i>damps</i> rather than deletes: a conflict of severity <i>s</i> multiplies the "
        "memory's ranking weight by (1 \u2212 0.7s), bounded between 0.3 and 1.0. The outdated item "
        "sinks below the current one without leaving the store."))
    f.extend(callout(
        "Why damping needed a further correction",
        "Damping alone was not sufficient, and the first version actually made results worse. The "
        "reason is that the re-ranking function multiplied the damped score by the memory's "
        "<i>importance</i>, which promoted memories that scored highly on abstract importance but "
        "were less relevant to the question \u2014 including, on several benchmark questions, above "
        "the correct answer. The correction was to make the re-ranking <b>rank-preserving</b>: the "
        "fused retrieval order supplies a prior, the damping multipliers adjust it, and importance "
        "acts only as a light tie-breaker. The general principle is that a re-ranking layer should "
        "<i>refine</i> an ordering, not replace it, unless it has strong evidence to do so."))

    # ---- 6 consolidation
    f.append(Sub("Memory consolidation"))
    f.append(P(
        "The term is borrowed from neuroscience, where it describes the process by which short-term "
        "memories are stabilised and integrated into long-term storage during sleep. The computational "
        "analogue is equally useful: a memory store that keeps every observation separately becomes "
        "dominated by redundancy, and retrieval wastes its limited context budget on the same content "
        "repeated."))
    f.extend(code("""  BEFORE consolidation                    AFTER
  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500                    \u2500\u2500\u2500\u2500\u2500
  "FastAPI routing uses decorators      "FastAPI routing maps HTTP
   to map HTTP methods and paths         methods and paths to Python
   to Python functions"                  functions using decorators"
  "FastAPI routing maps HTTP              \u2502
   methods and paths to Python            \u2514\u2500 merged ids [11, 12] retained
   functions using decorators"            \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
  "FastAPI routing maps HTTP methods
   and paths to Python functions"       Context reduced by ~66%
                                        Provenance preserved""",
                  "Consolidation merges near-duplicates into one canonical record while retaining the "
                  "identifiers of everything merged, so an answer can still cite its origins."))
    f.append(P(
        "Determining \u201cnear-duplicate\u201d requires a threshold, and the threshold matters. The "
        "figure commonly recommended in practice is 0.90 cosine similarity. Measuring the actual "
        "distribution showed that genuinely reworded duplicates \u2014 the common real case, where the "
        "same page is captured twice with small differences \u2014 score around 0.82, while unrelated "
        "memories score below 0.30. A 0.90 threshold therefore missed <i>every</i> reworded duplicate. "
        "The threshold was set to 0.78 from the measured distribution."))
    f.extend(callout(
        "A methodological point, not a technical one",
        "Choosing 0.78 because it made the test pass would have been fitting the method to the "
        "evaluation. The value was chosen from the measured score distribution \u2014 an 0.82 cluster "
        "of true duplicates separated by a wide margin from sub-0.30 non-duplicates \u2014 and the "
        "benchmark was then run to confirm it. The distinction matters because a threshold tuned on "
        "the test set would not transfer to real data, and no reviewer could tell the difference from "
        "the reported numbers alone."))

    # ---- 7 unlearning
    f.append(Sub("Machine unlearning"))
    f.append(P(
        "<b>Unlearning</b> is the problem of removing the influence of specific data from a trained "
        "system. It rose to prominence because privacy regulation grants a right to erasure, and "
        "retraining a model from scratch on every request is impractical."))
    f.append(P(
        "SecondBrain's version of the problem is narrower but shares its essential difficulty. Deleting "
        "a row from the memory table does not remove the content from retrieval, because the content "
        "exists in at least five independent places: the full-text index, the vector embedding, the "
        "knowledge-graph nodes derived from it, the temporal facts extracted from it, and the derived "
        "scores and conflict records. Unless exclusion is enforced at <i>every</i> surface, the "
        "content can re-enter a result set."))
    f.extend(code("""  User says: forget this.

  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
  \u2502 1  search_index      row deleted                            \u2502
  \u2502 2  vector store      embedding removed (not merely filtered) \u2502
  \u2502 3  graph_nodes       node and incident edges deleted         \u2502
  \u2502 4  temporal_facts    closed and detached from source        \u2502
  \u2502 5  scores/conflicts  derived rows purged                     \u2502
  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
       plus: a tombstone row, so the removal is auditable and reversible

  Measured outcome:
      baselines  \u2192 still return the forgotten content   (leak rate 0.022)
      adaptive   \u2192 never returns it                     (leak rate 0.000)""",
                  "Forgetting must be enforced at every surface. The measured asymmetry between the "
                  "baselines and the adaptive pipeline is the evidence that this is not automatic."))
    f.append(P(
        "The result that every baseline continues to return explicitly removed content is worth "
        "emphasising. It means that a system promising deletion while maintaining a derived index has "
        "an unlearning hole, and that the hole is not visible from the primary table. This is a "
        "finding about retrieval systems generally, not about SecondBrain specifically."))

    # ---- 8 gaps
    f.append(Sub("Knowledge-gap detection"))
    f.append(P(
        "A memory system can know what the user has encountered. Determining what they "
        "<i>understand</i> is harder, and the distinction matters because a concept can be seen "
        "constantly without ever being learned \u2014 it appears on reading lists, in courses to be "
        "studied, in tangents."))
    f.append(P(
        "The signal is not frequency but <i>shape</i>. A concept the user understands appears as the "
        "subject of explanatory statements, recurs across separate sessions, and is connected to "
        "other concepts in the graph. A concept merely encountered appears in lists, carries few "
        "connections, and is never explained. The implemented measure combines these:"))
    f.extend(code("""  exposure   = min(1, mentions / 12)
  depth      = 0.45 \u00b7 explained_ratio \u00b7 3      \u2190 appeared with explanatory context
             + 0.30 \u00b7 subject_ratio  \u00b7 3      \u2190 appeared as subject of a sentence
             + 0.25 \u00b7 session_spread           \u2190 recurred over time

  gap        = exposure \u00d7 (1 \u2212 depth) \u00d7 (1 \u2212 0.5 \u00b7 connectivity)""",
                  "The connectivity factor is essential: without it a well-understood but frequently "
                  "mentioned concept would be misreported as a gap."))

    # ---- 9 wake word
    f.append(Sub("Wake-word detection"))
    f.append(P(
        "A wake word is a always-listening keyword spotter: a small model that continuously scores "
        "short audio frames and fires when the target phrase is recognised. It is deliberately not "
        "full speech recognition \u2014 that would be wasteful, since the system must listen "
        "indefinitely but only transcribe once summoned."))
    f.append(P(
        "The implementation processes 16 kHz mono audio in 80-millisecond frames (1280 samples each) "
        "through a small ONNX neural network, producing a probability per frame. The engineering "
        "concerns are frame size, which must match the model's expectation exactly; threshold, which "
        "trades missed detections against false activations; and debounce, which prevents a single "
        "spoken phrase from firing the event several times as it rings out."))
    f.extend(table([
        ["Input", "Measured score", "Outcome", "Meaning"],
        ["Spoken \u201cHey Jarvis\u201d", "0.9968", "fires", "The model detects the phrase decisively"],
        ["Silence", "0.0000", "no fire", "No activity is not mistaken for speech"],
        ["White noise", "0.0007", "no fire", "Broadband noise is rejected"],
        ["440 Hz tone", "0.0018", "no fire", "A pure tone is not speech"],
    ], [128, 84, 62, W - 274],
        caption="Table 8 \u2014 Measured wake-word discrimination. The threshold of 0.5 sits in a wide "
                "margin between the positive case and every negative control."))
    f.append(P(
        "These figures were obtained by generating synthetic speech, decoding it to the correct sample "
        "rate, and passing it through the project's own scoring function \u2014 not through a mock. "
        "The distinction matters because the first implementation used an API signature that does not "
        "exist in the installed library version, and would have failed silently on the target machine. "
        "Only testing against the real library caught it."))

    # ---- 10 oauth/imap
    f.append(Sub("Authentication: OAuth, app passwords and scopes"))
    f.append(P(
        "<b>OAuth</b> lets a user grant an application limited access to an account without revealing "
        "their password. The user authenticates with the provider directly; the application receives "
        "a token. Access is described by <b>scopes</b> \u2014 named permission bundles such as "
        "<span face='Courier'>gmail.readonly</span>."))
    f.append(P(
        "Providers classify scopes by sensitivity, and the classification determines what an "
        "application must do before it can use them."))
    f.extend(table([
        ["Classification", "Example scopes", "Requirement to publish"],
        ["Non-sensitive", "openid, email, profile", "Self-assessment only; publishing is immediate"],
        ["Sensitive", "gmail.send, calendar.events", "Google OAuth verification review"],
        ["Restricted", "gmail.readonly, gmail.modify, mail.google.com",
         "Third-party security assessment (CASA), annual re-certification"],
    ], [88, 152, W - 240],
        caption="Table 9 \u2014 Scope tiers. Reading an inbox is a restricted scope, which is why a "
                "personal project cannot reasonably publish an application that does it over the "
                "Gmail API."))
    f.append(P(
        "<b>App passwords</b> are an older mechanism: once two-factor authentication is enabled, the "
        "provider can issue a long random password valid only for legacy protocols such as IMAP. No "
        "consent screen, no verification, no expiry. For a single-user desktop application they are "
        "the correct tool, which is why they became the default path."))
    f.extend(code("""  IMAP commands that make reading read-only

    EXAMINE mailbox        \u2190 opens a mailbox WITHOUT marking it read
    SELECT  mailbox        \u2190 opens it read-write (avoid)

    BODY.PEEK[HEADER]      \u2190 fetches a header WITHOUT setting the \\Seen flag
    BODY[HEADER]           \u2190 fetches it and marks the message read (avoid)

  Both distinctions are asserted by the test suite: an implementation that
  uses SELECT and BODY would silently mark the user's entire inbox as read
  the first time it synced.""",
                  "The read-only guarantee is not a configuration flag; it is a property of which "
                  "IMAP commands are issued. Getting it wrong would have been invisible until the "
                  "user noticed their inbox had been emptied of unread state."))

    # ---- 11 evaluation
    f.append(Sub("Evaluation methodology"))
    f.append(P(
        "A claim that a system is better must be supported by a measurement, and the choice of "
        "measurement determines what can be concluded. The metrics used here, and what each is for:"))
    f.extend(table([
        ["Metric", "Definition", "Purpose"],
        ["Hit@k", "Did a relevant item appear in the top k?",
         "Standard recall measure. Suffices when the task is \u201cfind something relevant\u201d."],
        ["MRR", "Mean of 1/rank of the first relevant item",
         "Rank-sensitive. Distinguishes systems that find the right item first from those that find "
         "it fifth."],
        ["Precision@k", "Fraction of returned items that are relevant",
         "Measures context efficiency: irrelevant items consume the model's finite context."],
        ["Stale@1", "Is the TOP-ranked item superseded or forbidden?",
         "Custom to this work. Rank one is what a generator leads with, so staleness there is what "
         "produces a confidently wrong answer."],
        ["Leak rate", "Fraction of returned items that were explicitly forgotten",
         "Custom to this work. Detects unlearning holes."],
        ["Duplicate rate", "Fraction of within-query pairs that are near-identical",
         "Custom to this work. Measures wasted context budget."],
        ["Latency", "Wall-clock time for the full question set",
         "Reports cost honestly; improvements are not free."],
    ], [76, 152, W - 228],
        caption="Table 10 \u2014 Metrics and their purposes. The three custom metrics were necessary "
                "because the standard ones proved unable to distinguish the systems tested."))
    f.extend(callout(
        "Why custom metrics were needed",
        "The expectation before measuring was that the research layer would improve Hit@5. It did "
        "not: every pipeline reached 1.000. Had the evaluation stopped there, the honest conclusion "
        "would have been that seven components accomplished nothing measurable. The custom metrics "
        "revealed what actually differed \u2014 the ordering and the staleness of the top result. This "
        "is a general lesson about evaluating retrieval systems: <i>a metric that saturates conveys no "
        "information, and saturation should be investigated rather than reported.</i>"))
    f.append(PageBreak())

    # ================================================================= PART V
    f.append(Section("Part V \u2014 Register of Deviations"))
    f.append(Spacer(1, 4))
    f.append(P(
        "A deviation register records every point at which the implementation departed from the plan, "
        "with the reason. It exists because a project without one cannot be evaluated for judgement "
        "\u2014 only for adherence. The deviations are listed chronologically and each records what "
        "was planned, what was done instead, and why."))

    deviations = [
        ("D1", "Note-taking application \u2192 automatic capture system",
         "Build a note-taking system with search.",
         "Abandoned notes entirely; built an autonomous capture pipeline.",
         "A system whose value depends on manual curation will be abandoned within a fortnight, "
         "because the user is bad at curation \u2014 that is why they have the problem. Moving the "
         "judgement from human to machine is harder engineering but is the only version that works."),
        ("D2", "OpenAI-compatible API \u2192 native Ollama API",
         "Call the local model through its OpenAI-compatible endpoint.",
         "Call Ollama's native /api/chat endpoint directly.",
         "The compatibility layer returned \u201cmodel not found\u201d for a model that existed. A "
         "shim adds a failure mode without adding capability when talking to one's own infrastructure."),
        ("D3", "Store all screenshots \u2192 elect one hero image per period",
         "Keep every captured frame.",
         "Score frames for information density and retain only the best per information period.",
         "Storing everything grows without bound and retrieves nothing useful. The criterion for "
         "\u201cbest\u201d must be measurable, and text density is."),
        ("D4", "Paid scraping APIs \u2192 self-hosted free scrapers",
         "Use Apify and SupaData for social ingestion.",
         "Built a native stack on free libraries; ingestion fell to 0.98 s.",
         "Directed by the user: build the capability rather than rent it. The general principle "
         "\u2014 replace recurring cost with one-off engineering \u2014 was then applied unprompted "
         "to mail and calendar (see D7)."),
        ("D5", "Dashboard interface \u2192 operating-system shell \u2192 holographic core \u2192 fifteen-tab OS",
         "A clean dashboard.",
         "Three successive rebuilds, landing on persistent navigation plus an ambient command centre.",
         "The requirement could not be specified in advance. Each rebuild eliminated a wrong "
         "interpretation: the first showed the visual language was wrong, the second showed that "
         "removing navigation makes functionality unfindable."),
        ("D6", "Written-only assistant \u2192 voice, orb, and spoken alerts",
         "Answer questions in the interface.",
         "Added speech in and out, a transparent floating orb, proactive spoken announcements.",
         "Derived from the user's reference videos once they were analysed for substance rather than "
         "appearance: the defining characteristic of the reference assistant is that it speaks first."),
        ("D7", "Google OAuth only \u2192 IMAP and iCal as the default path",
         "Connect the accounts through Google OAuth and publish the application.",
         "Added a second, credential-free path and made it the default.",
         "Investigating the user's question about a competitor revealed that reading an inbox "
         "requires a restricted scope, and publishing one requires an annual security assessment of "
         "roughly US$540\u2013$1,800. For a single-user application the cost is indefensible, and "
         "staying unverified forces weekly reconnection. OAuth is not the only way to read a mailbox."),
        ("D8", "Text-only presence \u2192 wake word",
         "The user presses a hotkey to summon the assistant.",
         "Added offline wake-word detection so the assistant can be addressed by name.",
         "A name is most of what distinguishes an assistant that is present from an application that "
         "is opened. Implemented offline so that no audio leaves the machine."),
        ("D9", "Paper first \u2192 implementation first",
         "Write the paper describing the seven contributions.",
         "Audited the claims, found six of seven unimplemented, built them, then wrote the paper from "
         "measured results.",
         "A paper written before the software would have described something that did not exist. The "
         "audit also changed the paper: the predicted result was wrong, so the paper reports the "
         "measured result instead."),
        ("D10", "Ranking by importance \u2192 rank-preserving re-ranking",
         "Re-rank retrieved memories by their computed importance score.",
         "Use the retrieval order as a prior and apply damping as an adjustment.",
         "Sorting by importance was actively harmful, promoting memories that were important in the "
         "abstract above the memory that actually answered the question. A re-ranking layer should "
         "refine an ordering, not replace it."),
        ("D11", "Two conflict classes \u2192 three",
         "Detect temporal supersession and lexical negation.",
         "Added numeric and dated value-change detection.",
         "Testing showed the first two missed the most common real case \u2014 a deadline that moved, "
         "expressed in the third person with no negation word and no first-person state claim."),
        ("D12", "Assumed similarity threshold \u2192 measured threshold",
         "Use 0.90 cosine similarity to identify duplicates.",
         "Set the threshold to 0.78 from the measured distribution.",
         "Reworded duplicates, the common real case, score around 0.82. A 0.90 threshold missed every "
         "one of them."),
        ("D13", "Ablation table \u2192 stated limitation",
         "Report a per-component ablation table.",
         "Removed the table and stated in the paper that the factorised ablation is not yet run.",
         "Some cells had not been independently measured. A table implying measurements that were not "
         "taken is worse than an honest gap, and a reviewer would eventually ask."),
    ]
    rows = [["#", "Dimension", "Planned", "Actual", "Reason"]]
    for d in deviations:
        rows.append([d[0], d[1], d[2], d[3], d[4]])
    f.extend(table([[r[0], r[1], r[2], r[3], r[4]] for r in rows],
                   [26, 92, 108, 120, W - 346],
                   caption="Table 11 \u2014 Deviation register. D7 and D9 are the two that most "
                           "changed the project's trajectory."))
    f.append(PageBreak())

    # ================================================================= PART VI
    f.append(Section("Part VI \u2014 Register of Defects"))
    f.append(Spacer(1, 4))
    f.append(P(
        "This register records the significant defects encountered, each with its symptom, the "
        "underlying cause, the fix, and the general lesson. It is organised by cause rather than by "
        "chronology, because the causes cluster and the clustering is the useful information: the "
        "same four or five mistakes account for almost every failure in the project."))

    f.append(Sub("Class 1 \u2014 Missing or unverified dependency"))
    f.extend(table([
        ["Defect", "Symptom", "Root cause", "Fix and lesson"],
        ["Undefined identifier, twice",
         "Blank screen on the home route; a second instance waiting on another tab",
         "A component was used in JSX without being imported. A production build succeeds because "
         "the code is syntactically valid.",
         "Imports added; a linter rule added to fail the build on any undefined identifier. Lesson: "
         "<i>a successful build proves compilation, not execution.</i>"],
        ["Undeclared package imports",
         "A fresh installation crashed on startup",
         "Two packages were imported directly but listed only as transitive dependencies of another "
         "package. They resolved on the development machine by accident.",
         "Both declared explicitly. Lesson: <i>a direct import needs a direct declaration</i>, "
         "however it happens to resolve locally."],
        ["Library version drift",
         "Wake-word detection would have failed silently on the target machine",
         "The model-loading call used an argument name that exists in a newer release than the one "
         "installed.",
         "Loading made version-tolerant, trying four constructor shapes. Lesson: <i>test against the "
         "installed version, not the documented one.</i>"],
        ["Dependency resolution failure",
         "A clean installation refused to complete",
         "A linting package declared a peer requirement for a major version of its host that "
         "contradicted the pinned version.",
         "Versions aligned to the installed major. Lesson: <i>a build that only works on the "
         "author's machine is not a build.</i>"],
    ], [78, 108, 150, W - 336], caption="Table 12 \u2014 Dependency defects."))

    f.append(Sub("Class 2 \u2014 Silent failure"))
    f.extend(table([
        ["Defect", "Symptom", "Root cause", "Fix and lesson"],
        ["Authentication never worked",
         "The interface rendered normally but showed empty data everywhere",
         "A service referenced a configuration object without importing it, so the login function "
         "raised before comparing any password. The frontend swallowed the error, so the application "
         "ran with no token and 52 protected endpoints returned 401 \u2014 which the interface "
         "rendered as an empty state.",
         "Import added. Lesson: <i>the most dangerous failure is the one the interface "
         "misrepresents</i>. Found only by running the server and logging in, not by reading code."],
        ["Thirty-three unauthenticated calls",
         "Even a correct login would not have authenticated most screens",
         "Screens used a raw browser fetch, which does not attach the token, instead of the "
         "application's authenticated client.",
         "A single authenticated helper plus a mechanical replacement across 18 files. Lesson: "
         "<i>duplicated plumbing drifts; centralise the cross-cutting concern.</i>"],
        ["A test passing while the system was offline",
         "A briefing endpoint reported success while the language model was unreachable",
         "The endpoint always returns 200 and substitutes canned text when the model is unavailable, "
         "and the test checked only the status code.",
         "The test now inspects the response for known fallback markers and reports DEGRADED with the "
         "actual cause. Lesson: <i>a test that cannot fail is not a test.</i>"],
        ["Three hundred milliseconds of swallowed exceptions",
         "Behaviour differed between runs with no error reported",
         "A generic exception handler caught deliberate errors and re-labelled them as server faults, "
         "so a missing record reported \u201cinternal server error\u201d with a \u201cnot found\u201d "
         "body.",
         "Deliberate exceptions re-raised before the generic handler. Lesson: <i>catch narrowly.</i>"],
    ], [78, 108, 150, W - 336], caption="Table 13 \u2014 Silent-failure defects. This class caused "
                                        "more lost time than every other class combined."))

    f.append(Sub("Class 3 \u2014 Incorrect error semantics"))
    f.extend(table([
        ["Defect", "Symptom", "Root cause", "Fix and lesson"],
        ["A missing record reported as an upstream failure",
         "Six endpoints returned 502 for a non-existent identifier",
         "The exception types for \u201cno such account\u201d and \u201cthe provider rejected us\u201d "
         "were the same, and both mapped to the gateway-error code.",
         "A distinct exception type for the missing-account case, mapped to 404. Lesson: <i>an error "
         "code is a claim about where the fault lies</i> \u2014 saying \u201cupstream\u201d when the "
         "request was wrong sends the reader in the wrong direction."],
        ["Status code depended on unrelated global state",
         "The same request returned 400 in one environment and 404 in another",
         "Routes called the provider before checking whether the account existed, so the response "
         "depended on whether the provider was configured.",
         "Every account-scoped route resolves the account locally before calling out. Lesson: <i>a "
         "response should be a function of the request, not of ambient configuration.</i>"],
    ], [78, 108, 150, W - 336], caption="Table 14 \u2014 Error-semantics defects."))

    f.append(Sub("Class 4 \u2014 Wrong model of the domain"))
    f.extend(table([
        ["Defect", "Symptom", "Root cause", "Fix and lesson"],
        ["Temporal supersession silently did nothing",
         "\u201cWhat am I working on?\u201d returned both the old and the new answer",
         "Two facts describing the same state were stored under different predicate names "
         "(\u201clearning\u201d and \u201cfocus\u201d), so neither superseded the other. The temporal "
         "model was correct; the normalisation was not.",
         "Predicates canonicalised into state classes before supersession. Lesson: <i>a data model is "
         "only as correct as its normalisation.</i> This defect reproduced exactly the failure the "
         "component was built to prevent."],
        ["Negation detected by substring",
         "Notes about notes were reported as logical contradictions",
         "Negation was tested with a substring check, so the word \u201cnot\u201d matched inside "
         "\u201cnotes\u201d, \u201cnotification\u201d and \u201canother\u201d.",
         "Word-boundary matching with an explicit pattern list. Lesson: <i>substring matching on "
         "natural language is almost always wrong</i> \u2014 it is the classic error in this domain."],
        ["The most common contradiction was undetectable",
         "\u201cDeadline moved from October to September\u201d was missed entirely",
         "Both the temporal extractor and the negation detector keyed on first-person state claims or "
         "negation words. A third-person factual value change matches neither.",
         "Added dated and numeric value-change detection, requiring shared topic signature and high "
         "salient-word overlap. Lesson: <i>test the common case, not the designed case.</i>"],
        ["Topic words stripped as noise",
         "The strongest real contradiction stopped being detected after a \u201cprecision\u201d "
         "tightening",
         "The stop-word list excluded \u201cdeadline\u201d and \u201cproject\u201d as filler "
         "\u2014 precisely the words that make two memories comparable.",
         "Generic filler only. Lesson: <i>a stop-word list is a model of the domain and can be wrong "
         "in ways that silently destroy the signal.</i>"],
        ["Importance ranking made results worse",
         "The proposed method scored below a baseline",
         "Re-ranking multiplied the damped retrieval score by an abstract importance score, promoting "
         "low-relevance, high-importance memories above the correct answer.",
         "Rank-preserving re-ranking with importance as a light tie-breaker. Lesson: <i>a re-ranker "
         "should refine an ordering, not replace it.</i>"],
    ], [78, 108, 150, W - 336], caption="Table 15 \u2014 Domain-model defects. This class is the most "
                                        "interesting: every one was invisible until measured."))

    f.append(Sub("Class 5 \u2014 Lifecycle and cleanup"))
    f.extend(table([
        ["Defect", "Symptom", "Root cause", "Fix and lesson"],
        ["Cleanup deleted the last reference",
         "Broken images in the live view",
         "The pruning process deleted raw frames that a preview still referenced.",
         "A dedicated buffer excluded from pruning. Lesson: <i>never let cleanup delete the last "
         "reference to something a view depends on.</i>"],
        ["Orphaned derived rows",
         "A test crashed on a record whose parent no longer existed",
         "Deleting a memory left its score row behind, which then inflated counts while never "
         "appearing in the joined listing.",
         "Orphan pruning added; the test now joins. Lesson: <i>derived data needs a lifecycle, not "
         "just a creation path.</i>"],
        ["The microphone never re-armed",
         "The assistant answered one question and then stopped",
         "The browser's speech recogniser ends its session by itself, and no handler restarted it. The "
         "summon gesture only spoke a greeting and never restarted recognition.",
         "Re-arm in the session-end handler, with backoff. Lesson: <i>an event-driven resource that "
         "ends itself needs an explicit restart path.</i>"],
        ["Two further ways the orb could die",
         "Not yet observed, found by writing the test",
         "If the model never answers, the turn stays open forever; and the text-to-speech completion "
         "event is not guaranteed in Electron.",
         "Two watchdogs. Lesson: <i>write the test for the failure you have not seen yet.</i> It "
         "found both before the user did."],
        ["A wake event could hide the assistant",
         "Not yet observed; found by reading the code",
         "The wake handler called a function that toggles window visibility rather than one that "
         "shows it, so waking an already-visible orb would hide it.",
         "A non-toggling reveal path added. Lesson: <i>\u201cshow\u201d and \u201ctoggle\u201d are "
         "different operations and conflating them produces inverted behaviour.</i>"],
    ], [78, 108, 150, W - 336], caption="Table 16 \u2014 Lifecycle and cleanup defects."))

    f.append(Sub("Class 6 \u2014 Process and data safety"))
    f.extend(table([
        ["Defect", "Symptom", "Root cause", "Fix and lesson"],
        ["Benchmark not reproducible",
         "Results changed between consecutive runs",
         "Derived research state from a previous run \u2014 temporal facts, conflicts, "
         "consolidations, tombstones \u2014 perturbed the following run.",
         "Derived state cleared at the start of each run; determinism now asserted by the suite. "
         "Lesson: <i>a benchmark that is not deterministic cannot support a claim made from it.</i>"],
        ["Test deleted real user data",
         "123 of the author's genuine memory cards were removed",
         "The mail-ingestion test registered the author's real email address, so its generated "
         "artefacts were indistinguishable from genuine ones and its cleanup could not tell them "
         "apart.",
         "Restored from version control. The test now uses a non-existent address and its cleanup "
         "<b>refuses to delete any artefact that does not carry the test marker</b>, reporting what "
         "it protected instead. Lesson: <i>a destructive operation must be able to prove that what "
         "it is deleting is its own.</i> This is the most serious defect in the project and the only "
         "one caused by the assistant rather than the application."],
        ["Verification tool crashed on the target machine",
         "The render smoke test failed on the user's machine but passed in development",
         "A browser global that had been assignable in the older runtime is a read-only accessor in "
         "the newer one installed on the user's machine.",
         "Globals installed via a descriptor-based helper; verified on both runtime versions. Lesson: "
         "<i>a check that fails on the target machine in the same way as the product is worse than no "
         "check.</i>"],
        ["Contract checker produced false positives",
         "Three correct endpoints were reported as missing",
         "The URL extractor and normaliser handled template expressions and query strings in the "
         "wrong order, truncating a URL at a question mark inside a ternary.",
         "Order corrected; ternary branches now expanded into separate candidates and each checked. "
         "Lesson: <i>a checker that cries wolf gets ignored</i>, which is why the mislabel of a "
         "timeout as a crash was treated as a bug in its own right."],
    ], [78, 108, 150, W - 336], caption="Table 17 \u2014 Process and data-safety defects."))

    f.extend(callout(
        "The pattern across all 27 defects",
        "Five causes account for almost everything. Silent failure, because a system that fails "
        "quietly is misread as working. Wrong error semantics, because an error code is a claim about "
        "where the fault lies. Wrong domain model, because the code is correct and the model is not. "
        "Lifecycle gaps, because creation paths are written and destruction paths are not. And process "
        "failure, because the check itself was untested. Notably, the entire first class \u2014 "
        "dependency problems \u2014 was eliminated once the verification system existed, and the "
        "domain-model class was found only by measurement."))
    f.append(PageBreak())

    # ================================================================ PART VII
    f.append(Section("Part VII \u2014 Verification"))
    f.append(Spacer(1, 4))
    f.append(P(
        "The project maintains fifteen automated verification gates. The design principle is that "
        "<i>each gate must be capable of failing.</i> A check that cannot fail is decoration, and "
        "several of the defects in Part VI were found precisely because a gate that had been passing "
        "was examined and discovered to be untestable."))

    f.extend(table([
        ["#", "Gate", "What it catches"],
        ["1", "Static analysis", "Undefined identifiers, unused symbols, hook violations \u2014 the "
                                 "crash class. Fails on any warning."],
        ["2", "Environment and integration health", "Eight static checks: imports resolve, icons "
                                                    "exist, client methods defined, API URLs match "
                                                    "real routes, preload surface complete, Python "
                                                    "compiles."],
        ["3", "Frontend\u2013backend API contract", "Every URL the interface calls is matched against "
                                                    "every route the backend serves, including both "
                                                    "branches of ternary expressions."],
        ["4", "Route render and mount", "All nineteen routes are rendered AND mounted so effects run, "
                                        "with a third phase exercising the connected states."],
        ["5", "Production build", "The bundle compiles."],
        ["6", "Backend functional suites", "Eleven live suites over authentication, capture, graph, "
                                           "vault, wiki, briefing, deliverables, semantic, OCR, voice."],
        ["7", "Google integration", "Fifty checks against a fake Google server: consent URL shape, "
                                    "read-only scopes, token exchange, refresh, revoked-token "
                                    "handling, and that the refresh token is not readable on disk."],
        ["8", "Mail and calendar", "Fifty-six checks against a fake IMAP server and a real HTTP "
                                   "iCalendar fetch, including the iCal feature matrix."],
        ["9", "Mail ingestion", "Forty-seven checks: the full path from IMAP through to retrieval, "
                                "asserting the pipeline can actually answer from ingested mail."],
        ["10", "Orb voice loop", "Twenty-two checks driving a fake speech engine, asserting the "
                                 "microphone re-arms and that watchdogs fire."],
        ["11", "Wake word and proactive voice", "Fifty-five checks on policy gates and, when the "
                                                "library is present, the real model against real "
                                                "audio."],
        ["12", "Hands-free interface wiring", "Ten checks that wake and speak events actually reach "
                                              "the interface."],
        ["13", "Research layer", "Sixty-eight checks, one per claim in the paper."],
        ["14", "Live endpoint sweep", "Boots the server and calls every registered route, reporting "
                                      "status, timing and whether any returned a server error."],
        ["15", "Browser route smoke (optional)", "Loads all routes in a real browser and screenshots "
                                                 "each."],
    ], [22, 152, W - 174],
        caption="Table 18 \u2014 The fifteen verification gates, run by a single command."))

    f.append(Sub("Three principles extracted from building this"))
    f.append(P(
        "<b>Test the claim, not the code.</b> The research suite contains one check per claim in the "
        "paper. If a claim cannot be tested, it should not be in the paper. Several of the "
        "domain-model defects in Part VI were found by this discipline, because writing the assertion "
        "forced the question \u201cwhat would this look like if it were broken?\u201d"))
    f.append(P(
        "<b>Prefer the failing case to the passing one.</b> The most valuable tests written were the "
        "negative controls: silence must not trigger the wake word; unrelated memories must not be "
        "reported as duplicates; a forgotten memory must not appear in <i>any</i> retrieval mode. A "
        "suite composed only of positive cases will pass on a system that does nothing."))
    f.append(P(
        "<b>Prove the check can fail.</b> During stabilisation, the crash-class bug was deliberately "
        "re-introduced and the gate was confirmed to refuse it. This is the only way to know that a "
        "green result means something. It is also how three false-positive defects in the checkers "
        "themselves were found \u2014 each generated by testing the test."))
    f.append(PageBreak())

    # =============================================================== PART VIII
    f.append(Section("Part VIII \u2014 The Research Contribution"))
    f.append(Spacer(1, 4))
    f.append(P(
        "The paper's central research question is: <i>how can a personal AI continuously update, "
        "consolidate, prioritise and temporally reason over a user's evolving knowledge without "
        "accumulating redundant, outdated or contradictory memories?</i>"))

    f.append(Sub("The seven components"))
    f.extend(table([
        ["#", "Component", "Function", "Key design decision"],
        ["C1", "Adaptive Memory Scoring",
         "Eight-term importance score with every term persisted",
         "Auditable rather than opaque: a score can be explained term by term"],
        ["C2", "Temporal Personal Knowledge Graph",
         "Triples with validity intervals and state supersession",
         "Close facts rather than delete them, so history stays queryable"],
        ["C3", "Contradiction-Aware Retrieval",
         "Three conflict classes detected; rank damping applied",
         "Damp rather than remove, preserving both current and historical answers"],
        ["C4", "Memory Consolidation",
         "Near-duplicate clustering with provenance retention",
         "Threshold calibrated from the measured distribution, not assumed"],
        ["C5", "Knowledge-Gap Detection",
         "Exposure versus depth, weighted by graph connectivity",
         "Connectivity factor prevents flagging well-understood concepts"],
        ["C6", "Retrieval-Enforced Forgetting",
         "Exclusion at five independent surfaces",
         "Enforcement at retrieval, not deletion, because derived stores survive deletion"],
        ["C7", "PersonalBrain-Bench",
         "Synthetic corpus with six question categories",
         "Synthetic by design, so the experiment is reproducible and contains no private data"],
    ], [24, 108, 148, W - 280],
        caption="Table 19 \u2014 The seven contributions and the decision that defines each."))

    f.append(Sub("Measured results"))
    f.extend(table([
        ["Pipeline", "Hit@5", "MRR", "Stale@1", "Leak", "Duplicate", "Latency"],
        ["Vanilla dense", "1.000", "0.833", "0.364", "0.022", "0.022", "33 ms"],
        ["Hybrid", "1.000", "0.944", "0.091", "0.022", "0.022", "29 ms"],
        ["Graph-augmented", "1.000", "0.944", "0.091", "0.022", "0.022", "37 ms"],
        ["Adaptive (proposed)", "1.000", "1.000", "0.000", "0.000", "0.000", "80 ms"],
    ], [116, 52, 50, 56, 48, 66, W - 388],
        caption="Table 20 \u2014 Comparative results on PersonalBrain-Bench (k = 5, 11 questions, 15 "
                "memories). Two consecutive runs are byte-identical."))
    f.extend(table([
        ["Question category", "Vanilla MRR", "Hybrid MRR", "Adaptive MRR", "Change"],
        ["Factual", "1.000", "1.000", "1.000", "\u2014"],
        ["Temporal", "0.750", "0.750", "1.000", "+0.250"],
        ["Contradiction", "0.500", "1.000", "1.000", "+0.000"],
        ["Multi-hop", "1.000", "1.000", "1.000", "\u2014"],
        ["Duplicate", "1.000", "1.000", "1.000", "\u2014"],
    ], [116, 84, 78, 88, W - 366],
        caption="Table 21 \u2014 MRR by category. Improvements appear exactly where the architecture "
                "predicts them and nowhere else."))

    f.append(Sub("What the results actually mean"))
    f.append(P(
        "<b>The headline finding is negative, and that is the contribution.</b> Hit@5 is 1.000 for "
        "every pipeline including the simplest baseline. Every system retrieves the relevant memory "
        "somewhere in its top five. Had the evaluation used only recall, the conclusion would have "
        "been that seven research components accomplished nothing measurable, and that conclusion "
        "would have been wrong."))
    f.append(P(
        "What differs is the <i>ordering</i> and the <i>staleness of what comes first</i>. The "
        "proposed pipeline raises mean reciprocal rank from 0.833 to 1.000 and reduces the rate of "
        "leading with superseded content from 36.4% to 0.0%. Because a language model consumes the "
        "ordered context and leads with what it reads first, staleness at rank one is what produces "
        "an answer that is confidently wrong \u2014 and, critically, every retrieved passage remains "
        "faithful to its source, so no faithfulness metric would flag it."))
    f.append(P(
        "The category breakdown localises the gains. Factual, multi-hop and duplicate questions are "
        "unchanged at 1.000, which is a desirable property: it means the added machinery is not a "
        "general-purpose change to retrieval but a targeted one. Temporal questions improve from "
        "0.750 to 1.000 once predicate canonicalisation makes supersession fire. Contradiction "
        "questions are where the vanilla baseline is weakest (0.500), consistent with the motivating "
        "scenario."))
    f.append(P(
        "The forgetting result is the sharpest. The baselines do not merely score lower; they "
        "<i>continue to return content the user explicitly asked to remove</i>. The adaptive pipeline "
        "returns it zero times. This is evidence that removal from a retrieval system is a property "
        "of the retrieval layer and is not obtained by deleting a row from the primary table."))

    f.append(Sub("Limitations, stated plainly"))
    f.extend(B([
        "<b>The benchmark is synthetic and small.</b> Fifteen memories and eleven questions across six "
        "categories. The categories isolate specific behaviours; they do not represent the "
        "distribution of real personal data. Absolute values should not be extrapolated.",
        "<b>Extraction is rule-based and conservative.</b> It will miss phrased contradictions that do "
        "not match its patterns. This trades recall for precision deliberately \u2014 a wrong fact in "
        "a personal graph is worse than a missing one \u2014 but the trade is real.",
        "<b>Temporal handling uses UTC-normalised timestamps</b> without full timezone or "
        "partial-interval reasoning, which would matter for events spanning midnight across zones.",
        "<b>The evaluation covers retrieval, not generation.</b> Whether higher MRR and lower stale@1 "
        "translate into fewer incorrect answers in generated prose is not measured here. This is the "
        "natural next experiment and the most significant gap.",
        "<b>The ablation is not yet factorised.</b> The per-category results localise the effect, but "
        "an independent run isolating each of the five post-retrieval stages has not been performed. "
        "The paper states this rather than inferring it.",
    ]))

    f.extend(callout(
        "The most defensible sentence in the paper",
        "\u201cEvery baseline continues to return explicitly unlearned content.\u201d This is a "
        "negative result about the baselines, it is measured, it is reproducible, and it is not "
        "obvious in advance. A contribution does not have to be a large positive number; a precise "
        "demonstration that an apparently simple property is not automatic is equally publishable, "
        "provided it is honest about scope."))
    f.append(PageBreak())

    # ================================================================== PART IX
    f.append(Section("Part IX \u2014 Current State and Future Work"))
    f.append(Spacer(1, 4))

    f.append(Sub("What works today"))
    f.extend(table([
        ["Capability", "Status", "Evidence"],
        ["Automatic screen capture with OCR", "Working", "Continuous capture with information-density "
                                                         "scoring and hero-frame election"],
        ["Memory vault with GitHub sync", "Working", "123 knowledge cards, auto-committed every 60 "
                                                      "seconds"],
        ["Self-improving wiki", "Working", "93 articles across six domains, recompiled as evidence "
                                           "arrives"],
        ["Knowledge graph", "Working", "350 nodes, 500 edges, interactive visualisation"],
        ["Question answering over memory", "Working", "Local model over 49-table store; verified by "
                                                       "the RAG retrieval assertion"],
        ["Mail ingestion", "Working", "Read-only IMAP; 47 automated checks; deadlines become tasks and "
                                      "spoken alerts"],
        ["Calendar ingestion", "Working", "iCalendar feeds with recurrence expansion and timezone "
                                          "normalisation"],
        ["Voice in and out", "Working", "Recogniser re-arms correctly; watchdogs prevent the "
                                        "previously reported stall"],
        ["Wake word", "Working when installed", "Measured 0.9968 against 0.000 for silence"],
        ["Proactive speech", "Working", "Priority-gated with quiet hours, cooldown and dedupe"],
        ["Research layer", "Working", "68 checks; four retrieval pipelines with measured comparison"],
        ["Desktop packaging", "Partial", "Runs from source; an installer configuration exists but has "
                                         "not been produced"],
    ], [128, 82, W - 210], caption="Table 22 \u2014 Current capabilities with the evidence for each."))

    f.append(Sub("What does not work, or is not attempted"))
    f.extend(B([
        "<b>Writing to the user's accounts.</b> Every integration is read-only by design. The system "
        "can draft a reply but cannot send it, and can report a deadline but cannot create the "
        "calendar event. This is a deliberate safety choice rather than a limitation of capability, "
        "and reversing it would require an approval layer that has not been built.",
        "<b>Generative answer quality measurement.</b> Retrieval is measured; generation is not. "
        "Whether the improved ordering produces measurably better prose has not been tested.",
        "<b>Long-running autonomy.</b> Agents run on schedules and timers within the running "
        "application. There is no daemon, so nothing happens when the application is closed.",
        "<b>Multi-user support.</b> The schema has a user table and the authentication is real, but "
        "the deployment model is single-user and the vault is a single Git repository.",
        "<b>Installer.</b> A configuration exists but a distributable installer has not been built.",
    ]))

    f.append(Sub("Immediate next steps"))
    f.extend(table([
        ["Priority", "Work item", "Rationale"],
        ["1", "Factorised ablation", "The one gap the paper admits. Each of the five post-retrieval "
                                     "stages isolated, so the contribution of each is measured "
                                     "rather than inferred."],
        ["2", "Generation-quality study", "Establish that the retrieval gains survive into the answer. "
                                          "A blind comparison across the four pipelines on the same "
                                          "question set."],
        ["3", "Grow PersonalBrain-Bench", "More memories, more categories, adversarial cases designed "
                                          "to break the conflict detector. Synthetic construction "
                                          "keeps it reproducible."],
        ["4", "Grounded answering with provenance", "The retrieval trace already records which "
                                                    "memories were used; surfacing citations in the "
                                                    "answer makes the reasoning auditable to the "
                                                    "user."],
        ["5", "Approval-gated write actions", "Draft the reply, propose the calendar event, and "
                                              "require confirmation. Turns the system from an "
                                              "advisor into an assistant without giving up the "
                                              "safety property."],
    ], [48, 140, W - 188], caption="Table 23 \u2014 Prioritised next steps."))

    f.append(Sub("Closing assessment"))
    f.append(P(
        "The system does what the original brief asked. It captures continuously, stores durably, "
        "answers in plain language, speaks and listens, and runs entirely on the author's machine "
        "without a paid service. It also does something the original brief did not anticipate: it "
        "identifies and addresses a class of failure specific to personal memory that general-purpose "
        "retrieval evaluation does not measure."))
    f.append(P(
        "The honest summary of the research contribution is that it is a careful negative result "
        "surrounded by a positive one. The negative result is that recall is the wrong instrument for "
        "personal memory \u2014 it saturates and conceals. The positive result is that three custom "
        "metrics \u2014 staleness at rank one, leakage after forgetting, and within-query duplication "
        "\u2014 do discriminate, and that a five-stage post-retrieval layer improves all three to "
        "zero while leaving ordinary recall untouched. That is a modest but real and defensible "
        "finding."))
    f.append(P(
        "The project's most transferable output may be neither the application nor the paper but the "
        "verification discipline described in Part VII. Of the twenty-seven defects recorded in "
        "Part VI, twenty-five were found by an automated check rather than by a person noticing "
        "something wrong. The two that a person found \u2014 a missing import and a stalled "
        "microphone \u2014 were both immediately converted into automated checks. The pattern that "
        "emerges is that <i>the value of testing is not in catching bugs that exist; it is in forcing "
        "the specification of what correct behaviour would even look like.</i>"))
    f.append(PageBreak())

    # ================================================================ APPENDIX
    f.append(Section("Appendix A \u2014 Project Statistics"))
    f.extend(table([
        ["Metric", "Value"],
        ["Total commits", "231"],
        ["Substantive commits", "69"],
        ["Automated vault synchronisations", "162"],
        ["Python source files", "165"],
        ["Python lines of code", "17,149"],
        ["JavaScript/JSX files (application)", "55"],
        ["JavaScript/JSX lines of code", "12,449"],
        ["Backend route modules", "21"],
        ["Specialised agents", "10"],
        ["Database tables", "49"],
        ["Interface routes", "19"],
        ["Automated verification gates", "15"],
        ["Test suites", "8"],
        ["Research assertions", "68"],
        ["Documented defects", "27"],
        ["Documented deviations", "13"],
    ], [220, W - 220], caption="Table 24 \u2014 Project metrics at the time of writing."))

    f.append(Section("Appendix B \u2014 Build Phases at a Glance"))
    f.extend(code("""  PHASE 0  Aug 2026        Foundations: FastAPI, SQLite, auth, capture skeleton
  PHASE 1  17 Sep          Curation, hero images, vault, wiki compiler, 3D brain
  PHASE 2  18 Sep          Free native scrapers, insight collisions, spoken briefing
  PHASE 3  21 Sep          Interface rebuilds: obsidian -> stark -> 15-tab OS + orb
  PHASE 4  22 Sep (am)     Two full error audits, verification system created
  PHASE 5  22 Sep          Google OAuth, then IMAP + iCal, mail ingestion pipeline
  PHASE 6  22 Sep          Wake word, proactive voice, orb voice-loop repair
  PHASE 7  22 Sep          Research layer: 7 contributions, benchmark, IEEE paper

  Gates added : 0 -> 15          Defects found and fixed : 27
  Deviations  : 13               Assertions : 8 suites, ~400 individual checks""",
                  "The build chronology in one view. Note that phases 4 through 7 all occurred on the "
                  "same day; the pace reflects the leverage gained once the verification system "
                  "existed."))

    f.append(Section("Appendix C \u2014 Glossary"))
    glossary = [
        ["Term", "Definition"],
        ["Agent", "A component with a single responsibility, its own failure mode, and no knowledge of "
                  "the others."],
        ["App password", "A long random credential issued by a provider for legacy protocols, usable "
                         "after two-factor authentication is enabled. No consent screen, no expiry."],
        ["CASA", "Cloud Application Security Assessment. A third-party security audit required by "
                 "Google for applications publishing restricted scopes."],
        ["Chunk", "A passage of text small enough to embed meaningfully and store as one unit."],
        ["Consolidation", "Merging near-duplicate memories into one canonical record while retaining "
                          "the identifiers of everything merged."],
        ["Cosine similarity", "The cosine of the angle between two vectors; the standard measure of "
                              "semantic similarity."],
        ["Damping", "Multiplying a retrieved item's ranking weight to demote it without removing it."],
        ["Embedding", "A numeric vector representing text, positioned so that similar meanings are "
                      "nearby."],
        ["Exposure versus depth", "Having encountered a concept versus having understood it. The "
                                  "distinction knowledge-gap detection must make."],
        ["Hero image", "The single representative frame elected from an information period, kept "
                       "instead of every screenshot."],
        ["Hit@k", "Whether a relevant item appeared in the top k results."],
        ["IMAP", "Internet Message Access Protocol. The mechanism desktop mail clients use to read "
                 "mailboxes."],
        ["iCalendar", "A text format for calendar data. Google publishes a private address per "
                      "calendar requiring no authentication."],
        ["Knowledge graph", "Entities as nodes and typed relationships as edges."],
        ["Leak rate", "Fraction of returned results that were explicitly forgotten. Custom metric "
                      "introduced by this work."],
        ["MRR", "Mean reciprocal rank: the mean of 1/rank of the first relevant result. Rank-sensitive."],
        ["OAuth", "A protocol allowing an application limited access to an account without receiving "
                  "the password."],
        ["RAG", "Retrieval-augmented generation. Retrieving relevant passages and passing them to a "
                "language model along with the question."],
        ["Scope", "A named permission bundle in OAuth. Providers tier scopes by sensitivity."],
        ["Stale@1", "Whether the top-ranked result is outdated. Custom metric introduced by this "
                    "work."],
        ["Supersession", "Closing an older fact when a newer one replaces it, rather than deleting it."],
        ["TF-IDF", "A classical term-weighting scheme for keyword retrieval. Needs no neural network, "
                   "which makes it deterministic."],
        ["Unlearning", "Removing the influence of specific data from a system that has already "
                       "incorporated it."],
        ["Validity interval", "The time range during which an assertion was true. A null end means "
                              "still true."],
        ["Vector store", "An index optimised for nearest-neighbour search over embeddings."],
        ["Wake word", "An always-listening keyword spotter that fires when a phrase such as the "
                      "assistant's name is recognised."],
    ]
    f.extend(table([[g[0], g[1]] for g in glossary], [110, W - 110], header=True))

    return f
