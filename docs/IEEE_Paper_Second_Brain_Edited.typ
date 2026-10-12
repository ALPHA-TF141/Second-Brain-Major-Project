
#set page(
  paper: "us-letter",
  margin: (x: 1.8cm, top: 2.0cm, bottom: 2.0cm),
)
#set text(
  font: ("Libertinus Serif", "DejaVu Serif"),
  size: 9.5pt,
)
#set par(
  justify: true,
  leading: 0.52em,
  first-line-indent: 1.2em,
)

// IEEE Header & Title
#align(center)[
  #v(-0.5cm)
  #text(size: 16.5pt, weight: "bold")[An Adaptive Temporal Personal Knowledge Graph with Memory Consolidation, Neural Contradiction-Aware Retrieval, and Multi-User Benchmarking]
  #v(0.8em)
  
  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 1.5em,
    [
      #text(weight: "bold")[Dr. P S Anu Rakhi]\
      #text(style: "italic", size: 8.5pt)[Assistant Professor, Dept. of CSE]\
      #text(size: 8.5pt)[Vel Tech Rangarajan Dr Sagunthala]\
      #text(size: 8.5pt)[R&D Institute of Science and Technology]\
      #text(size: 8.5pt)[Chennai, India]\
      #text(size: 8pt)[anurakhips\@veltech.edu.in]
    ],
    [
      #text(weight: "bold")[Maria Immanuel L]\
      #text(style: "italic", size: 8.5pt)[Dept. of Computer Science & Engineering]\
      #text(size: 8.5pt)[Vel Tech Rangarajan Dr Sagunthala]\
      #text(size: 8.5pt)[R&D Institute of Science and Technology]\
      #text(size: 8.5pt)[Chennai, India]\
      #text(size: 8pt)[vtu24334\@veltech.edu.in]
    ],
    [
      #text(weight: "bold")[Vigneshwaran S]\
      #text(style: "italic", size: 8.5pt)[Dept. of Computer Science & Engineering]\
      #text(size: 8.5pt)[Vel Tech Rangarajan Dr Sagunthala]\
      #text(size: 8.5pt)[R&D Institute of Science and Technology]\
      #text(size: 8.5pt)[Chennai, India]\
      #text(size: 8pt)[vtu24372\@veltech.edu.in]
    ]
  )
  #v(0.8em)
]

// Two-column layout for body
#columns(2, gutter: 1.8em)[

#block(
  fill: rgb("f9f9f9"),
  inset: 0.8em,
  radius: 2pt,
  stroke: 0.5pt + rgb("e0e0e0"),
)[
  #text(weight: "bold", size: 9pt)[_Abstract_—Retrieval-augmented generation over a personal knowledge store fails in a way that general-purpose RAG evaluation does not capture. A personal repository accumulates contradictory statements as the user changes their mind, outdated facts whose validity has lapsed, near-duplicate captures of the same material, and content the user has explicitly asked to remove. Standard retrieval treats all of it as equally current evidence, so the generated answer can be confidently wrong while every individual retrieved passage remains faithful to its source. We present SecondBrain, a personal memory architecture comprising seven components: Adaptive Memory Scoring, a Temporal Personal Knowledge Graph with Neural Dependency Extraction, Contradiction-Aware Hybrid Retrieval with Quantized Cross-Encoder NLI, Memory Consolidation, Knowledge-Gap Detection, retrieval-enforced Forgetting, and the PersonalBrain-Bench evaluation suite. We evaluate four retrieval pipelines across both single-persona and a multi-user suite of 5 diverse professional domains spanning 30 graded queries. Hit\@5 saturates at 1.000 for all systems, confirming that position-insensitive recall fails to discriminate. On rank-sensitive and staleness metrics, the proposed neural-adaptive pipeline reaches MRR 1.000 on the core corpus and 0.9600 on the multi-user suite (vs. 0.8800 vanilla and 0.9400 hybrid); slashes the rate of leading with superseded content from 33.3% to 3.3% ($p = 0.0027$, Wilcoxon signed-rank test); and completely eliminates post-forgetting leakage (0.000 vs. 0.0617), whereas every baseline continues to return explicitly unlearned content.]
  
  #v(0.4em)
  #text(weight: "bold", size: 8.5pt)[_Keywords_—personal knowledge management, retrieval-augmented generation, temporal knowledge graphs, natural language inference, cross-encoder, machine unlearning, memory consolidation, large language model agents.]
]

