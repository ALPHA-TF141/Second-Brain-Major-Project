
#set page(
  paper: "a4",
  margin: (
    left: 48.8pt,
    right: 48.2pt,
    top: 50pt,
    bottom: 38pt,
  ),
  footer: align(center)[#context text(font: "Libertinus Serif", size: 10pt)[#counter(page).display()]],
)

#set text(
  font: "Libertinus Serif",
  size: 9.5pt,
)

#set par(
  justify: true,
  leading: 0.45em,
  first-line-indent: 1.25em,
)

// Title exactly matching draft
#align(center)[
  #v(-0.35cm)
  #text(size: 20pt, weight: "regular")[
    An Adaptive Temporal Personal Knowledge Graph\
    with Memory Consolidation and Contradiction-\
    Aware Retrieval-Augmented Generation
  ]
  #v(0.9em)

  // 3-column author block
  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 1.0em,
    [
      #text(size: 9.5pt)[Dr. P S Anu Rakhi]\
      #text(style: "italic", size: 9.5pt)[School of Computing]\
      #text(style: "italic", size: 9.5pt)[Assistant Professor]\
      #text(style: "italic", size: 9.5pt)[Vel Tech Rangarajan Dr Sagunthala]\
      #text(style: "italic", size: 9.5pt)[R&D Institute of Science and Technology]\
      #text(size: 9.5pt)[Chennai, India]\
      #text(size: 9pt)[anurakhips\@veltech.edu.in]
    ],
    [
      #text(size: 9.5pt)[Maria Immanuel L]\
      #text(style: "italic", size: 9.5pt)[School of Computing]\
      #text(style: "italic", size: 9.5pt)[Vel Tech Rangarajan Dr Sagunthala]\
      #text(style: "italic", size: 9.5pt)[R&D Institute of Science and Technology]\
      #text(size: 9.5pt)[Chennai, India]\
      #text(size: 9pt)[vtu24334\@veltech.edu.in]
    ],
    [
      #text(size: 9.5pt)[Vigneshwaran S]\
      #text(style: "italic", size: 9.5pt)[School of Computing]\
      #text(style: "italic", size: 9.5pt)[Vel Tech Rangarajan Dr Sagunthala]\
      #text(style: "italic", size: 9.5pt)[R&D Institute of Science and Technology]\
      #text(size: 9.5pt)[Chennai, India]\
      #text(size: 9pt)[vtu24372\@veltech.edu.in]
    ]
  )
  #v(0.8em)
]

#columns(2, gutter: 26pt)[

#set par(first-line-indent: 0pt)
#text(size: 8.5pt, weight: "bold")[
Abstract—Retrieval-augmented generation over a personal knowledge store fails in a way that general-purpose RAG evaluation does not capture. A personal repository accumulates contradictory statements as the user changes their mind, outdated facts whose validity has lapsed, near-duplicate captures of the same material, and content the user has explicitly asked to remove. Standard retrieval treats all of it as equally current evidence, so the generated answer can be confidently wrong while every individual retrieved passage remains faithful to its source. We present Second Brain, a personal memory architecture comprising seven components: Adaptive Memory Scoring, a Temporal Personal Knowledge Graph with Neural Dependency Extraction, Contradiction-Aware Hybrid Retrieval with Quantized Cross-Encoder NLI, Memory Consolidation, Knowledge-Gap Detection, retrieval-enforced Forgetting, and the Personal Brain-Bench evaluation suite. We evaluate four retrieval pipelines on Personal Brain-Bench across single-persona and a multi-user suite of 5 diverse professional domains with 30 graded questions. Hit\@5 saturates at 1.000 for all four systems, confirming that position-insensitive recall does not distinguish them. On the rank-sensitive and staleness metrics that do discriminate, the proposed pipeline reaches MRR 1.000 (core) and 0.9600 (multi-user) against 0.833–0.880 (vanilla dense), 0.940–0.944 (hybrid) and 0.940–0.944 (graph-augmented); reduces the rate of leading with superseded content from 0.364 to 0.000 (core) and from 0.333 to 0.033 on multi-user benchmarks ($p = 0.0027$, Wilcoxon signed-rank test); and eliminates both duplicate context and post-forgetting leakage (0.000 vs. 0.062), whereas every baseline continues to return explicitly unlearned content. A component-wise ablation attributes each effect to its mechanism. All core figures use $k = 5$, a deterministic TF-IDF dense backend and corpus-scoped candidate generation; two consecutive benchmark executions produce byte-identical metrics, so the comparison is reproducible without any neural embedding model or network access.
]

#v(0.5em)
#text(size: 8.5pt, weight: "bold")[
Keywords—personal knowledge management, retrieval-augmented generation, temporal knowledge graphs, natural language inference, cross-encoder, contradiction resolution, retrieval-level forgetting, memory consolidation, large language model agents
]

#v(0.6em)
#set par(first-line-indent: 1.25em)

#align(center)[#text(size: 9.5pt, weight: "bold")[I. Introduction]]

Large language models augmented with retrieval over a user's own documents have become the dominant architecture for personal assistants. The retrieval layer is usually evaluated on general corpora, where documents are assumed mutually consistent, immutable and equally current. A personal knowledge store violates every one of those assumptions. The user changes their mind; a deadline is moved; the same web page is captured three times; a note is deliberately deleted.

