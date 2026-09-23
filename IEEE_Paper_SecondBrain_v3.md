# An Adaptive Temporal Personal Knowledge Graph with Memory Consolidation and Contradiction-Aware Retrieval-Augmented Generation

**Dr. P S Anu Rakhi** — Assistant Professor, School of Computing, Vel Tech Rangarajan Dr. Sagunthala R&D Institute of Science and Technology, Chennai, India. anurakhips@veltech.edu.in

**Maria Immanuel L** — School of Computing, Vel Tech Rangarajan Dr. Sagunthala R&D Institute of Science and Technology, Chennai, India. vtu24334@veltech.edu.in

**Vigneshwaran S** — School of Computing, Vel Tech Rangarajan Dr. Sagunthala R&D Institute of Science and Technology, Chennai, India. vtu24372@veltech.edu.in

---

## Abstract

Retrieval-augmented generation (RAG) over a *personal* knowledge store fails differently from RAG over a static corpus. A personal store accumulates statements the user has since contradicted, facts whose validity has lapsed, near-duplicate captures of the same material, and content the user has explicitly asked to remove. Conventional retrieval treats all of it as equally current evidence, so an answer can be confidently wrong while every retrieved passage remains faithful to its source; and the recall-oriented metrics standard in RAG evaluation do not reveal it, because they saturate before the ordering errors appear. This paper addresses that gap with SecondBrain, a research layer that applies adaptive lifelong personal memory management to RAG. Its seven components are Adaptive Memory Scoring, a Temporal Personal Knowledge Graph, Contradiction-Aware Hybrid Retrieval, Memory Consolidation, Knowledge-Gap Detection, retrieval-enforced Forgetting, and PersonalBrain-Bench. The layer is additive: it annotates existing memories through separate tables and can be disabled component by component, which is what makes a controlled comparison possible. On the controlled PersonalBrain-Bench corpus of 15 synthetic memories and 11 questions (9 answerable, six question categories plus an abstention category), four retrieval pipelines are compared at k = 5 in a deterministic, CPU-only, network-free configuration. Hit@5 saturates at 1.000 for all four systems, confirming that position-insensitive recall does not separate them. On the rank-sensitive measures it does: mean reciprocal rank is 1.000 for the proposed pipeline against 0.833 (dense-only), 0.944 (hybrid) and 0.944 (graph-augmented); the rate of leading with superseded content falls from 0.364 to 0.000; and both duplicate context and post-forgetting leakage fall from 0.022 to 0.000, whereas the baselines continue to return explicitly unlearned content in the model-free configuration evaluated here. Two consecutive executions reproduce these metrics exactly. The corpus is deliberately small and synthetic, the extraction rules are conservative, and the evaluation covers retrieval rather than end-to-end generation: the results characterise behaviour on a controlled corpus, and the paper states which claims remain to be measured.

**Keywords**—personal knowledge management, retrieval-augmented generation, temporal knowledge graphs, contradiction detection, retrieval-level forgetting, memory consolidation, personal AI evaluation.

---

## I. Introduction

Retrieval-augmented generation grounds a language model in retrieved evidence rather than in parametric memory alone [1], [2]. The retrieval layer is normally evaluated on general corpora whose documents are assumed mutually consistent, immutable and equally current. A personal knowledge store violates all three assumptions. The user changes their mind, a deadline moves, the same web page is captured three times, a note is deliberately deleted. These are ordinary events in a personal corpus, and each of them produces a retrieval failure that conventional RAG evaluation is not built to see.

Consider a concrete case. In January the user records that they are learning Python; in September they record that they are now focusing on Java. Both statements are in the store, correctly, because both were true when written. A conventional retriever returns whichever is more similar to the query "what am I working on?", and if that is the January note the assistant answers confidently and wrongly. No content was fabricated — every retrieved passage is faithful to its source — so faithfulness and hallucination metrics cannot detect the failure. The error is not in the generation step but in the decision about which evidence is currently true.

The same structure appears in three further cases. Two memories can disagree without either being out of date, when a deadline is moved or an invoice superseded. Near-duplicate captures waste the context budget that determines generation quality. And a memory the user has deleted can survive in a full-text index, a vector index or a derived graph, so that "removed" content returns to the answer.

Existing work addresses adjacent problems rather than this one. RAG and Graph RAG improve how evidence is found [1]–[7]; retrieval-level verification and self-critique check generated claims against the retrieved evidence [14]–[17]. The latter is orthogonal here: when the retrieved evidence is itself outdated or mutually contradictory, verification against that evidence confirms the error rather than catching it. Machine unlearning considers removing the influence of training data from model parameters [13], which is a different problem from removing an item from a retrieval store and every index derived from it. Agent-memory research establishes that persistence and memory modules matter [10]–[12], but does not specify how a stored memory ceases to be current.

**Research gap.** Three gaps follow. (i) There is no standard evaluation that contains superseded, contradictory, duplicated and deliberately forgotten personal memories, so these failures are unmeasurable in aggregate. (ii) Temporal validity, conflict status and removal are usually recorded as metadata rather than enforced at retrieval time, although retrieval time is where the failure occurs. (iii) Because recall-oriented metrics saturate on small personal corpora, improvements to ordering and staleness can be invisible to the metrics in standard use.