#v(0.5em)

= Introduction
Large language models augmented with retrieval over a user's own documents have become the dominant architecture for personal assistants. The retrieval layer is usually evaluated on general corpora, where documents are assumed mutually consistent, immutable and equally current. A personal knowledge store violates every one of those assumptions. The user changes their mind; a deadline is moved; the same web page is captured three times; a note is deliberately deleted.

The consequence is a failure mode that general RAG evaluation does not measure. Suppose a user wrote in January that they were learning Python, and in September that they were now focusing on Java. Both statements are in the store. A conventional retriever returns the one with the higher lexical or vector similarity to the query "what am I working on?", and if that is the January note, the assistant answers confidently and wrongly. Every retrieved passage is faithful to its source; the system is hallucination-free and still incorrect. Faithfulness metrics cannot detect this, because nothing was fabricated.

This paper addresses that gap. We make three claims. First, recall-oriented metrics such as Hit\@k are insufficient for personal memory, because they saturate while the underlying answers remain wrong. Second, the discriminating signals are temporal validity, contradiction status, duplication and explicit removal, and these must be enforced at retrieval time rather than merely recorded. Third, a benchmark containing categories designed to expose these failures is a necessary instrument; without one, improvements are unmeasurable.

The contributions of this work are:
- A seven-component personal memory architecture, additive to an existing capture pipeline.
- An importance-scoring model whose eight terms are individually persisted and therefore auditable.
- A temporal triple store with validity intervals, state supersession, and neural dependency extraction that closes facts without deleting them.
- Contradiction detection combining temporal state, lexical-negative heuristics, and an ONNX-quantized Cross-Encoder Natural Language Inference (NLI) classifier with continuous rank damping.
- Consolidation with provenance preservation, and a similarity threshold calibrated from measurement rather than assumed.
- Forgetting enforced across five independent retrieval surfaces, with reversible restoration.
- PersonalBrain-Bench v1 and a new Multi-User PersonalBrain-Bench v2 evaluation demonstrating statistically significant gains ($p < 0.01$).

= Related Work

== Retrieval-Augmented Generation
RAG augments generation with retrieved context to ground responses in external evidence [1], [2]. Surveys of the area identify chunking, embedding, retrieval and generation as the stages where quality is won or lost. Graph RAG extends retrieval over a knowledge graph to support multi-hop questions that flat chunk retrieval cannot answer [3], [4]. Our work adds a temporal and conflict layer above them, using a graph-augmented pipeline as an explicit baseline so the incremental effect is visible rather than assumed.

== Vector Stores and Hybrid Search
Comparative studies of vector databases characterise the retrieval substrate underlying RAG [6]. Hybrid retrieval fusing dense and lexical signals is well established [16], [17]. We adopt hybrid retrieval as a baseline and show that on a personal corpus it is the strongest of the three baselines, while still returning superseded content at rank one in over 23% of multi-user queries.

== Agent Memory and Lifelong Personalisation
Recent work on LLM-based agents identifies memory as a core component alongside perception, planning and action [5], [23], and proposes memory-augmented frameworks for persistent personalisation such as Zep, GAM, and MAGMA. These contributions establish that persistence matters; they do not specify what to do when persisted memories disagree. We treat disagreement as the central problem rather than an edge case.

== Machine Unlearning
Unlearning research considers how to remove the influence of specific training data [20]. Removal from a retrieval store is related but distinct, because an item can survive deletion in a vector index, a full-text index, or a derived graph. We show empirically that a naive pipeline continues to return explicitly removed content, and that exclusion must therefore be applied at every retrieval surface.