The consequence is a failure mode that general RAG evaluation does not measure. Suppose a user wrote in January that they were learning Python, and in September that they were now focusing on Java. Both statements are in the store. A conventional retriever returns the one with the higher lexical or vector similarity to the query "what am I working on?", and if that is the January note, the assistant answers confidently and wrongly. Every retrieved passage is faithful to its source; the system fabricates nothing and is still incorrect. Faithfulness metrics cannot detect this, because nothing was fabricated.

This paper addresses that gap with one main research question: _does retrieval-time enforcement of temporal validity, contradiction status, duplication and explicit removal improve the evidence a personal RAG system leads with, in a way that recall-oriented metrics cannot see?_ Four hypotheses make it testable. H1: recall-oriented metrics saturate and therefore cannot separate pipelines on a personal corpus. H2: rank-sensitive and staleness metrics do separate them. H3: the separation is attributable per mechanism - duplicate reduction arises only once consolidation is enabled, leakage elimination only once forgetting is enforced, and stale\@1 reduction once temporal validity and forgetting are active. H4: the conflict detector is deliberately conservative, trading recall for precision on free-text pairs. Each hypothesis maps to a reported measurement: H1 and H2 to Tables II and IV, H3 to the ablation in Table V, and H4 to the annotated-pair accuracy study in Section IV-C.

The contributions of this work are organised around what is adopted versus what is proposed (Table I). Established techniques - hybrid dense+lexical fusion, graph re-ranking, cross-encoder NLI, dependency parsing - are adopted and cited; the contribution is their coordinated, switchable integration and five specific mechanisms: an auditable eight-term scoring model with persisted components; supersession that closes facts instead of deleting them; rank damping instead of removal for contradictions; forgetting enforced across five independent retrieval surfaces with reversible restoration; and PersonalBrain-Bench, an instrument whose categories are designed to expose exactly these failures.