This paper asks one main question and four specific ones. **Main RQ:** how should a personal memory system retrieve evidence so that a generated answer reflects what the user currently holds to be true, rather than what they once wrote? **RQ1 (temporal validity):** does enforcing validity intervals over stored facts improve rank-sensitive retrieval for state-change questions, compared with relevance-only and hybrid retrieval? **RQ2 (contradiction):** does explicit conflict detection with rank damping improve the ordering of current facts over superseded ones for contradictory evidence? **RQ3 (consolidation):** does near-duplicate consolidation with retrieval-time deduplication reduce redundant context without reducing Hit@k? **RQ4 (retrieval-enforced forgetting):** does exclusion at every derived retrieval surface eliminate post-forgetting leakage where deleting the primary row alone does not?

The corresponding hypotheses are stated so that each maps to a measurement reported in Section VI. **H1:** the proposed pipeline attains higher MRR and lower stale@1 than dense-only and hybrid retrieval on the temporal-question subset. **H2:** it attains higher MRR than dense-only retrieval on the contradiction subset. **H3:** its duplicate rate is zero while baseline duplicate rates are not, with no loss in Hit@5. **H4:** its post-forgetting leakage is zero while baseline leakage is not, in a configuration in which the unlearned row remains present in the primary store. The null hypothesis under test for Hit@5 is that the pipelines do not differ on this corpus.

The contributions are as follows. (1) A seven-component research layer for personal memory in RAG, designed to be additive to an existing capture pipeline and individually switchable. (2) An importance-scoring model whose eight terms are persisted separately and are therefore auditable. (3) A temporal triple store with validity intervals and state supersession that closes facts without deleting them, so historical and current queries are both answerable. (4) Contradiction detection combining temporal, lexical-negation and numeric value-change signals, resolved by rank damping rather than removal. (5) Consolidation with provenance preservation and a similarity threshold calibrated from measurement. (6) Forgetting enforced across five retrieval surfaces with reversible restoration. (7) PersonalBrain-Bench and an evaluation showing that rank-sensitive and staleness metrics separate the pipelines where Hit@k cannot.

Section II positions the work against existing literature. Sections III and IV describe the architecture and the seven components. Sections V and VI report the controlled evaluation. Section VII specifies the experiments that are designed but not yet run, Section VIII analyses cases in which the current rules fail, and Sections IX and X set out limitations and conclusions.

---

## II. Related Work

### A. Retrieval-Augmented Generation

RAG augments generation with retrieved context to ground responses in external evidence [1], and surveys of the area identify chunking, embedding, retrieval and generation as the stages where quality is won or lost [2]. The design assumption throughout is that the corpus documents are contemporaneous and mutually consistent with respect to the query. Our work does not replace this pipeline; it adds a temporal and conflict layer above it, and uses a graph-augmented pipeline as an explicit baseline so that the incremental effect is measured rather than assumed.

### B. Hybrid and Vector Retrieval

Dense retrieval learns a shared embedding space for queries and passages [3], while lexical scoring remains a strong and interpretable baseline [4]; fusing the two is standard practice and comparative studies characterise the vector-store substrate beneath it [5]. We adopt hybrid retrieval as a baseline and show that on a personal corpus it is the strongest of the three baselines while still returning superseded content at rank one in 18.2% of queries.

### C. Graph RAG

Graph RAG retrieves over a knowledge graph to support multi-hop questions that flat chunk retrieval cannot answer [6], [7], building on knowledge-graph representations generally [8]. Our graph component is used as a baseline and as a re-ranking signal rather than as the contribution.

### D. Temporal Knowledge Representation

Temporal knowledge graphs extend triples with a time dimension and represent facts as implicitly or explicitly time-scoped statements [9]. Our temporal store uses the same interval formulation, but applies it for a different purpose: not to predict missing links, but to decide which of several stored assertions about the user is currently true at retrieval time.

### E. LLM Agent Memory and Lifelong Personalisation

Agent research identifies memory as a core component alongside perception, planning and action [10]; systematic reviews catalogue memory sources, forms and operations for LLM agents [11]; and lifelong-learning roadmaps treat evolving knowledge as a first-class concern [12]. These contributions establish that persistence matters and how memory modules are designed. They treat disagreement between stored memories as an edge case rather than as the central problem, and they do not define an operational notion of current truth over the store.

### F. Memory Consolidation

Deduplication and near-duplicate detection are long-standing problems in information retrieval. In a personal store the cost is specific: redundant retrieved passages consume the context budget that determines generation quality. Our consolidation clusters memories by cosine similarity over term-frequency vectors, elects a canonical representative, and preserves every merged identifier so that provenance survives the merge.

### G. Machine Unlearning and Retrieval-Level Forgetting

Machine unlearning asks how to remove the influence of specific training data from a trained model [13]. The problem addressed here is different in kind, and the distinction matters for interpreting our results: this work addresses forgetting at the retrieval and derived-memory layer rather than parameter-level machine unlearning. No model weights are modified. What removal must survive is not a parametric representation but a set of derived retrieval surfaces, each of which can independently re-admit the content.

### H. Contradiction and Hallucination Handling

Work on reducing hallucination verifies generated claims against retrieved evidence through self-reflection and critique [14], corrective retrieval [15], hyperparameter tuning of the retrieval stage [16], or certainty estimation over retrieval and generation [17]. These methods improve the reliability of the generate step. They do not detect that the evidence itself is stale or self-contradictory, which is the failure mode this paper targets.

### I. Personal AI and Knowledge-Management Benchmarks

Existing RAG benchmarks evaluate retrieval and answer quality over corpora whose items are assumed valid. To our knowledge no widely used benchmark contains superseded facts, contradictions between items, deliberate removals, or a declared abstention category in combination, although establishing that absence as a fact would require a systematic benchmark review that this paper does not claim to provide. PersonalBrain-Bench is therefore proposed as an instrument for this setting rather than as a general replacement.