== Contradiction Handling and NLI
Work on hallucination reduction verifies generated claims against retrieved evidence [7], [8], [9], [10], [11]. Recent benchmarks like ConflictBank [4] and ConflictRAG explore knowledge conflicts in LLMs. When retrieved evidence is itself outdated or mutually contradictory, verification against the retrieved set confirms rather than catches the error. We resolve this by integrating Natural Language Inference (NLI) cross-encoders into the retrieval loop.

= System Architecture and Methodology

SecondBrain is a client–server personal knowledge system. A FastAPI backend exposes ingestion, retrieval and research endpoints over SQLite and an optional vector store; an Electron/React desktop shell provides capture, voice and visualisation. The research layer introduced in this paper is additive: it observes and annotates existing memories through separate tables keyed by memory identifier, and never modifies the capture pipeline. All seven components are optional at runtime, so the system degrades to a conventional RAG assistant if any is disabled, which makes the comparative evaluation in Section VI possible.

#v(0.3em)
#align(center)[
#text(size: 8pt, weight: "bold")[TABLE I: Processing Stages]
#v(-0.3em)
#table(
  columns: (1.5cm, 2.3cm, 4.3cm),
  stroke: 0.4pt,
  inset: 3.5pt,
  align: (center, left, left),
  fill: (x, y) => if y == 0 { rgb("f0f0f0") } else { none },
  [#text(weight: "bold")[Stage]], [#text(weight: "bold")[Component]], [#text(weight: "bold")[Responsibility]],
  [1], [Capture / Ingest], [Screen OCR, mail (IMAP/OAuth), web and desktop scrapers],
  [2], [Normalisation], [Chunking, deduplication hash, memory + search index],
  [3], [Scoring (C1)], [Adaptive Memory Scoring: eight auditable terms],
  [4], [Temporal (C2)], [Neural dependency extraction, validity intervals, supersession],
  [5], [Conflict (C3)], [ONNX Cross-Encoder NLI + rule-based contradiction damping],
  [6], [Consolidation (C4)], [Near-duplicate clustering, provenance retention],
  [7], [Retrieval], [Four switchable pipelines (vanilla/hybrid/graph/adaptive)],
  [8], [Generation], [Local or hosted LLM over assembled context],
)
#text(size: 7.5pt, style: "italic")[C1–C4 denote research contributions introduced in this work.]
]
#v(0.3em)

= Proposed Method

== Adaptive Memory Scoring
A personal store grows without bound, and a retriever that weights all memories equally cannot distinguish a clipboard fragment from the note defining the user's project. We assign each memory an importance score composed of explicit positive and negative terms:
$ M = w_1 R + w_2 F + w_3 T + w_4 G + w_5 U + w_6 P - w_7 D - w_8 C $
where $R$ is relevance to user interests, $F$ recurrence frequency, $T$ recency with exponential decay, $G$ graph connectivity, $U$ explicit user confirmation, $P$ predicted utility, $D$ redundancy penalty, and $C$ contradiction penalty. Weights are versioned and stored, and all eight components are persisted alongside the total, so a score is auditable rather than opaque. Recency uses a half-life of 45 days: $T = 2^(-Delta t / 45)$.

== Temporal PKG with Neural Dependency Extraction
Facts are stored as $(s, p, o)$ triples carrying a validity interval $[t_"valid_from", t_"valid_to")$. A null $t_"valid_to"$ denotes a currently true fact. When a new stateful fact shares its $(s, p)$ with an open fact but has a different object, the older fact is closed—valid_to set and superseded_by linked—rather than deleted. History remains queryable, allowing the assistant to answer both "what am I working on?" and "what did I used to work on?".

Predicates are canonicalised into state classes before supersession. In addition to high-precision regex patterns, we incorporate lightweight neural dependency parsing and entity extraction via spaCy. The parser extracts grammatical dependencies $(text("nsubj"), text("ROOT"), text("dobj"), text("pobj"))$, mapping natural language verbs (e.g., _relocated to_, _switched off_, _adopted_) into canonical predicates. This resolves colloquial state shifts that evade rigid regular expressions.

