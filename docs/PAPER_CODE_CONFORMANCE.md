# Paper ↔ code conformance record

Every mechanism, weight, threshold and dataset size stated in
*"Adaptive Temporal Personal Knowledge Graph with Memory Consolidation and
Contradiction-Aware Retrieval-Augmented Generation"* is listed here with the
exact location that implements it.

Use this when a reviewer, guide or examiner asks "does the code do what the
paper says?" — the answer is a line reference, not an assurance.

Audited against `main` @ `b100fcc`, 31 Oct 2026.

---

## Section IV — Proposed method

| Paper claim | Where it lives | Status |
|---|---|---|
| Eq. (1): `S = 0.30R + 0.08F + 0.22T + 0.15G + 0.15U + 0.10P − 0.18D − 0.25C` | `backend/app/research/scoring.py:34` `DEFAULT_WEIGHTS` | exact |
| Eq. (1): `M = min(1.5, max(0, S))` | `backend/app/research/scoring.py:178` | exact |
| Weights sum to 1.00 over the six positive terms | 0.30+0.08+0.22+0.15+0.15+0.10 = 1.00 | exact |
| Recency `T = 2^(−Δt/45)`, Δt in days | `backend/app/research/scoring.py:64,91` — `math.pow(0.5, age/45)`, identical to `2^(−age/45)` | exact |
| §IV-B facts are (subject, predicate, object) with `[valid_from, valid_to)`; newer value **closes** the earlier fact instead of deleting it | `backend/app/research/temporal.py` — `TemporalFact`, `superseded_by` | exact |
| §IV-B stateful predicates canonicalised via spaCy dependency parsing (learning/focusing → one state class) | `backend/app/research/temporal.py` — `STATEFUL_PREDICATES`, `PREDICATE_CANON` | exact |
| §IV-C detector uses **max contradiction probability across both text orders** | `backend/app/research/neural_nli.py:138-146` — `predict_pair(a,b)` and `predict_pair(b,a)` | exact |
| §IV-C threshold 0.55 | `backend/app/research/contradictions.py:126` | exact |
| §IV-C damping factor `1 − 0.7s` | `backend/app/research/contradictions.py:477` | exact |
| §IV-D near-duplicates by cosine over term-frequency counters | `backend/app/research/consolidation.py:45` `_cosine(Counter, Counter)` | exact |
| §IV-D retrieval dedup at 0.78 | `backend/app/research/consolidation.py:27` `DEFAULT_THRESHOLD = 0.78` | exact |
| §IV-D representative chosen by importance then length | `backend/app/research/consolidation.py:99` | exact |
| §IV-D member identifiers retained for traceability | `MemoryConsolidation` rows record member ids | exact |
| §IV-E `gap = exposure·(1−depth)·(1−0.5·connectivity)` | `backend/app/research/gaps.py:148` | exact |
| §IV-E exposure = mention count capped at 12, normalised | `backend/app/research/gaps.py:137` `min(1.0, mentions/12.0)` | exact |
| §IV-F forgetting = tombstone + text-index removal + vector deletion + graph deletion | `backend/app/research/forgetting.py:39` `forget()` | exact |
| §IV-F restoration rebuilds the text index but not vectors/graph | `backend/app/research/forgetting.py:170` `restore()` | exact |

## Section V — Experimental setup

| Paper claim | Where it lives | Verified value |
|---|---|---|
| v1 corpus: 15 memories, 11 questions, 9 answerable, spanning 240 days | `backend/app/research/bench.py` `PersonalBrainBench` | **15 / 11 / 9 / 238 days** |
| Five-persona suite: 5 personas × 11 memories × 6 queries = 30 queries, 25 answerable | `backend/app/research/multi_user_bench.py` `PERSONA_TEMPLATES` | **5 / 11 / 6 / 30 / 25** |
| Four modes: TF-IDF vector, hybrid, graph-augmented, adaptive | `backend/app/research/pipeline.py` `MODES` | present (plus an added fifth, see below) |
| Hybrid fuses TF-IDF and keyword candidates at 0.7/0.3 with a recency bonus | `backend/app/ranking/hybrid_ranker.py:5,24` | **0.7** semantic, 0.3 keyword, **0.08** recency |
| v1 duplicate rate uses term-frequency cosine at 0.90 | `backend/app/research/bench.py:443` | **0.90** |
| v2 duplicate rate uses token-set Jaccard at 0.78 | `backend/app/research/multi_user_bench.py:430` | **0.78** |
| Systems returned 45, 46, 46 and 43 items | `backend/benchmark_results.json` | **45 / 46 / 46 / 43** |

## Section VII — Implementation and verification