**TABLE I — Research Gap Comparison**

| Approach | Temp. | Conflict | Dedup. | Forget. | Personal bench. |
|---|---|---|---|---|---|
| Dense / hybrid RAG [1]–[5] | — | — | — | — | — |
| Graph RAG [6]–[8] | — | — | — | — | — |
| Temporal KG completion [9] | Yes | — | — | — | — |
| Agent memory / lifelong [10]–[12] | — | — | — | — | — |
| Machine unlearning [13] | — | — | — | Params | — |
| Self-critique / corrective RAG [14]–[17] | — | Evidence | — | — | — |
| This work | Yes | Yes | Yes | Yes | Yes |

*Columns: Temp. = temporal memory; Conflict = contradiction handling; Dedup. = consolidation or deduplication; Forget. = retrieval-level forgetting; Personal bench. = a benchmark that includes personal-memory failure categories. Cells are marked from what each cited source describes as its own contribution; a dash means the capability is not addressed by that work, not that the work is deficient. "Evidence" denotes checking generated text against retrieved evidence rather than resolving disagreement between stored memories; "Params" denotes removal from model parameters [13].*

---

## III. System Architecture

SecondBrain is a client–server personal knowledge system. A FastAPI backend exposes ingestion, retrieval and research endpoints over SQLite and an optional vector store; an Electron/React desktop shell provides capture, voice and visualisation. The research layer described here is additive: it observes and annotates existing memories through tables keyed by memory identifier, and does not modify the capture path. Each component is guarded at runtime, so the system degrades to a conventional RAG assistant if a component is unavailable or disabled, which is what makes the comparative evaluation in Section VI possible.

**Fig. 1.** Retrieval pipeline with the derived stores and the five surfaces at which forgetting is enforced.

```
                    User
                      |
        Text / voice / web / screen capture
                      |
        Normalisation + deduplication hash
                      |
        Memory store (primary table)  <----.
                      |                    |
        Adaptive Memory Scoring (C1)        |  forgetting enforced at
                      |                     |  5 surfaces:
        Temporal KG (C2) . vector store .   |    1. primary memory store
        search index                        |    2. search / full-text index
                      |                     |    3. vector store
        Contradiction Detection (C3)        |    4. knowledge graph
                      |                     |    5. derived metadata
        Memory Consolidation (C4)           |       (scores, conflicts)
                      |                     |
        Forgetting filter (C6)  ------------'
                      |
        Hybrid retrieval (dense + lexical)
                      |
        Re-ranking: validity, conflict, importance
                      |
        Local or hosted LLM  ->  answer
```

The architecture separates three layers, and the separation is what allows the paper's claims to be tested. The **application layer** captures and stores: screen OCR, mail over IMAP or OAuth, web and social ingestion, normalisation and the primary memory table. The **research layer** annotates and filters: scoring, the temporal graph, conflict detection, consolidation, gap detection and forgetting, all stored in separate tables. The **evaluation layer** is the benchmark and its harness, which drives the retrievers over a fixed corpus and writes a machine-readable artefact. No component in the research layer writes to the capture path, and the evaluation layer reads only through the public retrieval interface.

**TABLE II — Processing Stages**

| Stage | Component | Responsibility |
|---|---|---|
| 1 | Capture / ingest | Screen OCR, mail (IMAP/OAuth), web and social capture |
| 2 | Normalisation | Chunking, content hash, memory row + search index row |
| 3 | Scoring (C1) | Adaptive Memory Scoring: eight persisted terms |
| 4 | Temporal (C2) | Triple extraction, validity intervals, supersession |
| 5 | Conflict (C3) | Three conflict classes, damping policy |
| 6 | Consolidation (C4) | Near-duplicate clustering, provenance retention |
| 7 | Gaps (C5) | Exposure vs explanation depth per concept |
| 8 | Forgetting (C6) | Tombstone + exclusion at five retrieval surfaces |
| 9 | Retrieval | Four switchable pipelines (dense / hybrid / graph / adaptive) |
| 10 | Generation | Local or hosted LLM over the assembled context |

Table III states which mechanisms are adopted from prior work and which are proposed here, so that no existing technique is presented as new.

**TABLE III — Adopted Mechanisms versus Proposed Mechanisms**

| Element | Status |
|---|---|
| Dense, lexical and hybrid retrieval [3]–[5] | Adopted as baselines |
| Graph-augmented re-ranking [6]–[8] | Adopted as a baseline |
| Interval-based temporal triples [9] | Adopted representation |
| Cosine near-duplicate clustering | Adopted technique, applied to consolidation |
| Eight-term importance score with per-term persistence | Proposed |
| Predicate canonicalisation before supersession | Proposed |
| Three-class conflict detection with rank damping | Proposed combination |
| Five-surface forgetting enforcement with restoration | Proposed |
| Exposure-versus-depth gap score | Proposed |
| PersonalBrain-Bench | Proposed instrument |

---

## IV. Proposed Method

### A. Adaptive Memory Scoring (C1)

A personal store grows without bound, and a retriever that weights every memory equally cannot distinguish a clipboard fragment from the note that defines the user's project. Each memory receives an importance score composed of six positive and two negative terms:

    M = w1R + w2F + w3T + w4G + w5U + w6P − w7D − w8C        (1)