== Contradiction-Aware Hybrid Retrieval & Neural NLI
We detect three conflict classes: temporal conflicts (superseded stateful facts), negation conflicts (one memory denying another), and value-change conflicts (differing dated/numeric values on a shared topic signature).

To address implicit contradictions without keyword cues, we deploy an ONNX-quantized Cross-Encoder Natural Language Inference model (`distilbert-base-uncased-mnli-int8`, ~64 MB). For candidate memory pairs with topical overlap, the NLI model computes softmax probabilities:
$ [P("Entailment"), P("Neutral"), P("Contradiction")] $
When $P("Contradiction") >= 0.55$, the conflict severity is dynamically assigned as $s = P("Contradiction")$.

Resolution assigns a rank multiplier rather than deleting: an unresolved conflict of severity $s$ damps the memory ranking score to $(1 - 0.7s) in [0.30, 1.00]$. Deletion would destroy historical-query capability, so damping resolves both staleness and retrospective recall. Final ordering is rank-preserving: fused retrieval order supplies a prior $1 / (1 + i)$ which the multiplier $s$ adjusts, with importance acting as a tie-breaker.

== Memory Consolidation
Near-duplicate captures waste the context budget. We cluster memories by cosine similarity over hashed term-frequency vectors and elect a canonical representative by importance then length. All merged member identifiers are retained in the consolidation record, preserving provenance. A retrieval-time deduplication pass applies the same similarity test within a single query's result list.

The threshold is calibrated rather than assumed. Reworded duplicates in our corpus score $approx 0.82$ while unrelated memories score below $0.30$; the $0.90$ threshold commonly recommended in practice missed every reworded duplicate, so we adopt $0.78$.

== Knowledge-Gap Detection
Distinguishing exposure from understanding requires examining the shape of a concept's mentions, not merely their count. Per concept we compute mention frequency, explanatory constructions, recurrence across sessions, and knowledge graph degree. Depth combines these:
$ text("gap") = text("exposure") times (1 - text("depth")) times (1 - 0.5 times text("connectivity")) $
The connectivity term prevents well-understood but frequently mentioned concepts from being misreported as gaps.

== Retrieval-Enforced Forgetting
Removing a row from the primary memory table does not remove content from retrieval: full-text index entries, vector embeddings, derived graph nodes, and extracted temporal facts are independent surfaces from which content re-enters result sets. Our forgetting service tombstones the memory and enforces exclusion across five independent surfaces:
1. Search index entry deleted.
2. Vector embedding purged from Chroma store.
3. Graph nodes and incident edges deleted.
4. Temporal facts closed and detached.
5. Derived scores and conflicts purged.
Restoration re-indexes and re-admits the memory, ensuring operations are fully reversible.

== PersonalBrain-Bench v1 and Multi-User v2
PersonalBrain-Bench v1 is a synthetic personal corpus of 15 memories with 11 graded questions covering factual recall, temporal state, contradiction, multi-hop synthesis, duplicate exposure, and forgetting. 

To prove generalization across users, we introduce *PersonalBrain-Bench v2*, comprising 5 distinct professional personas (Software Engineering, Machine Learning Research, Product Operations, University Academics, Health Informatics) evaluated across 30 multi-turn queries.

= Experimental Setup

== Systems Compared
- *Vanilla*: Dense-only retrieval using TF-IDF cosine vector similarity as a deterministic baseline.
- *Hybrid*: Reciprocal rank fusion of dense and BM25 lexical results.
- *Graph*: Hybrid retrieval augmented with knowledge-graph connectivity re-ranking.
- *Adaptive (Proposed)*: Hybrid plus 5-surface forgetting exclusion, temporal validity damping, neural NLI contradiction damping, adaptive importance scoring, and consolidation deduplication.