| Paper claim | Verified |
|---|---|
| "Twenty-nine selected research-module tests passed" | `pytest tests/test_temporal_graph.py tests/test_contradictions.py tests/test_neural_research.py` → **29 collected**; 25 pass + 4 skip in a bare sandbox (skips are the optional spaCy/ONNX paths), all 29 pass where those packs are installed |
| NLI artifact `onnx-community/distilbert-base-uncased-mnli-ONNX` | `backend/app/research/neural_nli.py:29` `DEFAULT_REPO` |
| Neural embedder present but optional (degrades to TF-IDF) | `backend/app/embeddings/embedding_model.py`; `pipeline.py` `_candidate_semantic` is wrapped in try/except |
| Retrieval compared at k = 5 | `run_bench.py` — `BENCH_K`, default 5 |

---

## Three places where the code is now ahead of the paper's wording

These are not contradictions of the architecture — they are places where the
sentence describing the mechanism is out of date. Each has a one-line fix in the
paper. None require a code revert.

### 1. Graph mode no longer sorts by node degree

`backend/app/research/pipeline.py` — graph retrieval seeds from concepts the
**query** names, walks one predicate hop, weights seeds by inverse document
frequency, and fuses with the lexical prior.

The paper (§V-A) still says *"The graph mode reorders by graph-degree boost."*
Degree-only sorting is a popularity prior that ignores the query; it is why the
paper had to report graph ≈ hybrid. With the graph now populated and
query-conditioned, that sentence should read:

> The graph mode seeds from concepts the query mentions, expands one predicate
> hop, weights seeds by inverse document frequency, and fuses the result with
> the lexical prior; adaptive adds the research-layer operations to hybrid
> retrieval rather than that graph pass.

### 2. Five-persona adaptive MRR is 0.940, not 0.920

The 0.920 in Table IV / the abstract was produced while persona cleanup left
derived state behind (the contamination the paper's limitations section
describes). With isolation fixed, adaptive ties hybrid at **0.940** and keeps
stale@1 at **0.100** versus 0.233.

Affected: abstract ("0.880, 0.940, 0.940, and 0.920"), Table IV, and §IX's
*"achieved lower accuracy than the hybrid baseline"*, which is no longer true.

### 3. The cited commit hash has moved

§VII cites `commit 7f7b679086e8`. `main` is now `b100fcc` — the commit that
contains the graph builder. Update the hash, or cite the repository without a
pinned commit.

---

## Reproducing every number in the paper

```bash
cd backend
python scripts/run_bench.py      # Tables II, III
python scripts/run_stats.py      # bootstrap CIs + leave-one-out ablation
python scripts/run_multi_user_bench.py   # Table IV
python scripts/run_ablation.py   # Table V
python scripts/run_conflict_accuracy.py  # Section IV-C precision/recall
```

Expected core-corpus table (deterministic; latency varies):

| System | Hit@5 | MRR | stale@1 | Leak | Dup. |
|---|---|---|---|---|---|
| TF-IDF vector | 1.000 | 0.833 | 0.364 | 0.022 | 0.022 |
| Hybrid | 1.000 | 0.944 | 0.182 | 0.022 | 0.022 |
| Graph-aug. | 1.000 | 0.944 | 0.182 | 0.022 | 0.022 |
| Adaptive | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |

## Conflict detection: what changed and why

| Item | Before | Now | Evidence |
| --- | --- | --- | --- |
| ONNX NLI at runtime | never loaded (`huggingface_hub` missing), silently returned "no conflict" | loads; `requirements-semantic.txt` already listed the deps | `neural_nli.is_available() == True` |
| Missing-model path | `classify_conflict` returned `(False, 0.0, "unknown")` despite logging "falling back to rule-based" | explicit conservative `_rule_conflict` (one-sided negation over near-identical claims) | `tests/test_neural_research.py` |
| Decision rule | max contradiction over both premise orders | minimum over both orders decides; max is still reported as severity | `classify_conflict(..., both_orders=True)` |
| Polarity guard | none | two restriction markers (`never` vs `only`) suppress an NLI-only conflict | holdout FP analysis |
| Value slots | calendar dates only | dates, numeric slots anchored on the counted noun, and named-entity substitution with a change cue | dev/holdout pair sets |
| Tokenisation | sentence-final punctuation kept (`"RAM."` != `"RAM"`), silently blocking pairs | punctuation stripped around tokens | `tests/test_contradictions.py` |

Resulting agreement between paper and code: Section IV-C's description of four
signals, the both-orders rule and the 0.55 threshold is now exactly what
`contradictions.py` and `neural_nli.py` do.

## Generated tables

`paper/main.tex` no longer contains any literal measurement. Tables II-VIII and
all inline numbers come from `paper/generated/*.tex`, written by
`backend/scripts/export_paper_metrics.py`. `backend/scripts/regen_paper.sh`
re-runs the experiments and the exporter in one step; `paper/README.md`
documents the mapping.