R is relevance to the user's represented interests; F recurrence across sessions; T recency under exponential decay; G graph connectivity of the memory's concepts; U explicit user confirmation; P predicted future utility; D a redundancy penalty; and C a contradiction penalty. Every component is normalised to [0, 1] before weighting, all eight are persisted alongside the total with the weights version, and no component is a learned parameter. Recency uses a half-life of 45 days, T = 2^(−Δt/45), so a memory loses half its recency contribution every 45 days without ever reaching zero. The weights in use are w = (0.30, 0.08, 0.22, 0.15, 0.15, 0.10) for R, F, T, G, U, P and (0.18, 0.25) for the subtracted D and C; the positive terms sum to 1.0. These values were set by design, not optimised: sensitivity to them is an experiment that has not been run, and is specified in Section VII.

**[REQUIRES EXPERIMENT]** Sensitivity of retrieval quality to the half-life (e.g. 15, 30, 45, 90, 180 days) and to the weight vector, including removal of individual terms.

### B. Temporal Personal Knowledge Graph (C2)

Facts are stored as (subject, predicate, object) triples carrying a validity interval [valid_from, valid_to). A null valid_to denotes a currently true fact. When an incoming stateful fact shares its (subject, predicate) with an open fact but carries a different object, the older fact is closed: valid_to is set and a superseded_by link is recorded. History therefore remains queryable, so "what am I working on?" and "what did I used to work on?" are both answerable from one store. Deletion would answer the stale-answer problem at the cost of the historical one; closing a fact preserves both capabilities.

Predicates are canonicalised into state classes before supersession is applied. Without canonicalisation, "learning Python" and "focusing on Java" are recorded under different predicates, neither supersedes the other, and the graph reports both as current. This was a real defect in our first implementation rather than a hypothetical one: the two facts the graph exists to reconcile were stored separately, and only the automated suite surfaced it.

The same mechanism is what makes the motivating Python/Java case answerable. Both memories remain in the store; the older is closed at the timestamp of the newer, and retrieval can distinguish a question about current focus (answered from the open fact) from one about history (answered from the closed interval).

### C. Contradiction-Aware Hybrid Retrieval (C3)

Three conflict classes are detected, summarised in Table IV. Temporal conflicts arise when a memory asserts a fact that a later memory superseded. Negation conflicts arise when two memories share a topic signature and one denies what the other asserts. Value-change conflicts arise when two memories share a topic signature with high salient-word overlap but carry different dated or numeric values, which is the moved-deadline case that neither a first-person pattern nor a negation word covers.

**TABLE IV — Conflict Classes and Example Pairs**

| Class | Example pair | Signal |
|---|---|---|
| Temporal | "learning Python" (Jan) vs "focusing on Java" (Sep) | Same canonical predicate, different object |
| Negation | "the review is on Friday" vs "the review is not on Friday" | Shared topic, one side negated |
| Value change | "deadline 15 October" vs "deadline 30 September" | Shared topic, differing dated value |

Resolution applies a rank multiplier rather than a deletion: an unresolved conflict of severity s damps the affected memory by (1 − 0.7s), bounded to [0.3, 1.0], so a severe conflict cannot remove a memory from consideration entirely. Final ordering is rank-preserving: the fused retrieval order supplies a prior 1/(1+i) which the multipliers adjust, with importance acting only as a light tie-breaker. Sorting by importance alone was actively harmful in development, promoting high-importance but less relevant memories above the relevant one; that negative result shaped the final design.

**[REQUIRES EXPERIMENT]** Precision, recall and F1 of conflict detection against a manually annotated conflict set. The detector is rule-based and its accuracy has not been measured; only its downstream effect on retrieval is reported in Section VI.

### D. Memory Consolidation (C4)

Memories are clustered by cosine similarity over hashed term-frequency vectors, and a canonical representative is elected by importance and then length. Every merged member identifier is retained in the consolidation record, so provenance is preserved and a merge can be inspected. A retrieval-time deduplication pass applies the same similarity test within a single query's result list, so the guarantee holds even before an offline consolidation run has executed.

The threshold is calibrated rather than assumed. In our corpus, reworded duplicates score approximately 0.82 while unrelated memories score below 0.30; the 0.90 threshold common in practice missed every reworded duplicate, so 0.78 is used. A threshold chosen by inspecting the test set would be a methodological error; this one was chosen from the measured similarity distribution and then left fixed for the benchmark. Because the corpus is small, the calibration should be repeated on a larger corpus, and the sensitivity around it is unmeasured.

**[REQUIRES EXPERIMENT]** Threshold sensitivity at 0.60, 0.65, 0.70, 0.75, 0.78, 0.80, 0.85 and 0.90, reporting merge count, false merges and duplicate rate.

### E. Knowledge-Gap Detection (C5)

Distinguishing exposure from understanding requires examining the shape of a concept's mentions rather than their count. For each concept the system computes mention frequency, whether it appears as the subject of an explanatory construction, whether it recurs across separate capture sessions, and its degree in the knowledge graph. Depth combines these, and the gap score is exposure × (1 − depth) × (1 − 0.5 · connectivity). The connectivity term is essential: without it, a well-understood but frequently mentioned concept is misreported as a gap. This is a secondary contribution, included because the failure it describes is specific to personal corpora; it is not presented as the paper's principal novelty, and its output is not evaluated as a ranking task here.

### F. Retrieval-Enforced Forgetting (C6)

Removing a row from the memory table does not remove the content from retrieval. The full-text index entry, the vector embedding, the derived graph nodes and their incident edges, and the extracted temporal facts are independent surfaces from which the content can re-enter a result set, and the derived scores and conflict rows are two more pieces of state that reference it. The forgetting service therefore tombstones the memory and enforces exclusion at five surfaces: the search-index entry is deleted, the vector is removed from the store, graph nodes and their incident edges are deleted, temporal facts are closed and detached from their source, and derived scores and conflict rows are purged. Restoration re-indexes and re-admits the memory, so the operation is reversible. Fig. 1 marks where this applies in the pipeline.