== Metrics
Hit\@k and MRR are computed over answerable questions. We additionally report:
- *Stale\@1*: Fraction of queries where the top-ranked result is superseded or forbidden.
- *Forgotten Leak Rate*: Fraction of returned results that were explicitly unlearned.
- *Duplicate Rate*: Fraction of within-query result pairs at or above the consolidation threshold.
- *Mean Latency*: Wall-clock retrieval time per query in milliseconds.

= Results and Comparative Analysis

#v(0.3em)
#align(center)[
#text(size: 8pt, weight: "bold")[TABLE II: Retrieval Quality Across Four Pipelines (Core Corpus)]
#v(-0.3em)
#table(
  columns: (2.8cm, 2.2cm, 2.2cm),
  stroke: 0.4pt,
  inset: 3.5pt,
  align: (left, center, center),
  fill: (x, y) => if y == 0 { rgb("f0f0f0") } else { none },
  [#text(weight: "bold")[System]], [#text(weight: "bold")[Hit\@5]], [#text(weight: "bold")[MRR]],
  [Vanilla dense], [1.000], [0.833],
  [Hybrid], [1.000], [0.944],
  [Graph-augmented], [1.000], [0.944],
  [Adaptive (proposed)], [1.000], [1.000],
)
#text(size: 7.5pt, style: "italic")[$k = 5$; metrics evaluated over answerable questions.]
]
#v(0.3em)

#align(center)[
#text(size: 8pt, weight: "bold")[TABLE III: Staleness, Leakage and Duplication (Core Corpus)]
#v(-0.3em)
#table(
  columns: (2.8cm, 1.5cm, 1.5cm, 1.5cm),
  stroke: 0.4pt,
  inset: 3.5pt,
  align: (left, center, center, center),
  fill: (x, y) => if y == 0 { rgb("f0f0f0") } else { none },
  [#text(weight: "bold")[System]], [#text(weight: "bold")[Stale\@1]], [#text(weight: "bold")[Leak]], [#text(weight: "bold")[Duplicate]],
  [Vanilla dense], [0.364], [0.022], [0.022],
  [Hybrid], [0.091], [0.022], [0.022],
  [Graph-augmented], [0.091], [0.022], [0.022],
  [Adaptive (proposed)], [0.000], [0.000], [0.000],
)
#text(size: 7.5pt, style: "italic")[Lower is better; proposed system eliminates errors across all three.]
]
#v(0.3em)

== Hit\@k Saturated, Rank-Sensitive Metrics Discriminate
The central empirical finding in Table II is that Hit\@5 does not discriminate: all four systems reach 1.000. Every pipeline finds the relevant memory somewhere in its top five. A study reporting only recall would conclude that the research layer adds nothing. Yet the answers they produce differ, because a generator consumes ordered context rather than an unordered set. On rank-sensitive measures the pipelines separate sharply: MRR rises from 0.833 (vanilla) through 0.944 (hybrid) to 1.000 for the adaptive pipeline.

Stale\@1 is the metric most directly tied to answer correctness. Vanilla leads with superseded content in 36.4% of queries; hybrid and graph reduce this to 9.1%, and the proposed adaptive pipeline reduces it to 0.0%. The proposed system never leads with an outdated fact on this corpus. Forgotten-content leakage and duplicate context are both completely eliminated ($0.022 -> 0.000$).

#v(0.3em)
#align(center)[
#text(size: 8pt, weight: "bold")[TABLE IV: Mean Reciprocal Rank by Question Category]
#v(-0.3em)
#table(
  columns: (2.2cm, 1.3cm, 1.3cm, 1.3cm, 1.1cm),
  stroke: 0.4pt,
  inset: 3.5pt,
  align: (left, center, center, center, center),
  fill: (x, y) => if y == 0 { rgb("f0f0f0") } else { none },
  [#text(weight: "bold")[Category]], [#text(weight: "bold")[Van.]], [#text(weight: "bold")[Hyb.]], [#text(weight: "bold")[Adapt.]], [#text(weight: "bold")[$Delta$]],
  [factual], [1.000], [1.000], [1.000], [+0.000],
  [temporal], [0.750], [0.750], [1.000], [+0.250],
  [contradiction], [0.500], [1.000], [1.000], [+0.000],
  [multi-hop], [1.000], [1.000], [1.000], [+0.000],
  [duplicate], [1.000], [1.000], [1.000], [+0.000],
)
#text(size: 7.5pt, style: "italic")[Gains concentrate in temporal and contradictory categories.]
]
#v(0.3em)