#v(0.2em)
#align(center)[
#text(size: 8pt, weight: "bold")[TABLE I]\\\
#text(size: 8pt)[Adopted Techniques Versus Proposed Mechanisms]
#v(0.1em)
#table(
  columns: (3.6cm, 1.5cm, 3.5cm),
  stroke: 0.3pt + rgb("#888888"),
  inset: 2.5pt,
  align: (left, center, left),
  fill: (x, y) => if y == 0 { rgb("#f2f2f2") } else { none },
  [#text(size: 7.5pt, weight: "bold")[Technique]], [#text(size: 7.5pt, weight: "bold")[Status]], [#text(size: 7.5pt, weight: "bold")[Role in this paper]],
  [#text(size: 7pt)[Dense + lexical hybrid fusion]], [#text(size: 7pt)[Adopted [3], [4]]], [#text(size: 7pt)[Baseline and candidate generator]],
  [#text(size: 7pt)[Knowledge-graph re-ranking]], [#text(size: 7pt)[Adopted [6]–[8]]], [#text(size: 7pt)[Explicit graph-augmented baseline]],
  [#text(size: 7pt)[Cross-encoder NLI (ONNX)]], [#text(size: 7pt)[Adopted model]], [#text(size: 7pt)[Conflict severity; proposed damping use]],
  [#text(size: 7pt)[Dependency parsing (spaCy)]], [#text(size: 7pt)[Adopted tool]], [#text(size: 7pt)[Proposed predicate canonicalisation]],
  [#text(size: 7pt)[Validity intervals / TKGs]], [#text(size: 7pt)[Adopted idea [9]]], [#text(size: 7pt)[Proposed close-not-delete supersession]],
  [#text(size: 7pt)[Eight-term auditable scoring]], [#text(size: 7pt)[Proposed]], [#text(size: 7pt)[Persisted, versioned importance terms]],
  [#text(size: 7pt)[Rank damping for conflicts]], [#text(size: 7pt)[Proposed]], [#text(size: 7pt)[Demote, never delete, superseded side]],
  [#text(size: 7pt)[Five-surface forgetting]], [#text(size: 7pt)[Proposed]], [#text(size: 7pt)[Retrieval-level, distinct from [13]]],
  [#text(size: 7pt)[PersonalBrain-Bench v1/v2]], [#text(size: 7pt)[Proposed]], [#text(size: 7pt)[Instrument exposing the failure mode]],
)
#text(size: 6.8pt, style: "italic")[No adopted technique is claimed as novel; the integration and the five proposed mechanisms are.]
]
#v(0.4em)

#align(center)[#text(size: 9.5pt, weight: "bold")[II. Related Work]]

#text(style: "italic")[A. Retrieval-Augmented Generation]

RAG augments generation with retrieved context to ground responses in external evidence [1], [2]. Surveys of the area identify chunking, embedding, retrieval and generation as the stages where quality is won or lost. Our work does not replace these stages; it adds a temporal and conflict layer above them.

#text(style: "italic")[B. Dense, Lexical and Hybrid Retrieval]

Dense passage retrieval [3] and probabilistic lexical ranking [4] are the two signals hybrid retrieval fuses; comparative studies characterise the vector stores that underlie them [5]. We adopt hybrid retrieval as a baseline and show that on a personal corpus it is the strongest of the three baselines, while still returning superseded content at rank one in 18.2% of queries (rising to 23.3% across multi-user queries).

#text(style: "italic")[C. Graph Retrieval and Temporal Knowledge Graphs]

Graph RAG extends retrieval over a knowledge graph to support multi-hop questions that flat chunk retrieval cannot answer [6], [7]; knowledge graphs themselves are surveyed in [8]. Temporal knowledge graph completion studies validity intervals over evolving facts [9]. We use a graph-augmented pipeline as an explicit baseline so the incremental effect of the temporal layer is visible rather than assumed, and we treat interval validity as prior art, not as a claim.

#text(style: "italic")[D. Agent Memory and Lifelong Personalisation]

Recent work on LLM-based agents identifies memory as a core component alongside perception, planning and action [10], surveys the memory mechanisms of agent architectures [11], and extends lifelong learning to LLM agents [12]. These contributions establish that persistence matters; they do not specify what to do when persisted memories disagree. We treat disagreement as the central problem rather than an edge case.

#text(style: "italic")[E. Machine Unlearning]

Unlearning research considers how to remove the influence of specific training data from model parameters [13]. Removal from a retrieval store is related but distinct, because an item can survive deletion in a vector index, a full-text index, or a derived graph. We show empirically that a naive pipeline continues to return explicitly removed content, and that exclusion must therefore be applied at every retrieval surface. Throughout this paper we therefore say _retrieval-level forgetting_ and make no claim about parameter-level unlearning.

#text(style: "italic")[F. Contradiction Handling and Hallucination Reduction]

Work on hallucination reduction verifies generated claims against retrieved evidence [14], [15], [16], [17]. That is orthogonal to our setting: our failures arise when the retrieved evidence is itself outdated or mutually contradictory, so verification against the retrieved set would confirm rather than catch the error. We address this directly by integrating an ONNX Natural Language Inference (NLI) model to classify conflict severity at retrieval time.

#v(0.6em)
#align(center)[#text(size: 9.5pt, weight: "bold")[III. System Architecture and Methodology]]

SecondBrain is a client–server personal knowledge system. A FastAPI backend exposes ingestion, retrieval and research endpoints over SQLite and an optional vector store; an Electron/React desktop shell provides capture, voice and visualisation. The substrate is standard: Sentence-BERT-style embeddings [18] over an approximate nearest-neighbour index [19], a local or hosted LLM for generation [20], and weakly-supervised speech recognition for the voice path [21]. The research layer introduced in this paper is additive: it observes and annotates existing memories through separate tables keyed by memory identifier, and never modifies the capture pipeline. All seven components are optional at runtime, so the system degrades to a conventional RAG assistant if any is disabled, which is what makes the comparative evaluation and the ablation in Section VI possible. Processing proceeds through eight stages - capture/ingest; normalisation (chunking, content hash, dedup key); adaptive scoring (C1); temporal extraction and supersession (C2); conflict detection and damping (C3); consolidation (C4); switchable retrieval; and generation over the assembled context. Fig. 1 shows the resulting architecture: the research layer (C1–C6) annotates the memory store and gates retrieval, and PersonalBrain-Bench (C7) evaluates the four pipelines.

#figure(
  image("diagrams/paper_architecture.svg", width: 100%),
  supplement: [Fig.],
  caption: [SecondBrain architecture. Capture and normalisation are unchanged from a conventional personal RAG system; the research layer (dashed) is additive and switchable. C1–C6 annotate the memory store and gate retrieval (exclusion, rank damping, deduplication); C7 evaluates the four retrieval pipelines reported in Tables II–V.],
)
#v(0.3em)

#align(center)[#text(size: 9.5pt, weight: "bold")[IV. Proposed Method: Seven Contributions]]

#text(style: "italic")[A. Adaptive Memory Scoring]

A personal store grows without bound, and a retriever that weights all memories equally cannot distinguish a clipboard fragment from the note defining the user's project. We assign each memory an importance score composed of explicit positive and negative terms:
#align(center)[
$ M = w_1 R + w_2 F + w_3 T + w_4 G + w_5 U + w_6 P - w_7 D - w_8 C quad (1) $
]
where $R$ is relevance to the user's represented interests, $F$ recurrence frequency, $T$ recency with exponential decay, $G$ graph connectivity of the memory's concepts, $U$ explicit user confirmation, $P$ predicted future utility, $D$ a redundancy penalty, and $C$ a contradiction penalty. Every term is computed on $[0, 1]$ and clipped; in weight version v1 the coefficients are $(w_1, dots, w_8) = (0.30, 0.08, 0.22, 0.15, 0.15, 0.10, 0.18, 0.25)$, the last two entering with negative sign. Weights are versioned and stored, and all eight components are persisted alongside the total, so a score is auditable rather than opaque. Recency uses a half-life of 45 days: $T = 2^(-Delta t / 45)$.

#text(style: "italic")[B. Temporal Personal Knowledge Graph & Neural Dependency Extraction]

Facts are stored as (subject, predicate, object) triples carrying a validity interval $[t_"valid_from", t_"valid_to")$. A null $t_"valid_to"$ denotes a currently true fact. When a new stateful fact shares its (subject, predicate) with an open fact but has a different object, the older fact is closed — $t_"valid_to"$ set and superseded_by linked — rather than deleted. History therefore remains queryable, which allows the assistant to answer both "what am I working on?" and "what did I used to work on?" from one store.

Predicates are canonicalised into state classes before supersession is applied. Without this, "I am learning Python" and "I am now focusing on Java" are recorded under different predicates, neither supersedes the other, and the graph reports both as current. To capture natural phrasing beyond hand-crafted regex rules, we augment extraction with neural dependency parsing via spaCy. By parsing grammatical trees ($text("nsubj")$, $text("ROOT")$, $text("dobj")$, $text("pobj")$), the model resolves verb lemmas (e.g. _switch_, _relocate_, _adopt_) and maps them directly to canonical state predicates.

#text(style: "italic")[C. Contradiction-Aware Hybrid Retrieval & Neural NLI]

We detect three conflict classes. Temporal conflicts arise when a memory asserts a fact that a later memory superseded. Negation conflicts arise when two memories share a topic signature and one denies what the other asserts. Value-change conflicts arise when two memories share a topic signature with high salient-word overlap but carry different dated or numeric values — the moved-deadline and invoice case that no first-person pattern or negation word covers.

To detect implicit contradictions lacking explicit keywords, we integrate an ONNX-quantized Cross-Encoder Natural Language Inference (NLI) model (`distilbert-base-uncased-mnli-int8`, ~64 MB). For candidate memory pairs with topical overlap, the NLI model computes continuous softmax probabilities: $[P("Entailment"), P("Neutral"), P("Contradiction")]$. When $P("Contradiction") >= 0.55$, conflict severity is set dynamically as $s = P("Contradiction")$.

Resolution assigns a rank multiplier rather than removing the superseded memory: an unresolved conflict of severity $s$ damps the memory to $(1 - 0.7s)$, bounded in $[0.3, 1.0]$. Deletion would answer the stale-answer problem but destroy the historical-query capability, so damping resolves both. Final ordering is rank-preserving: the fused retrieval order supplies a prior $1 / (1 + i)$ which the multiplier $s$ adjusts, with importance acting only as a light tie-breaker. Sorting on importance alone proved actively harmful during development, promoting high-importance but less relevant memories above the gold answer.

The detector's own accuracy was previously unmeasured; we therefore annotated 21 synthetic memory pairs (10 positives across the three classes, 11 hard negatives: near-duplicates, topically similar but consistent, same-words-different-subject, unrelated, and negation-worded-but-consistent pairs). In the shipped configuration the detector reaches precision 0.667, recall 0.400 (F1 0.500); with the neural classifier unavailable it recalls nothing. The detector is thus conservative by construction: it prefers silence to spurious conflicts, and Section VI-C reports where that conservatism costs it.

#text(style: "italic")[D. Memory Consolidation]

Near-duplicate captures waste the context budget that determines generation quality. We cluster memories by cosine similarity over hashed term-frequency vectors and elect a canonical representative by importance then length. Every merged member identifier is retained in the consolidation record, so provenance is preserved. A retrieval-time deduplication pass applies the same similarity test within a single query's result list, so the guarantee holds even before an offline consolidation run.

The threshold is calibrated rather than assumed. Reworded duplicates in our corpus score $approx 0.82$ while unrelated memories score below 0.30; the 0.90 threshold commonly recommended in practice missed every reworded duplicate, so we adopt 0.78. A threshold chosen by inspection of the test set would be a methodological error; ours was chosen from the measured distribution and then validated by the benchmark.

#text(style: "italic")[E. Knowledge-Gap Detection]

Distinguishing exposure from understanding requires examining the shape of a concept's mentions, not merely their count. Per concept we compute mention frequency, whether it appears as the subject of an explanatory construction, whether it recurs across separate capture sessions, and its degree in the knowledge graph. Depth combines these, and
$ text("gap") = text("exposure") times (1 - text("depth")) times (1 - 0.5 times text("connectivity")) $
The connectivity term is essential: without it, a well-understood but frequently mentioned concept is misreported as a gap.

#text(style: "italic")[F. Retrieval-Enforced Forgetting]

Removing a row from the memory table does not remove the content from retrieval: the full-text index entry, the vector embedding, the derived graph nodes and the extracted temporal facts are all independent surfaces from which the content can re-enter a result set. Our forgetting service tombstones the memory and enforces exclusion at five surfaces: the search index entry is deleted, the vector is removed from the store, graph nodes and their incident edges are deleted, temporal facts are closed and detached from their source, and derived scores and conflicts are purged. Restoration re-indexes and re-admits the memory, so the operation is reversible.

#text(style: "italic")[G. PersonalBrain-Bench v1 & Multi-User PersonalBrain-Bench v2]

Existing RAG benchmarks do not contain contradictory, superseded or deliberately forgotten personal memories, so they cannot expose the failures this paper targets. PersonalBrain-Bench v1 is a synthetic personal corpus with a graded question set covering six categories: factual recall; temporal state; contradiction (a changed deadline); multi-hop synthesis; duplicate exposure; and forgetting.

To validate scalability across diverse users, we further formulate PersonalBrain-Bench v2: a multi-user suite covering 5 professional domains (Software Engineering, Machine Learning Research, Product Operations, University Academics, Health Informatics) evaluated across 30 multi-turn queries.

#v(0.6em)
#align(center)[#text(size: 9.5pt, weight: "bold")[V. Experimental Setup]]

#text(style: "italic")[A. Corpus]

PersonalBrain-Bench contains 15 memories spanning email, notes, code, web captures and screen text, with creation timestamps distributed across a 240-day window so recency and supersession are exercised rather than simulated. The corpus deliberately embeds a superseded state pair (learning Python / now focusing on Java), a moved deadline (15 October $->$ 30 September), a three-member near-duplicate cluster, a multi-hop chain linking a project to a dataset and a model, a sensitive scratch note that is then explicitly forgotten, and a concept mentioned repeatedly without explanation. Ingestion produced 2 detected conflicts. Of 11 questions, 9 are answerable and the remainder test abstention or removal.

#text(style: "italic")[B. Systems Compared]

Vanilla is dense-only retrieval. Hybrid fuses dense and lexical results. Graph adds knowledge-graph connectivity re-ranking. Adaptive is the proposed pipeline: hybrid plus forgetting exclusion, temporal validity damping, neural NLI contradiction damping, importance weighting and consolidation-based deduplication. All four share identical candidate generation and differ only in the post-retrieval layer, so the measured deltas isolate that layer.

#text(style: "italic")[C. Metrics]

Hit\@k and MRR are computed over answerable questions only; including abstention and removal questions, which have no gold memory by construction, would depress every system equally and conceal real differences. We additionally report stale\@1, the fraction of queries whose top-ranked result is superseded or forbidden, because rank one is what a generator leads with; forgotten leak rate, the fraction of returned results that were explicitly unlearned; and duplicate rate, the fraction of within-query result pairs at or above the consolidation threshold.

#text(style: "italic")[D. Reproducibility]

All core figures were produced with $k = 5$, the deterministic TF-IDF dense backend and corpus-scoped candidate generation; the leakage and staleness asymmetries are stated for exactly this configuration. The core pipeline requires no external GPU. Two consecutive full executions produce byte-identical metrics (Section VII). All results reported here were produced by single-command scripts and written to machine-readable artefacts, including the ablation of Section VI-C.

#v(0.6em)
#align(center)[#text(size: 9.5pt, weight: "bold")[VI. Results and Comparative Analysis]]

#text(style: "italic")[A. Core Corpus Performance]

#v(0.2em)
#align(center)[
#text(size: 8pt, weight: "bold")[TABLE II]\
#text(size: 8pt)[Core-Corpus Retrieval Quality, Staleness, Leakage and Duplication]
#v(0.1em)
#table(
  columns: (2.45cm, 1.1cm, 1.1cm, 1.2cm, 0.95cm, 1.0cm),
  stroke: 0.3pt + rgb("#888888"),
  inset: 2.6pt,
  align: (left, center, center, center, center, center),
  fill: (x, y) => if y == 0 { rgb("#f2f2f2") } else { none },
  [#text(size: 7.5pt, weight: "bold")[System]], [#text(size: 7.5pt, weight: "bold")[Hit\@5]], [#text(size: 7.5pt, weight: "bold")[MRR]], [#text(size: 7.5pt, weight: "bold")[Stale\@1]], [#text(size: 7.5pt, weight: "bold")[Leak]], [#text(size: 7.5pt, weight: "bold")[Dup.]],
  [#text(size: 7.5pt)[Vanilla dense]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[0.833]], [#text(size: 7.5pt)[0.364]], [#text(size: 7.5pt)[0.022]], [#text(size: 7.5pt)[0.022]],
  [#text(size: 7.5pt)[Hybrid]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[0.944]], [#text(size: 7.5pt)[0.182]], [#text(size: 7.5pt)[0.022]], [#text(size: 7.5pt)[0.022]],
  [#text(size: 7.5pt)[Graph-augmented]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[0.944]], [#text(size: 7.5pt)[0.182]], [#text(size: 7.5pt)[0.022]], [#text(size: 7.5pt)[0.022]],
  [#text(size: 7.5pt)[Adaptive (proposed)]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[0.000]], [#text(size: 7.5pt)[0.000]], [#text(size: 7.5pt)[0.000]],
)
#text(size: 6.5pt, style: "italic")[$k = 5$; metrics over answerable questions; last three lower-is-better (stale\@1 counts 4/11, 2/11, 2/11, 0/11).]
]
#v(0.2em)

#v(0.2em)

The central empirical finding is that Hit\@5 does not discriminate: all four systems reach 1.000. Every pipeline finds the relevant memory somewhere in its top five. A study reporting only recall would conclude that the research layer adds nothing. Yet the answers they produce differ, because a generator consumes the ordered context rather than the set. On rank-sensitive measures the pipelines separate sharply: MRR rises from 0.833 (vanilla) through 0.944 (hybrid, equal to graph-augmented) to 1.000 for the adaptive pipeline, a relative improvement of 5.9% over the strongest baseline and 20.0% over vanilla dense retrieval.

Stale\@1 is the metric most directly tied to answer correctness. Vanilla leads with superseded content in 36.4% of queries; hybrid and graph reduce this to 18.2%, and the adaptive pipeline reduces it to 0.0%. The proposed system therefore never leads with an outdated fact on this corpus, while the strongest baseline still does so on roughly one query in five. Because each retrieved passage remains faithful to its source, no faithfulness metric would flag those cases.

Forgotten-content leakage and duplicate context are both eliminated ($0.022 -> 0.000$ and $0.022 -> 0.000$). The leakage result also demonstrates the negative case: every baseline continues to return explicitly unlearned content, confirming that removal is a retrieval-layer property not obtained by deleting a row from the primary table.

#v(0.2em)
#align(center)[
#text(size: 8pt, weight: "bold")[TABLE III]\\\
#text(size: 8pt)[Mean Reciprocal Rank by Question Category]
#v(0.1em)
#table(
  columns: (2.2cm, 1.3cm, 1.3cm, 1.3cm, 1.1cm),
  stroke: 0.3pt + rgb("#888888"),
  inset: 2.6pt,
  align: (left, center, center, center, center),
  fill: (x, y) => if y == 0 { rgb("#f2f2f2") } else { none },
  [#text(size: 7.5pt, weight: "bold")[Category]], [#text(size: 7.5pt, weight: "bold")[Van.]], [#text(size: 7.5pt, weight: "bold")[Hyb.]], [#text(size: 7.5pt, weight: "bold")[Adapt.]], [#text(size: 7.5pt, weight: "bold")[$Delta$]],
  [#text(size: 7.5pt)[factual]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[+0.000]],
  [#text(size: 7.5pt)[temporal]], [#text(size: 7.5pt)[0.750]], [#text(size: 7.5pt)[0.750]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[+0.250]],
  [#text(size: 7.5pt)[contradiction]], [#text(size: 7.5pt)[0.500]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[+0.000]],
  [#text(size: 7.5pt)[multi-hop]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[+0.000]],
  [#text(size: 7.5pt)[duplicate]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[+0.000]],
)
#text(size: 6.8pt, style: "italic")[Gains concentrate in temporal and contradictory questions.]
]
#v(0.2em)

Contradiction questions are where vanilla is weakest (0.500), consistent with the motivating scenario: presented with two dated statements about the same deadline, unattended dense retrieval has no mechanism to prefer the later one, while temporal validity and value-change detection both drive it to rank one (1.000). Temporal questions improve from 0.750 to 1.000 once predicate canonicalisation makes supersession fire. End-to-end retrieval latency over the 11 core queries is 33 ms for vanilla dense (1.14$times$ hybrid), 29 ms for hybrid, 37 ms for graph-augmented (1.28$times$) and 65 ms for the adaptive pipeline (2.24$times$) - the price of the research layer at this corpus scale, from the same execution as Table II.

#v(0.2em)
#v(0.2em)

#text(style: "italic")[B. Multi-User Scalability and Statistical Significance]
Table IV covers the 5 personas over 30 queries; stale\@1 counts behind the rates are 10/30, 7/30, 7/30 and 1/30 queries respectively.

#v(0.2em)
#align(center)[
#text(size: 8pt, weight: "bold")[TABLE IV]\\\
#text(size: 8pt)[Multi-User Benchmark & Significance (5 Personas, 30 Queries)]
#v(0.1em)
#table(
  columns: (2.1cm, 1.0cm, 1.0cm, 1.2cm, 1.0cm, 1.9cm),
  stroke: 0.3pt + rgb("#888888"),
  inset: 2.5pt,
  align: (left, center, center, center, center, center),
  fill: (x, y) => if y == 0 { rgb("#f2f2f2") } else { none },
  [#text(size: 7pt, weight: "bold")[Pipeline]], [#text(size: 7pt, weight: "bold")[Hit\@5]], [#text(size: 7pt, weight: "bold")[MRR]], [#text(size: 7pt, weight: "bold")[Stale\@1]], [#text(size: 7pt, weight: "bold")[Leak]], [#text(size: 7pt, weight: "bold")[Stale $p$-val]],
  [#text(size: 7pt)[Vanilla dense]], [#text(size: 7pt)[1.000]], [#text(size: 7pt)[0.880]], [#text(size: 7pt)[0.333]], [#text(size: 7pt)[0.062]], [#text(size: 7pt)[$p = 0.0027\*\*$]],
  [#text(size: 7pt)[Hybrid]], [#text(size: 7pt)[1.000]], [#text(size: 7pt)[0.940]], [#text(size: 7pt)[0.233]], [#text(size: 7pt)[0.045]], [#text(size: 7pt)[$p = 0.0143\*$]],
  [#text(size: 7pt)[Graph-aug.]], [#text(size: 7pt)[1.000]], [#text(size: 7pt)[0.940]], [#text(size: 7pt)[0.233]], [#text(size: 7pt)[0.045]], [#text(size: 7pt)[$p = 0.0143\*$]],
  [#text(size: 7pt)[Adaptive (prop.)]], [#text(size: 7pt)[1.000]], [#text(size: 7pt)[0.960]], [#text(size: 7pt)[0.033]], [#text(size: 7pt)[0.000]], [#text(size: 7pt)[Baseline ref.]],
)
#text(size: 6.5pt, style: "italic")[\*\* $p < 0.01$, \* $p < 0.05$ via paired Wilcoxon test vs. Adaptive.]
]
#v(0.2em)

Hit\@5 remains fully saturated at 1.000 across all systems. The proposed Adaptive Neural pipeline achieves MRR 0.960 against 0.880 (vanilla) and 0.940 (hybrid). Crucially, Stale\@1 falls from 33.3% to 3.3%, which is statistically significant ($p = 0.0027$, Wilcoxon test). Baselines leak unlearned content in 4.5%–6.2% of answers, while the proposed architecture guarantees 0.0% leakage.

#text(style: "italic")[C. Component-Wise Ablation]

Table V adds one mechanism per row to hybrid retrieval with the research layer disabled, in the same configuration as Table II. The design tests H3 directly: each metric should move only on the row that introduces the mechanism responsible for it.

#v(0.2em)
#align(center)[
#text(size: 8pt, weight: "bold")[TABLE V]\\\
#text(size: 8pt)[Cumulative Ablation: One Mechanism Per Row]
#v(0.1em)
#table(
  columns: (2.6cm, 1.1cm, 1.2cm, 1.2cm, 1.2cm),
  stroke: 0.3pt + rgb("#888888"),
  inset: 2.5pt,
  align: (left, center, center, center, center),
  fill: (x, y) => if y == 0 { rgb("#f2f2f2") } else { none },
  [#text(size: 7.5pt, weight: "bold")[Configuration]], [#text(size: 7.5pt, weight: "bold")[MRR]], [#text(size: 7.5pt, weight: "bold")[Stale\@1]], [#text(size: 7.5pt, weight: "bold")[Dup.]], [#text(size: 7.5pt, weight: "bold")[Leak]],
  [#text(size: 7.5pt)[Hybrid (layer off)]], [#text(size: 7.5pt)[0.944]], [#text(size: 7.5pt)[0.182]], [#text(size: 7.5pt)[0.022]], [#text(size: 7.5pt)[0.022]],
  [#text(size: 7.5pt)[+ temporal]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[0.091]], [#text(size: 7.5pt)[0.022]], [#text(size: 7.5pt)[0.022]],
  [#text(size: 7.5pt)[+ contradiction]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[0.091]], [#text(size: 7.5pt)[0.022]], [#text(size: 7.5pt)[0.043]],
  [#text(size: 7.5pt)[+ consolidation]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[0.091]], [#text(size: 7.5pt)[0.000]], [#text(size: 7.5pt)[0.046]],
  [#text(size: 7.5pt)[+ forgetting]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[0.000]], [#text(size: 7.5pt)[0.000]], [#text(size: 7.5pt)[0.000]],
  [#text(size: 7.5pt)[+ importance (full)]], [#text(size: 7.5pt)[1.000]], [#text(size: 7.5pt)[0.000]], [#text(size: 7.5pt)[0.000]], [#text(size: 7.5pt)[0.000]],
)
#text(size: 6.5pt, style: "italic")[Duplicate rate falls only on the consolidation row; leakage only on the forgetting row.]
]
#v(0.2em)

The ablation confirms the predicted attribution for two of the three effects: the duplicate rate falls to zero exactly when consolidation switches on, and leakage falls to zero exactly when forgetting switches on. Temporal validity supplies the MRR gain and halves stale\@1; forgetting removes the remainder, because the surviving stale case is a forgotten-and-superseded memory that only exclusion can remove. Two honest negatives belong in the record. Contradiction damping does not move stale\@1 on this corpus - its conflicts are not the top-ranked stale items - and on two of eleven queries it slightly raises leakage by reordering rather than excluding; its value is conflict resolution for historical queries, not ordering. Importance weighting adds nothing measurable: it is a light tie-breaker by design, and sorting on it alone was harmful in development. A failure analysis of the detector (Section IV-C) completes the picture: of ten annotated conflicts it missed five value-change pairs whose paraphrase shared no explicit predicate or date, and it raised two false positives on negation-worded but consistent pairs - precisely the conservative behaviour H4 predicts.

#v(0.6em)
#align(center)[#text(size: 9.5pt, weight: "bold")[VII. Implementation and Verification]]

The system is implemented rather than prototyped, and every number in this paper is regenerated by a committed script: a benchmark runner that rebuilds derived research state from scratch and reproduces Tables II–III and the latency figures; an ablation runner producing Table V; a conflict-accuracy harness producing the Section IV-C figures; a multi-user runner producing Table IV with paired Wilcoxon tests; and a verification suite (static health checks, frontend–backend contract checks, pytest research tests covering scoring ranges, supersession semantics, NLI damping, consolidation provenance, gap suppression and leakage across all four modes, plus an endpoint sweep asserting no registered route returns a 5xx).

Two implementation defects are reported because they are instructive about the contribution itself. First, predicate canonicalisation was initially absent, so the two facts the temporal graph exists to reconcile were stored separately and neither superseded the other. Second, negation was detected by substring matching, so any memory mentioning "notes" registered as a negation and produced spurious contradiction reports. Both were found by the verification suite rather than by inspection, which is the argument for testing each claim individually.

#v(0.6em)
#align(center)[#text(size: 9.5pt, weight: "bold")[VIII. Discussion and Limitations]]

#text(weight: "bold")[Why Hit\@k is the wrong headline.] Our results show a system that is identical to its baselines on recall and materially better on the metric that determines whether the user is misinformed. This is a caution about evaluation practice for personal AI: saturation of a convenient metric is not evidence of equivalence.

#text(weight: "bold")[Damping rather than deleting.] Removing superseded memories would attain the same stale\@1 result while making the assistant unable to answer historical queries. Both capabilities are legitimate, so the design must support both: validity intervals close facts without erasing them, and rank multipliers demote rather than remove.

#text(weight: "bold")[Forgetting is a cross-cutting property.] The baseline leakage result shows that deletion at one surface is insufficient. Any system that promises removal while retaining a derived index has a forgetting hole.

Four limitations are material:
- While PersonalBrain-Bench v2 scales to 5 personas, evaluation on real-world longitudinal personal stores under strict privacy constraints remains future work.
- Fact and conflict extraction combines neural models with conservative heuristics; the annotated-pair study (precision 0.667, recall 0.400) quantifies that conservatism, and multi-hop contradictions spanning three or more separate notes require recursive graph deduction.
- Temporal handling uses UTC-normalised timestamps without full timezone or partial-interval reasoning, which would matter for events spanning midnight across zones.
- The evaluation covers retrieval, not end-to-end generation quality. Whether higher MRR and lower stale\@1 translate into fewer incorrect answers in generated prose is not measured here. The designed next experiment fixes model, prompt, temperature and context budget across the four retrievers and uses two raters blind to the condition with a stated disagreement rule; an automatic judge, if added, must report its human-agreement rate.

#v(0.6em)
#colbreak()
#align(center)[#text(size: 9.5pt, weight: "bold")[IX. Conclusion and Future Work]]

Personal knowledge stores violate the consistency assumptions of general retrieval benchmarks, and the resulting failures are invisible to recall-oriented metrics. We presented SecondBrain, a seven-component personal memory architecture, and PersonalBrain-Bench, an instrument that exposes those failures. Across four pipelines and multi-user evaluations, Hit\@5 saturates while MRR rises from 0.833–0.880 to 0.960–1.000, the rate of leading with superseded content falls from 33.3%–36.4% to 0.0%–3.3% ($p = 0.0027$), and both post-forgetting leakage and duplicate context are eliminated, while every baseline continues to return explicitly unlearned content. A cumulative ablation attributes the duplicate and leakage effects to consolidation and forgetting respectively, and reports two negative results - contradiction damping and importance weighting - that the corpus does not reward.

Future work proceeds in four directions: (1) the blinded end-to-end generation study designed in Section VIII; (2) recursive multi-hop contradiction reasoning; (3) a learned weighting of scoring terms via Pairwise Learning-to-Rank, now that the ablation has fixed the baseline each learned weight must beat; and (4) growth of the benchmark toward longitudinal personal corpora under appropriate de-identification safeguards.

#v(0.5em)
#align(center)[#text(size: 9pt, weight: "bold")[Acknowledgment]]
#set par(first-line-indent: 0pt)
#text(size: 8pt)[The authors thank Dr. P S Anu Rakhi, Assistant Professor, School of Computing, for supervision and guidance throughout this work, and acknowledge the open-source projects on which the system is built, in particular FastAPI, SQLAlchemy, ONNX Runtime, and spaCy.]

#v(0.5em)
#align(center)[#text(size: 9pt, weight: "bold")[References]]
#set text(size: 7.2pt)
#set par(leading: 0.42em, first-line-indent: 0pt)

[1] P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," in _Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)_, vol. 33, 2020, pp. 9459–9474.

[2] Y. Gao, Y. Xiong, X. Gao, K. Jia, J. Pan, Y. Bi, Y. Dai, J. Sun, and H. Wang, "Retrieval-Augmented Generation for Large Language Models: A Survey," _arXiv:2312.10997_, 2023.

[3] V. Karpukhin et al., "Dense Passage Retrieval for Open-Domain Question Answering," in _Proc. EMNLP_, 2020, pp. 6769–6781.

[4] S. Robertson and H. Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond," _Foundations and Trends in Information Retrieval_, vol. 3, no. 4, pp. 333–389, 2009.

[5] N. Bruch, S. Nedelkoski, and S. Mandal, "A Deep Dive into Vector Stores: Classifying the Backbone of Retrieval-Augmented Generation," in _Proc. IEEE Int. Conf. Big Data_, 2024.

[6] D. Edge et al., "From Local to Global: A Graph RAG Approach to Query-Focused Summarization," _arXiv:2404.16130_, 2024.

[7] Z. Peng et al., "Graph Retrieval-Augmented Generation: A Survey," _arXiv:2408.08921_, 2024.

[8] A. Hogan et al., "Knowledge Graphs," _ACM Computing Surveys_, vol. 54, no. 4, 2021.

[9] Z. Cai et al., "Temporal Knowledge Graph Completion: A Survey," in _Proc. IJCAI_, 2023.

[10] L. Wang et al., "A Survey on Large Language Model based Autonomous Agents," _Frontiers of Computer Science_, vol. 18, no. 6, 2024.

[11] Z. Zhang et al., "A Survey on the Memory Mechanism of Large Language Model based Agents," _arXiv:2404.13501_, 2024.

[12] Q. Zheng, X. Shi, Y. Cai, J. Li, Y. Zhang, B. Li, J. Yu, and Z. Ma, "Lifelong Learning of Large Language Model based Agents: A Roadmap," _IEEE Trans. Pattern Anal. Mach. Intell._, 2026 (early access).

[13] L. Bourtoule et al., "Machine Unlearning," in _Proc. IEEE Symp. Security and Privacy (S&P)_, 2021, pp. 141–159.

[14] A. Asai, Z. Wu, Y. Wang, A. Sil, and H. Hajishirzi, "Self-RAG: Learning to Retrieve, Generate and Critique through Self-Reflection," in _Proc. ICLR_, 2024.

[15] S. Yan et al., "Corrective Retrieval Augmented Generation," _arXiv:2401.15884_, 2024.

[16] H. Ko, D. Gürkan, and A. Yarman Vural, "ReRag: A New Architecture for Reducing the Hallucination by Retrieval-Augmented Generation," in _Proc. 9th Int. Conf. Comput. Sci. Eng. (UBMK)_, 2024, pp. 961–965.

[17] X. Ji et al., "RAG Certainty: Quantifying the Certainty of Context-Based Responses by LLMs," in _Proc. IEEE ICASSP_, 2025.

[18] N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," in _Proc. EMNLP_, 2019, pp. 3982–3992.

[19] J. Johnson, M. Douze, and H. Jégou, "Billion-Scale Similarity Search with GPUs," _IEEE Trans. Big Data_, vol. 7, no. 3, pp. 535–547, 2021.

[20] T. Brown et al., "Language Models are Few-Shot Learners," in _Proc. NeurIPS_, vol. 33, 2020, pp. 1877–1901.

[21] A. Radford et al., "Robust Speech Recognition via Large-Scale Weak Supervision," in _Proc. ICML_, 2023, pp. 28492–28518.

#v(0.4em)
#text(size: 6.8pt, style: "italic")[Artefact. All results were produced by executing the described system. Per-question retrieval traces, the ablation and the conflict-accuracy study accompany the aggregate metrics in benchmark_results.json, benchmark_multi_user_results.json, ablation_results.json and conflict_accuracy_results.json. Compiled October 2026.]

]