As stated in Section II, this is retrieval-level forgetting, not parameter-level machine unlearning [13]: no model weight is modified, and a model that has already memorised the content in a previous session is out of scope.

### G. PersonalBrain-Bench (C7)

Existing RAG benchmarks do not contain contradictory, superseded or deliberately forgotten personal memories, so they cannot expose the failures this paper targets. PersonalBrain-Bench is a synthetic personal corpus with a graded question set. Synthetic construction is deliberate: a real personal store would make the experiment unreproducible and would place private data in a publication. The corpus and question set are described in Section V-A.

---

## V. Experimental Setup

### A. Corpus and Question Set

PersonalBrain-Bench contains 15 memories spanning email, notes, code, web captures and screen text, with creation timestamps distributed across a 240-day window so that recency and supersession are exercised rather than simulated. The corpus embeds a superseded state pair (learning Python, then focusing on Java), a moved deadline (15 October to 30 September), a three-member near-duplicate cluster, a multi-hop chain linking a project to a dataset and a model, a sensitive scratch note that is then explicitly forgotten, and a concept mentioned repeatedly without explanation. Ingestion detects 2 conflicts, both of the value-change class, and one memory is forgotten for the removal evaluation. Of the 11 questions, 9 are answerable; the two remaining questions test abstention and removal respectively and have no gold memory by construction. Table V lists the categories.

**TABLE V — Question Categories in PersonalBrain-Bench**

| Category | n | Answerable | What it tests |
|---|---|---|---|
| Factual recall | 3 | Yes | Retrieval of an unambiguous stored fact |
| Temporal state | 2 | Yes | Current value preferred over superseded |
| Contradiction | 2 | Yes | Current side of a changed deadline |
| Multi-hop | 1 | Yes | Synthesis across linked memories |
| Duplicate | 1 | Yes | No redundant context in the result set |
| Abstention (gap) | 1 | No | Unanswerable question not answered |
| Removal | 1 | No | Forgotten content not returned |

### B. Systems Compared

**Vanilla** is dense-only retrieval. **Hybrid** fuses dense and lexical results. **Graph** adds knowledge-graph connectivity re-ranking. **Adaptive** is the proposed pipeline: hybrid plus forgetting exclusion, temporal validity damping, contradiction damping, importance weighting and consolidation-based deduplication. All four share identical candidate generation and differ only in the post-retrieval layer, so measured differences are attributable to that layer rather than to the retriever.

### C. Metrics

Hit@k and MRR are computed over answerable questions only; including abstention and removal questions, which have no gold memory by construction, would depress every system equally and conceal differences. Three further metrics are reported. **stale@1** is the fraction of queries whose top-ranked result is superseded or forbidden, because rank one is what a generator leads with. **Forgotten-leak rate** is the fraction of returned results that were explicitly unlearned. **Duplicate rate** is the fraction of within-query result pairs at or above the consolidation threshold. All are fractions of returned results or of questions, and lower is better for all three.

### D. Reproducibility and Configuration

The evaluation is reported for a single recorded configuration (dense backend "tfidf", scoring weights version "v1", k = 5, corpus-scoped evaluation). Three properties are worth stating explicitly, because each was a source of irreproducibility that had to be removed. First, the dense retriever is pinned to the model-free TF-IDF path for the benchmark: with a neural embedder installed the leak and staleness figures differ, so a result table without the backend stated is not reproducible. The shipped pipeline still selects a neural embedder automatically when one is installed; only the evaluation is pinned. Second, every stage — retrieval, scoring, conflict detection, temporal supersession, gap statistics and keyword search — is evaluated within the corpus scope, so the presence of unrelated memories in the database cannot move the numbers. Third, two consecutive full executions reproduce the figures exactly, with no network access and no GPU. All results are produced by one script and written to a machine-readable artefact that records the configuration and the environment.

The retrieval layer and each of the seven components are exercised by an automated suite of 77 assertions that runs offline: scoring component behaviour and range, temporal extraction and supersession semantics, contradiction detection and penalty application, consolidation threshold and provenance retention, gap scoring and depth suppression, forgetting leakage across all four retrieval modes, benchmark comparability, and the API surface including authentication and error codes. Surrounding the research layer, a further 14 verification steps cover the application: six backend suites (213 assertions), three in-process rendering harnesses for the UI, static analysis, an import and API-contract check, a production build, and an endpoint sweep that boots the server and probes every registered GET route for server errors.

---

## VI. Results

Table VI reports retrieval quality and Table VII the staleness, leakage and duplication metrics. Every number is read from the artefact produced by the run described in Section V-D.

**TABLE VI — Retrieval Quality Across Four Pipelines**

| System | Hit@5 | MRR |
|---|---|---|
| Vanilla dense | 1.000 | 0.833 |
| Hybrid | 1.000 | 0.944 |
| Graph-augmented | 1.000 | 0.944 |
| Adaptive (proposed) | 1.000 | 1.000 |

*k = 5; metrics over the 9 answerable questions.*

**TABLE VII — Staleness, Leakage and Duplication**

| System | stale@1 | Leak | Duplicate |
|---|---|---|---|
| Vanilla dense | 0.364 | 0.022 | 0.022 |
| Hybrid | 0.182 | 0.022 | 0.022 |
| Graph-augmented | 0.182 | 0.022 | 0.022 |
| Adaptive (proposed) | 0.000 | 0.000 | 0.000 |