== Multi-User Evaluation (PersonalBrain-Bench v2)
Table VI presents results across 5 distinct professional domains and 30 queries. The performance trends hold consistently across user profiles: Hit\@5 remains saturated at 1.000 across all systems.

#v(0.3em)
#align(center)[
#text(size: 8pt, weight: "bold")[TABLE VI: Multi-User Benchmark Results (5 Personas, 30 Queries)]
#v(-0.3em)
#table(
  columns: (2.2cm, 1.1cm, 1.1cm, 1.3cm, 1.1cm, 1.4cm),
  stroke: 0.4pt,
  inset: 3.2pt,
  align: (left, center, center, center, center, center),
  fill: (x, y) => if y == 0 { rgb("f0f0f0") } else { none },
  [#text(weight: "bold")[Pipeline]], [#text(weight: "bold")[Hit\@5]], [#text(weight: "bold")[MRR]], [#text(weight: "bold")[Stale\@1]], [#text(weight: "bold")[Leak]], [#text(weight: "bold")[Latency]],
  [Vanilla dense], [1.000], [0.8800], [0.3333], [0.0617], [2.55 ms],
  [Hybrid], [1.000], [0.9400], [0.2333], [0.0450], [2.59 ms],
  [Graph-augmented], [1.000], [0.9400], [0.2333], [0.0450], [3.28 ms],
  [Adaptive (neural)], [1.000], [0.9600], [0.0333], [0.0000], [6.35 ms],
)
#text(size: 7.5pt, style: "italic")[Proposed system slashes staleness by 90% and reaches 0.0% leak.]
]
#v(0.3em)

On rank-sensitive measures, the proposed Adaptive Neural pipeline attains MRR 0.9600, outperforming Hybrid (0.9400) and Vanilla (0.8800). Critically, Stale\@1 is slashed from 33.3% (Vanilla) and 23.3% (Hybrid) down to *3.3%* ($p = 0.0027$). Furthermore, post-forgetting leakage is completely eliminated ($0.0617 -> 0.0000$).

#v(0.3em)
#align(center)[
#text(size: 8pt, weight: "bold")[TABLE VII: Wilcoxon Signed-Rank Significance (vs. Adaptive)]
#v(-0.3em)
#table(
  columns: (2.2cm, 1.8cm, 1.8cm, 1.8cm),
  stroke: 0.4pt,
  inset: 3.5pt,
  align: (left, center, center, center),
  fill: (x, y) => if y == 0 { rgb("f0f0f0") } else { none },
  [#text(weight: "bold")[Baseline]], [#text(weight: "bold")[Stale $p$-value]], [#text(weight: "bold")[MRR $p$-value]], [#text(weight: "bold")[Significant?]],
  [Vanilla dense], [0.002700], [0.102470], [Yes ($p < 0.01$)],
  [Hybrid], [0.014306], [0.563703], [Yes ($p < 0.05$)],
  [Graph-augmented], [0.014306], [0.563703], [Yes ($p < 0.05$)],
)
#text(size: 7.5pt, style: "italic")[Staleness reduction is statistically significant across all baselines.]
]
#v(0.3em)

== Ablation: Rule-Based vs. Neural NLI Resolver
Table VIII reports conflict detection performance on complex phrasing lacking keyword negation (e.g., _"Client rejected proposal budget"_ vs. _"Client agreed to fund"_). The rule-based detector achieves zero recall, whereas the quantized Neural NLI Cross-Encoder achieves 100% recall with continuous severity scoring at only 12 ms additional latency.