*stale@1 = top-ranked result superseded or forbidden. Leak = returned results that were explicitly forgotten. Duplicate = within-query result pairs at or above the consolidation threshold. Lower is better; the proposed system reaches zero on all three.*

**[REQUIRES EXPERIMENT]** stale@1, leak and duplicate are proportions over few questions and results (11 questions; 45 returned results per system at k = 5). They are reported as counts as well as rates wherever a test is run, and neither confidence intervals nor significance tests are claimed for them here; the protocol that would be used is specified in Section VII-F.

**Hit@5 does not discriminate.** All four systems reach 1.000: every pipeline finds the relevant memory somewhere in its top five, so the null hypothesis of no difference on this metric is not rejected. A study reporting only recall would conclude that the research layer adds nothing. The answers the pipelines support nevertheless differ, because a generator consumes the ordered context rather than the set. On rank-sensitive measures the pipelines separate: MRR rises from 0.833 (vanilla) through 0.944 (hybrid, equal to graph-augmented) to 1.000 for the adaptive pipeline, a relative improvement of 5.9% over the strongest baseline and 20.0% over dense-only retrieval. H1 and H2 are supported on this corpus at the level of the subset results in Table VIII.

**Staleness is where the effect is largest.** Dense-only retrieval leads with superseded content in 36.4% of queries; hybrid and graph reduce this to 18.2%, and the adaptive pipeline reduces it to 0.0%. In counts, the strongest baseline leads with outdated content on 2 of 11 questions and the proposed pipeline on none. Because each retrieved passage remains faithful to its source, no faithfulness metric would flag those cases; this is the failure mode that motivated the work.

**Leakage and duplication are eliminated.** Forgotten-content leakage falls from 0.022 to 0.000 and duplicate context from 0.022 to 0.000. The leakage result also carries the negative case: in this configuration the baselines continue to return explicitly unlearned content, which is direct evidence that removal is a property of the retrieval layer rather than something obtained by deleting a row from the primary table. H3 and H4 are supported in this configuration. Because the effect depends on which dense backend is installed, the configuration is part of the claim, not a detail of the setup.

**TABLE VIII — Mean Reciprocal Rank by Question Category**

| Category | n | Van. | Hyb. | Adapt. | Δ (vs van.) |
|---|---|---|---|---|---|
| factual | 3 | 1.000 | 1.000 | 1.000 | +0.000 |
| temporal | 2 | 0.750 | 0.750 | 1.000 | +0.250 |
| contradiction | 2 | 0.500 | 1.000 | 1.000 | +0.000 |
| multi-hop | 1 | 1.000 | 1.000 | 1.000 | +0.000 |
| duplicate | 1 | 1.000 | 1.000 | 1.000 | +0.000 |

*Answerable categories only; the abstention and removal questions have no gold memory. Δ is the proposed pipeline minus dense-only retrieval. The per-category figures rest on one to five questions each: they localise where the effect appears, and are directional rather than conclusive until the benchmark is enlarged (Section VII).*

Gains concentrate where the architecture predicts them. Temporal questions improve from 0.750 to 1.000 once predicate canonicalisation makes supersession fire, and contradiction questions from 0.500 to 1.000: presented with two dated statements about the same deadline, dense retrieval has no mechanism to prefer the later one, while validity damping and value-change detection both promote it. Factual, multi-hop and duplicate questions are unchanged, which is the intended signature of a component that changes ordering rather than recall.

**TABLE IX — Latency on the Benchmark Corpus**

| System | Total ms (11 queries) | Relative |
|---|---|---|
| Vanilla dense | 37 | 1.28× |
| Hybrid | 29 | 1.00× |
| Graph-augmented | 39 | 1.34× |
| Adaptive (proposed) | 76 | 2.62× |

*The adaptive pipeline costs approximately 2.6× the hybrid baseline on a corpus of 15 memories, an overhead dominated by conflict and temporal lookups. At personal-corpus scale this is small against generation latency, but the cost is real and is stated as measured. Wall-clock on the development machine; latency is not comparable across machines and does not vary with corpus size in a way this experiment establishes.*

---

## VII. Planned Evaluations

This section specifies the experiments that the current results do not cover. Each item is marked **[REQUIRES EXPERIMENT]** because no result is reported for it. They are included because the limitations in Section IX are only credible alongside a concrete plan to remove them.

### A. Component-Wise Ablation

The current comparison holds the whole post-retrieval layer against three baselines; it does not isolate which of the five stages produces the effect. The per-category results in Table VIII localise it, but a factorised ablation is the direct test. The design is cumulative, adding one stage at a time so that each row differs from the one above by a single mechanism, measured on the same corpus and question set with the same candidate generation.

**TABLE X — Ablation Design**

| Configuration | Temporal | Conflict | Consol. | Forget | Importance |
|---|---|---|---|---|---|
| Baseline (hybrid) | — | — | — | — | — |
| + Temporal validity | Yes | — | — | — | — |
| + Contradiction damping | Yes | Yes | — | — | — |
| + Consolidation | Yes | Yes | Yes | — | — |
| + Forgetting | Yes | Yes | Yes | Yes | — |
| Full adaptive | Yes | Yes | Yes | Yes | Yes |

*Metrics per row: Hit@5, MRR, stale@1, forgotten-leak rate, duplicate rate and latency. **[REQUIRES EXPERIMENT]** No row of this table has been run.*

### B. End-to-End Generation Evaluation

The present evaluation stops at retrieval. Whether lower stale@1 and higher MRR produce correct generated answers is not measured here, and it is the most important open question: retrieval metrics are proxies. The proposed design generates answers with the same local model for all four systems, over identical prompts and identical ordered context, and scores them on answer correctness, temporal correctness, contradiction resolution, evidence correctness, forgotten-information leakage in the generated text, and abstention correctness. Scoring would be done by two independent human raters on the full question set with a stated disagreement-resolution rule, since automatic judges introduce their own failure modes. **[REQUIRES EXPERIMENT]**

### C. Threshold and Parameter Sensitivity

The consolidation threshold (0.60–0.90, focused on 0.78), the recency half-life (15–180 days) and the eight scoring weights each have an unmeasured sensitivity. The weight study would report the effect of zeroing one term at a time, which also tests whether the eight-term score is justified over a simpler alternative. **[REQUIRES EXPERIMENT]**

### D. Conflict-Detection Accuracy

The three-class detector is rule-based and its precision and recall are unmeasured. The study requires a manually annotated set of memory pairs labelled by conflict class and by whether the conflict is genuine, reporting per-class precision, recall and F1 with the confusion matrix. Negation detection is expected to be the weakest, since it previously produced false positives by substring matching. **[REQUIRES EXPERIMENT]**

### E. Scalability

Latency is currently reported for one corpus of 15 memories, which cannot show how the per-run conflict and temporal lookups grow. A scalability study would measure the same metrics at corpus sizes of 15, 50, 100, 500, 1,000 and 5,000 memories, reporting both retrieval latency and the offline cost of scoring, conflict detection and consolidation, and would state whether the pipeline stays within an interactive budget. **[REQUIRES EXPERIMENT]**

### F. Statistical Protocol