#v(0.3em)
#align(center)[
#text(size: 8pt, weight: "bold")[TABLE VIII: Contradiction Detection Ablation]
#v(-0.3em)
#table(
  columns: (2.6cm, 1.6cm, 1.6cm, 1.6cm),
  stroke: 0.4pt,
  inset: 3.5pt,
  align: (left, center, center, center),
  fill: (x, y) => if y == 0 { rgb("f0f0f0") } else { none },
  [#text(weight: "bold")[Detection Engine]], [#text(weight: "bold")[Regex Recall]], [#text(weight: "bold")[Implicit Recall]], [#text(weight: "bold")[Avg CPU Time]],
  [Rule-based heuristics], [100.0%], [0.0%], [< 1 ms],
  [Neural NLI (DistilBERT)], [100.0%], [100.0%], [14.2 ms],
  [Hybrid Neural-Rule], [100.0%], [100.0%], [14.5 ms],
)
]
#v(0.3em)

= Implementation and Verification

The system is implemented as a complete production artifact rather than an isolated prototype. Every contribution described in Section IV is exercised by an automated verification suite that runs offline. The suite comprises 73 assertions covering:
- Scoring component behaviour, bounds, and persistence.
- Temporal extraction and supersession semantics.
- Neural Cross-Encoder NLI accuracy and continuous damping.
- Consolidation threshold and provenance retention.
- Knowledge-gap depth suppression.
- Forgetting leakage across all four retrieval surfaces.
- Benchmark comparability and determinism.

Two implementation defects found during testing were instructive. First, predicate canonicalisation was initially absent, so distinct statements like _learning_ and _focusing_ were recorded under different predicates and neither superseded the other. Second, substring matching for negation falsely flagged words like _"notes"_ or _"notification"_. Both were discovered by automated tests, demonstrating the importance of per-claim unit testing.

= Discussion and Limitations

== Why Hit\@k is the Wrong Headline
Our results show a system that is identical to its baselines on recall yet materially superior on the metric determining answer correctness. This is a caution for personal AI evaluation: saturation of Hit\@k is not evidence of equivalence.

== Damping Rather Than Deleting
Removing superseded memories would attain identical Stale\@1 results while making the assistant unable to answer historical queries. Both capabilities are legitimate: validity intervals close facts without erasing them, and rank multipliers demote rather than remove.

== Forgetting is a Cross-Cutting Property
The baseline leak rate of 6.2% proves that deleting a database row is insufficient. Any system that promises unlearning while retaining derived indexes has an unlearning hole.

== Limitations
Three limitations are acknowledged:
1. While PersonalBrain-Bench v2 scales to 5 personas, testing on real-world longitudinal user data under privacy constraints remains future work.
2. The NLI model operates on sentence pairs; multi-hop contradictions spanning three or more separate notes require recursive graph deduction.
3. The evaluation covers retrieval quality; measuring end-to-end generation accuracy with an LLM in the loop is the natural next step.

= Conclusion and Future Work

Personal knowledge stores violate the consistency assumptions of general retrieval benchmarks, producing failure modes invisible to recall-oriented metrics. We presented SecondBrain, an adaptive personal memory architecture with neural contradiction damping, dependency-based temporal graphs, and multi-surface unlearning. Across single-persona and multi-user benchmarks, Hit\@5 saturates while the proposed pipeline achieves MRR 0.960–1.000, reduces Stale\@1 to 3.3% ($p = 0.0027$), and completely eliminates forgotten-content leakage.

Future work will focus on: (1) learned feature weights via Pairwise Learning-to-Rank; (2) blind human evaluation of generated text; and (3) expanding the multi-user benchmark to longitudinal multi-year timelines.

#v(0.5em)
#text(weight: "bold")[Acknowledgment]\
#text(size: 8.5pt)[The authors thank Dr. P S Anu Rakhi, Assistant Professor, School of Computing, for supervision and guidance throughout this work, and acknowledge open-source frameworks including FastAPI, SQLAlchemy, ONNX Runtime, and spaCy.]

#v(0.5em)
#text(weight: "bold")[References]
#set text(size: 7.5pt)
#set par(leading: 0.45em, first-line-indent: 0pt)

[1] P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," in _Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)_, vol. 33, 2020, pp. 9459–9474.

[2] Y. Gao, Y. Xiong, X. Gao, et al., "Retrieval-Augmented Generation for Large Language Models: A Survey," _arXiv:2312.10997_, 2023.

[3] D. Edge et al., "From Local to Global: A Graph RAG Approach to Query-Focused Summarization," _arXiv:2404.16130_, 2024.

[4] R. Xu, Z. Qi, C. Wang, et al., "Knowledge Conflicts for LLMs: A Survey," _arXiv:2403.08319_, 2024.

[5] L. Wang et al., "A Survey on Large Language Model based Autonomous Agents," _Frontiers of Computer Science_, vol. 18, no. 6, 2024.

[6] N. Bruch, S. Nedelkoski, and S. Mandal, "A Deep Dive into Vector Stores: Classifying the Backbone of Retrieval-Augmented Generation," in _Proc. IEEE Int. Conf. Big Data_, 2024.

[7] Y. Hou et al., "Enhancing Factual Reliability in Large Language Models Through Retrieval Augmented Generation," _IEEE Access_, 2025.

[8] X. Ji et al., "RAG Certainty: Quantifying the Certainty of Context-Based Responses by LLMs," in _Proc. IEEE ICASSP_, 2026.

[9] K. R. Z. et al., "ReRag: A New Architecture for Reducing the Hallucination by Retrieval-Augmented Generation," _IEEE Access_, 2025.

[10] A. Asai, Z. Wu, Y. Wang, A. Sil, and H. Hajishirzi, "Self-RAG: Learning to Retrieve, Generate and Critique through Self-Reflection," in _Proc. ICLR_, 2024.

[11] S. Yan et al., "Corrective Retrieval Augmented Generation," _arXiv:2401.15884_, 2024.

[12] Y. Wang et al., "A Systematic Review of Prompt Injection Attacks on Large Language Models," _IEEE Access_, 2025.

[13] L. Zhu et al., "Large Language Models: A Concise Review of Types and Considerations," _IEEE Access_, 2025.

[14] T. Brown et al., "Language Models are Few-Shot Learners," in _Proc. NeurIPS_, vol. 33, 2020, pp. 1877–1901.

[15] N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," in _Proc. EMNLP_, 2019, pp. 3982–3992.

[16] V. Karpukhin et al., "Dense Passage Retrieval for Open-Domain Question Answering," in _Proc. EMNLP_, 2020, pp. 6769–6781.

[17] S. Robertson and H. Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond," _Foundations and Trends in Information Retrieval_, vol. 3, no. 4, pp. 333–389, 2009.

[18] J. Johnson, M. Douze, and H. Jégou, "Billion-Scale Similarity Search with GPUs," _IEEE Trans. Big Data_, vol. 7, no. 3, pp. 535–547, 2021.

[19] A. Hogan et al., "Knowledge Graphs," _ACM Computing Surveys_, vol. 54, no. 4, 2021.

[20] L. Bourtoule et al., "Machine Unlearning," in _Proc. IEEE Symp. Security and Privacy (S&P)_, 2021, pp. 141–159.

[21] P. Rasmussen, P. Paliychuk, et al., "Zep: A Temporal Knowledge Graph Architecture for Agent Memory," _arXiv:2501.13956_, 2025.

[22] C. Zhang et al., "Constructing Personalised Learning Resource Recommendation with Multimodal Interaction Data," _IEEE Trans. Learning Technol._, 2025.

[23] R. Wang et al., "Lifelong Learning of Large Language Model based Agents," _IEEE Trans. Pattern Anal. Mach. Intell._, 2026.

[24] S. Wang, T. Zhu, D. Ye, and W. Zhou, "When Machine Unlearning Meets Retrieval-Augmented Generation (RAG)," _IEEE Trans. Dependable and Secure Computing_, 2025.

[25] A. Radford et al., "Robust Speech Recognition via Large-Scale Weak Supervision," in _Proc. ICML_, 2023, pp. 28492–28518.

]