Once the benchmark is enlarged, each system would be run over multiple independently generated corpora with the same question templates, and results reported as mean ± standard deviation with 95% bootstrap confidence intervals over resampled questions. Paired comparisons between systems would use a paired test over the shared question set (Wilcoxon signed-rank for per-question rank statistics, McNemar's test for per-question hit and stale outcomes), with the number of questions stated. The present paper reports point estimates only and makes no significance claim. **[REQUIRES EXPERIMENT]**

---

## VIII. Failure-Case Analysis

The mechanisms above are rule-based and pattern-driven, and they fail in predictable ways. Table XI lists the cases we expect to fail, with the reason. These are design limitations rather than undiscovered defects: none of them is solved by the current system, and none is claimed to be.

**TABLE XI — Anticipated Failure Cases**

| Case | Why the current rules miss it |
|---|---|
| Contradiction phrased without shared vocabulary | Conflict detection requires a shared topic signature or canonical predicate |
| Missing or wrong timestamp | Supersession orders by recorded time; a wrong timestamp inverts the ordering |
| Ambiguous temporal expression ("next month", "soon") | Extraction expects an absolute date or a recognised pattern |
| Future plan later abandoned silently | No retraction is recorded, so the fact stays open and is reported as current |
| Implicit state change with no supersession cue | A new state must share a canonical predicate to close the previous one |
| Memory relevant only in combination with another | Ranking scores memories individually; joint relevance is not modelled |
| Forgotten content reproduced verbatim in an unrelated memory | Removal applies to the forgotten item, not to copies of its text elsewhere |

The last row is the sharpest: retrieval-level forgetting removes the item and its derived state, but a user who pasted the same credential into a second note has created a second memory that the tombstone does not cover. Detection of duplicated sensitive content across memories is not attempted here.

---

## IX. Discussion and Limitations

**Saturation of a convenient metric is not evidence of equivalence.** Our results show a system that is identical to its baselines on recall and materially different on the metric that determines whether the user is misinformed. This is a caution about evaluation practice for personal AI, and it is the reason the paper reports stale@1 and leakage alongside Hit@k.

**Damping rather than deleting** is a deliberate design decision. Removing superseded memories would attain the same stale@1 result while making the assistant unable to answer historical questions. Both capabilities are legitimate: validity intervals close facts without erasing them, and rank multipliers demote rather than remove. Whether damping is preferable to removal is a question for a user study, not for this corpus.

**Forgetting is a cross-cutting property.** The baseline leakage result shows that deletion at one surface is insufficient; any system that promises removal while retaining a derived index or a duplicate copy elsewhere has a removal hole. This holds independently of the machine-learning sense of unlearning, and the two should not be conflated.

The limitations are material and are stated in full.

- PersonalBrain-Bench is small and synthetic. Fifteen memories and eleven questions isolate specific behaviours rather than represent the distribution of real personal data; per-category figures rest on one to five questions, so absolute values should not be extrapolated and per-category deltas should be treated as directional.
- The evaluation covers retrieval, not end-to-end generation quality. Whether the ranking improvements produce fewer incorrect answers in generated prose is not measured here; the design that would measure it is given in Section VII-B.
- No component-wise ablation has been run. The aggregate comparison and the per-category results are consistent with the intended mechanism, but they do not isolate it; the factorised design is given in Section VII-A.
- Extraction is rule-based and conservative, trading recall for precision. It will miss contradictions that do not match its patterns, as set out in Section VIII.
- Temporal handling uses UTC-normalised timestamps without full timezone or partial-interval reasoning, which would matter for events spanning midnight across zones.
- Scalability is not established. Latency is reported for a single small corpus, so the cost of conflict and temporal lookups at larger corpus sizes is unknown.
- Conclusions about forgetting depend on the configured dense backend, because a vector store allows deletion of the embedding itself. The evaluation states and pins its configuration for that reason.

---

## X. Conclusion and Future Work

Personal knowledge stores violate the consistency assumptions of general retrieval benchmarks, and the resulting failures are invisible to recall-oriented metrics. This paper addressed the question of how a personal memory system should retrieve evidence so that generated answers reflect what the user currently holds to be true, and proposed a seven-component research layer for that problem: auditable importance scoring, a temporal knowledge graph with validity intervals and supersession, contradiction-aware retrieval across three conflict classes, consolidation with provenance preservation, exposure-versus-depth gap detection, forgetting enforced at five retrieval surfaces, and PersonalBrain-Bench as an instrument for the setting.

On the controlled PersonalBrain-Bench corpus, the evaluation indicates that Hit@5 saturates for all four pipelines while rank-sensitive and staleness metrics separate them: MRR 0.833 → 1.000, stale@1 0.364 → 0.000, and both post-forgetting leakage and duplicate context from 0.022 to 0.000, with the baselines continuing to return explicitly unlearned content in the configuration evaluated. These are results about a small synthetic corpus in a model-free configuration; they demonstrate behaviour on that corpus and are not evidence of general superiority.

What remains unresolved is therefore explicit. Component-wise attribution, end-to-end generation quality, conflict-detection accuracy, parameter and threshold sensitivity, scalability, and behaviour on real de-identified personal corpora are all unmeasured here, and Section VII specifies the experiments that would measure them. Future work proceeds along those lines, together with a learned rather than fixed weighting of the scoring terms and an LLM-assisted extractor retained behind the high-precision rule-based trigger.

---

## Acknowledgment

The authors thank the School of Computing, Vel Tech Rangarajan Dr. Sagunthala R&D Institute of Science and Technology, for institutional support, and acknowledge the open-source projects on which the system is built, in particular FastAPI, SQLAlchemy and sentence-transformers.

---

## References

[1] P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," in *Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 33, 2020, pp. 9459–9474.

[2] Y. Gao et al., "Retrieval-Augmented Generation for Large Language Models: A Survey," arXiv:2312.10997, 2023.

[3] V. Karpukhin et al., "Dense Passage Retrieval for Open-Domain Question Answering," in *Proc. Conf. Empirical Methods Natural Lang. Process. (EMNLP)*, 2020, pp. 6769–6781.

[4] S. Robertson and H. Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond," *Found. Trends Inf. Retr.*, vol. 3, no. 4, pp. 333–389, 2009.

[5] N. Bruch, S. Nedelkoski, and S. Mandal, "A Deep Dive into Vector Stores: Classifying the Backbone of Retrieval-Augmented Generation," in *Proc. IEEE Int. Conf. Big Data*, 2024.

[6] D. Edge et al., "From Local to Global: A Graph RAG Approach to Query-Focused Summarization," arXiv:2404.16130, 2024.

[7] Z. Peng et al., "Graph Retrieval-Augmented Generation: A Survey," arXiv:2408.08921, 2024.

[8] A. Hogan et al., "Knowledge Graphs," *ACM Comput. Surv.*, vol. 54, no. 4, 2021.

[9] B. Cai, Y. Xiang, L. Gao, H. Zhang, Y. Li, and J. Li, "Temporal Knowledge Graph Completion: A Survey," in *Proc. 32nd Int. Joint Conf. Artif. Intell. (IJCAI)*, 2023, pp. 6545–6553.

[10] L. Wang et al., "A Survey on Large Language Model based Autonomous Agents," *Frontiers Comput. Sci.*, vol. 18, no. 6, p. 186345, 2024.

[11] Z. Zhang et al., "A Survey on the Memory Mechanism of Large Language Model based Agents," arXiv:2404.13501, 2024.

[12] J. Zheng et al., "Lifelong Learning of Large Language Model based Agents: A Roadmap," *IEEE Trans. Pattern Anal. Mach. Intell.*, 2026 (early access).

[13] L. Bourtoule et al., "Machine Unlearning," in *Proc. IEEE Symp. Security and Privacy (S&P)*, 2021, pp. 141–159.

[14] A. Asai, Z. Wu, Y. Wang, A. Sil, and H. Hajishirzi, "Self-RAG: Learning to Retrieve, Generate and Critique through Self-Reflection," in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2024.

[15] S. Yan et al., "Corrective Retrieval Augmented Generation," arXiv:2401.15884, 2024.

[16] R. Ko, M. K. Gürkan, and F. T. Yarman Vural, "ReRag: A New Architecture for Reducing the Hallucination by Retrieval-Augmented Generation," in *Proc. 9th Int. Conf. Comput. Sci. Eng. (UBMK)*, 2024, pp. 961–965.

[17] X. Ji et al., "RAG Certainty: Quantifying the Certainty of Context-Based Responses by LLMs," in *Proc. IEEE Int. Conf. Acoust., Speech Signal Process. (ICASSP)*, 2025.

[18] N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," in *Proc. EMNLP*, 2019, pp. 3982–3992.

[19] J. Johnson, M. Douze, and H. Jégou, "Billion-Scale Similarity Search with GPUs," *IEEE Trans. Big Data*, vol. 7, no. 3, pp. 535–547, 2021.

[20] T. Brown et al., "Language Models are Few-Shot Learners," in *Proc. NeurIPS*, vol. 33, 2020, pp. 1877–1901.

[21] A. Radford et al., "Robust Speech Recognition via Large-Scale Weak Supervision," in *Proc. Int. Conf. Mach. Learn. (ICML)*, 2023, pp. 28492–28518.

---

*Artefact.* All results were produced by executing the described system. The run configuration and environment are recorded in `benchmark_results.json`; per-question retrieval traces accompany the aggregate metrics.
