"""
Review, required-changes checklist, experimental plan and novelty statement.
===========================================================================
Generated from the reviewer/editor pass over "Ieee Paper draft 1 (1).pdf".
Every factual assertion about the draft was checked against the draft text
itself; every assertion about the system's behaviour was checked by running the
code in this repository. Where a number in the draft could not be reproduced,
the discrepancy is stated with the measurement that shows it.

Usage:  python generate_review_report.py
Output: PAPER_REVIEW_AND_EXPERIMENT_PLAN.pdf
"""
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Frame, PageBreak, PageTemplate, Paragraph, Spacer

from report_builder_base import (
    B, P, Report, Section, Sub, callout, table,
)

OUT = "PAPER_REVIEW_AND_EXPERIMENT_PLAN.pdf"

# Widths for the review document's body frame (A4 at 62 pt margins = 471 pt).
W = 471


def main():
    story = []

    # =====================================================================
    # COVER
    # =====================================================================
    story.append(Section("Reviewer Report and Revision Plan"))
    story.append(Sub("An Adaptive Temporal Personal Knowledge Graph with Memory "
                     "Consolidation and Contradiction-Aware Retrieval-Augmented Generation"))
    story.append(P(
        "Manuscript: draft 1, 5 pages, 25 references. Authors: Dr. P S Anu Rakhi, "
        "Maria Immanuel L, Vigneshwaran S (Vel Tech Rangarajan Dr. Sagunthala R&D "
        "Institute of Science and Technology)."))
    story.append(P(
        "Review scope: research problem and framing, novelty positioning, methodology, "
        "experimental design, statistical validity, claim-evidence alignment, reference "
        "verification against the published record, and IEEE presentation."))

    story.extend(callout(
        "How to read this document",
        "Stage 1 is the critical review. Stage 2 is the prioritised checklist. The corrected "
        "paper itself is a separate artefact (IEEE_Conference_Paper_SecondBrain_v3.pdf) so it "
        "can be submitted directly. Stage 4 is the experimental plan that removes each "
        "[REQUIRES EXPERIMENT] marker. Stage 5 is the defensible novelty statement. "
        "Appendix A is the reference audit, which contains the single most urgent correction "
        "in this review."))

    # =====================================================================
    # STAGE 1
    # =====================================================================
    story.append(PageBreak())
    story.append(Section("Stage 1 - Critical Review"))

    story.append(Sub("1.1 What the draft does well"))
    story.append(P(
        "The draft has a real argument, and it is the right one for this system. It does not "
        "present the implementation as the contribution; it identifies a failure mode "
        "(retrieval treats outdated and contradictory personal memories as equally current "
        "evidence), shows why existing metrics cannot see it (faithfulness is preserved "
        "because nothing is fabricated), and reports a metric that can "
        "(stale@1). That framing is stronger than most student drafts, which present a "
        "system tour and append a screenshot."))
    story.append(P(
        "Three further strengths are worth protecting through revision. First, the "
        "architecture is described as <i>additive</i> and every component is switchable, "
        "which is exactly what makes a controlled comparison possible; the draft states "
        "this and uses it. Second, the limitations section is already honest: it names the "
        "synthetic corpus, the rule-based extraction, the missing end-to-end generation "
        "evaluation and the absent ablation. Third, the negative result is reported rather "
        "than hidden - Hit@5 saturates at 1.000 for all four systems, and the draft says so "
        "instead of leading with a flattering metric."))

    story.append(Sub("1.2 Critical weaknesses"))
    story.append(P(
        "The weaknesses below are ordered by how much they threaten acceptance. W1 to W3 are "
        "blocking; W4 to W7 materially weaken the paper; W8 onwards are presentational but "
        "still worth fixing before submission."))

    story.extend(table([
        ["ID", "Weakness", "Why it matters"],
        ["W1", "Two reported figures are not reproducible from the code. The draft states "
               "\u201cIngestion produced 4 detected conflicts\u201d and gives baseline "
               "stale@1 = 0.091. Re-running the described system produces 2 conflicts and "
               "stale@1 = 0.182 (Table 1.1 below).",
               "This is the one finding that must be fixed before anything else. A reviewer "
               "who re-runs the artefact and gets different numbers will distrust every "
               "other number in the paper."],
        ["W2", "Several references do not match the published record: one has the wrong "
               "venue, year and truncated author names; one has a mangled surname initial; "
               "several carry future years; at least one could not be located at all. See "
               "Appendix A.",
               "Incorrect citations are unambiguous, cheap to check, and read as carelessness "
               "or as padding. Some of the uncited references in the current list are also "
               "irrelevant to the argument."],
        ["W3", "The contribution is presented as seven co-equal components with no "
               "statement of which is the paper's actual claim, and no table separating "
               "adopted techniques from proposed ones.",
               "As written, a reviewer can reasonably read the paper as claiming novelty for "
               "RAG, hybrid retrieval, knowledge graphs, consolidation and unlearning "
               "individually - none of which is novel. The draft is vulnerable on exactly "
               "the point where it is actually defensible."],
        ["W4", "No research questions and no hypotheses are stated. The evaluation measures "
               "things, but nothing is being tested.",
               "Without stated hypotheses, the results cannot be said to confirm or refute "
               "anything, and the per-category table has no stated prediction to match."],
        ["W5", "The evaluation is retrieval-only, and the paper's central claim is about "
               "answers.",
               "The draft acknowledges this in one limitation sentence, but the gap is "
               "large: a reviewer will ask how a 5.9% MRR improvement changes what the user "
               "reads. This needs a designed experiment, not only an admission."],
        ["W6", "No ablation. Five post-retrieval mechanisms are bundled and compared "
               "against three baselines; which mechanism produces the effect is unknown.",
               "The per-category table is suggestive but cannot substitute for a "
               "component-wise design. Reviewers of systems papers treat the ablation as "
               "mandatory."],
        ["W7", "Statistical treatment is absent. Rates such as stale@1 and duplicate rate "
               "are reported as if exact, from 11 questions and 45 returned results per "
               "system.",
               "Some of the reported differences are a single question changing rank. The "
               "paper should report counts, and once the benchmark grows, confidence "
               "intervals and a paired test."],
        ["W8", "The phrase \u201cmachine unlearning\u201d is used for a retrieval-store "
               "operation, and \u201challucination-free\u201d is used as a description of "
               "the system.",
               "Unlearning has a specific meaning in the literature (removing the influence "
               "of training data from parameters). Equating the two invites a rejection on "
               "terminology. \u201cHallucination-free\u201d is an absolute claim no "
               "retrieval-layer result can support."],
        ["W9", "Structure and numbering are inconsistent: Section V is interleaved "
               "out of order in the typeset output (V-B and V-C appear after VI-A), "
               "and Table III is followed by a caption that does not match its content.",
               "Typesetting defects of this kind are read as evidence that the paper was "
               "not proofread, which undermines confidence in the measurements."],
        ["W10", "Related work is organised by topic but contains no comparison table and no "
                "explicit gap statement, and it omits temporal knowledge representation "
                "and memory-consolidation literature entirely.",
                "\u201cExisting work is orthogonal\u201d is asserted rather than shown. A "
                "gap table forces the claim to be explicit and checkable."],
    ], [22, 224, W - 246]))

    story.append(P(
        "<b>Table 1.1 - Reproducibility check.</b> Each draft figure was re-measured by "
        "running the code, with the pre-fix research modules restored (commit 38d9b20) as "
        "well as with the current ones."))
    story.extend(table([
        ["Quantity in draft", "Draft value", "Measured (pre-fix)", "Measured (current)",
         "Verdict"],
        ["Conflicts detected at ingestion", "4", "2", "2",
         "Not reproducible"],
        ["Hybrid stale@1", "0.091", "0.182", "0.182", "Not reproducible"],
        ["Graph stale@1", "0.091", "0.182", "0.182", "Not reproducible"],
        ["Vanilla stale@1", "0.364", "0.364", "0.364", "Reproduces"],
        ["MRR (vanilla / hybrid / adaptive)", "0.833 / 0.944 / 1.000",
         "0.833 / 0.944 / 1.000", "0.833 / 0.944 / 1.000", "Reproduces"],
        ["Leak and duplicate rates", "0.022 \u2192 0.000", "same", "same", "Reproduces"],
        ["Adaptive latency", "80 ms", "76 ms", "76 ms",
         "Wall-clock; varies per run and per machine"],
    ], [126, 74, 82, 82, W - 364]))
    story.append(P(
        "The two irreproducible values share a cause. Both came from a run whose database "
        "held state beyond the benchmark corpus: conflict rows and consolidation state "
        "belonging to other memories changed the counts, and retrieval was not scoped to "
        "the corpus, so an unrelated memory could take a top-5 slot and move stale@1. The "
        "corrected pipeline evaluates the corpus against itself and pins the dense backend, "
        "which is why the current numbers are stable across runs. The paper must therefore "
        "report the re-measured values, and should state the configuration explicitly, "
        "because the effect being measured depends on it."))

    story.append(Sub("1.3 Unsupported or overreaching statements in the draft"))
    story.extend(table([
        ["Location", "Statement", "Problem", "Replacement"],
        ["Abstract", "\u201cwhereas every baseline continues to return explicitly unlearned "
                      "content\u201d",
         "True only in the model-free configuration. With a vector store the embedding is "
         "deleted and no mode can return the content. As written it reads as a general "
         "property.",
         "State the configuration inside the claim."],
        ["Abstract / Intro", "Counts \u201cseven components\u201d then \u201cthree "
                             "claims\u201d without connecting them",
         "A reviewer cannot tell what is claimed to be new.",
         "Add the adopted-vs-proposed table (now Table III) and state the contribution as "
         "coordinated integration plus the specific mechanisms."],
        ["Section I", "\u201cthe system is hallucination-free and still incorrect\u201d",
         "Absolute claim about generation, and no generation evaluation was run.",
         "\u201cevery retrieved passage is faithful to its source, so a faithfulness metric "
         "cannot flag the error\u201d."],
        ["Section II-D", "\u201cMachine Unlearning\u201d as the heading for retrieval-store "
                         "removal",
         "Conflates two different problems [Bourtoule et al. define unlearning over model "
         "parameters].",
         "Rename to retrieval-level forgetting, and state the distinction explicitly."],
        ["Section IV-D", "\u201cthe 0.90 threshold commonly recommended in practice missed "
                         "every reworded duplicate\u201d",
         "No source is given for the recommendation, and \u201cin practice\u201d is "
         "unattributed.",
         "Either cite a source or rewrite as the observation it is: our corpus's reworded "
         "duplicates scored \u2248 0.82, so a 0.90 cutoff would merge nothing."],
        ["Section VI", "\u201cThe proposed system therefore never leads with an outdated "
                       "fact on this corpus\u201d",
         "Defensible as written (it says <i>on this corpus</i>), but the following sentence "
         "\u201croughly one query in eleven\u201d understates the measured value.",
         "Use the re-measured rate and its count: 2 of 11 questions."],
        ["Section VII", "\u201cthe paper's claims are each mapped to at least one executable "
                        "check\u201d",
         "True for the implementation, but the 68 assertions do not test any of the "
         "hypotheses; they test component behaviour.",
         "Say that the suite tests component behaviour; the benchmark tests the hypotheses."],
    ], [68, 116, 148, W - 332]))

    story.append(Sub("1.4 Novelty risks"))
    story.append(P(
        "There are three places where a reviewer could reject the paper for novelty, and one "
        "place where the paper is too modest."))
    story.extend(B([
        "<b>Risk 1 - \u201cthis is engineering, not research.\u201d</b> The draft's own first "
        "contribution is \u201ca seven-component personal memory architecture\u201d. Assembly "
        "of known parts is not a research contribution. The fix is not to inflate the "
        "components but to move the claim: the contribution is the <i>evaluation of a "
        "neglected failure mode</i> together with a benchmark that exposes it and an "
        "architecture whose switches let that failure be isolated. The paper's own finding "
        "- that the standard metric is saturated and therefore uninformative - is the "
        "interesting part and should be foregrounded.",
        "<b>Risk 2 - overlapping with agent-memory work.</b> Lifelong-learning and "
        "agent-memory roadmaps already treat evolving knowledge as a first-class concern. "
        "The paper must cite that literature (it currently does not) and state precisely "
        "what is added: an operational definition of <i>current</i> truth over the store, "
        "enforced at retrieval time, with the derived-surface problem made explicit.",
        "<b>Risk 3 - \u201ctemporal knowledge graphs are established.\u201d</b> Correct, and "
        "the draft should say so. What is not established is using interval validity to "
        "decide between competing personal assertions at retrieval time, and measuring the "
        "effect with stale@1.",
        "<b>Being too modest.</b> The leakage result - that deletion at one surface is "
        "insufficient, demonstrated with the baselines still returning removed content - is "
        "a genuinely useful negative finding for personal AI, and the draft buries it in a "
        "limitations bullet. It belongs in the contributions.",
    ]))

    story.append(Sub("1.5 Methodology risks"))
    story.extend(B([
        "<b>Corpus size.</b> 15 memories and 11 questions give per-category figures based on "
        "one to five questions. The draft's per-category table (its Table IV) therefore "
        "reports MRR deltas that a single question's rank change can produce. The paper "
        "should say this explicitly and treat the per-category deltas as directional.",
        "<b>Threshold and weight selection.</b> The consolidation threshold (0.78) was "
        "calibrated on the same corpus used for evaluation. The draft argues the threshold "
        "was chosen from the measured distribution rather than by inspecting the test set, "
        "which is the right instinct, but on a 15-memory corpus the two are hard to "
        "separate. State it as a limitation and repeat the calibration on a larger corpus.",
        "<b>Single-run reporting.</b> The draft reports one execution. Reproducibility is "
        "claimed on the basis that two consecutive runs agree, which is necessary but not "
        "sufficient: determinism of one configuration is not robustness across corpora.",
        "<b>Backend dependence.</b> The direction of the leakage result depends on whether a "
        "vector store is present, because a deleted embedding cannot be returned. This is "
        "not a flaw, but it must be stated in the claim itself rather than in a footnote.",
    ]))

    story.append(Sub("1.6 IEEE presentation issues"))
    story.extend(B([
        "Section order in the typeset output is broken: Section V's subsections (Corpus, "
        "Systems Compared, Metrics, Reproducibility) appear after Section VI's first "
        "subsection. Section VI-A is then empty.",
        "Table III's caption is followed immediately by unrelated body text; the table's "
        "content is missing from the flow.",
        "Tables II to V are referenced in the text before the tables that define their "
        "columns appear.",
        "Equation (1) is reported as \u201cM = w1R + w2F + w3T + w4G + w5U + w6P \u2212 w7D "
        "\u2212 w8C (1)\u201d with no definition list in the manuscript; the eight weights "
        "are never given, so the model is not reproducible from the paper.",
        "The T (recency) term is described as \u201cexponential decay\u201d with a 45-day "
        "half-life, but the expression is only stated as T = 2\u2212\u0394t/45 in the "
        "typeset text, with unclear minus-sign handling.",
        "Reference list: mixed formatting (some entries omit pages, one contains a "
        "mistyped ampersand as \u201cS&amp;P;\u201d), future years (2026) for entries that "
        "do not yet exist, and, verified by scanning the body text for citation markers, "
        "ten of the 25 references are never cited at all: only [1]-[11], [16], [17], [20] "
        "and [23] appear in the argument.",
        "Terminology is inconsistent: \u201cSecond Brain\u201d, \u201cSecondBrain\u201d and "
        "\u201cPersonal Brain-Bench\u201d versus \u201cPersonalBrain-Bench\u201d appear in "
        "the abstract alone.",
        "The Acknowledgment thanks a co-author (the supervisor is listed as an author) - "
        "remove.",
    ]))

    # =====================================================================
    # STAGE 2
    # =====================================================================
    story.append(PageBreak())
    story.append(Section("Stage 2 - Required Changes (prioritised)"))

    story.append(Sub("Red - must fix before submission"))
    story.extend(table([
        ["#", "Change", "Where"],
        ["R1", "Replace every irreproducible figure with the re-measured value: conflicts "
               "2 (not 4); hybrid/graph stale@1 0.182 (not 0.091); latency from the same "
               "run as the rest of the table.",
         "Abstract, V-A, VI, Tables II-V"],
        ["R2", "Correct or remove the references that do not match the published record, and "
               "renumber in order of first citation. Appendix A lists each one.",
         "References"],
        ["R3", "Add the research question (one main, four specific) and hypotheses H1-H4, "
               "each mapped to a reported measurement.",
         "Introduction"],
        ["R4", "Add the adopted-versus-proposed table so no established technique is "
               "presented as new, and rewrite the contribution list around coordinated "
               "integration plus the specific mechanisms.",
         "Introduction, Section III"],
        ["R5", "State the evaluation configuration inside every claim that depends on it "
               "(dense backend, corpus scope, k), and state that the leakage asymmetry "
               "holds in that configuration.",
         "Abstract, V-D, VI"],
        ["R6", "Replace \u201cmachine unlearning\u201d with retrieval-level forgetting "
               "throughout, with one explicit sentence distinguishing them; delete "
               "\u201challucination-free\u201d.",
         "Abstract, I, II, IV-F"],
        ["R7", "Fix the section ordering, the missing Table III content, and the empty VI-A "
               "in the typeset output.",
         "Whole paper"],
        ["R8", "Give the eight weights, the normalisation ranges and the half-life formula "
               "in the manuscript so the scoring model is reproducible from the paper.",
         "Section IV-A"],
    ], [22, W - 92, 70]))

    story.append(Sub("Orange - strongly recommended"))
    story.extend(table([
        ["#", "Change", "Where"],
        ["O1", "Add the component-wise ablation design (cumulative, one mechanism per row) "
               "and mark it [REQUIRES EXPERIMENT].",
         "New section"],
        ["O2", "Add the failure-case analysis: stating where the rules fail is what makes "
               "the rest of the claims credible.",
         "New section"],
        ["O3", "Add conflict-detection precision/recall as a marked missing experiment; do "
               "not claim accuracy that has not been measured.",
         "Section IV-C"],
        ["O4", "Add the end-to-end generation evaluation design, and say plainly that "
               "retrieval metrics are proxies.",
         "Planned evaluation"],
        ["O5", "Add the statistical protocol (counts now; bootstrap CIs and a paired test "
               "once the benchmark grows).",
         "Planned evaluation"],
        ["O6", "Expand Related Work to nine areas including temporal knowledge "
               "representation, consolidation and agent memory, and add the gap table.",
         "Section II"],
        ["O7", "Report rates as counts alongside proportions, and mark where a difference is "
               "one question changing rank.",
         "Section VI"],
    ], [22, W - 92, 70]))

    story.append(Sub("Yellow - optional / future work"))
    story.extend(table([
        ["#", "Change", "Where"],
        ["Y1", "Expand the benchmark beyond 15 memories / 11 questions and add mixed "
               "temporal-contradictory and multi-timestamp categories.",
         "Benchmark (future)"],
        ["Y2", "Threshold and parameter sensitivity studies (0.60-0.90; half-life 15-180 "
               "days; term ablation).",
         "Planned evaluation"],
        ["Y3", "Scalability curve at 15 / 50 / 100 / 500 / 1,000 / 5,000 memories.",
         "Planned evaluation"],
        ["Y4", "A learned rather than fixed weighting of the scoring terms, with the fixed "
               "version as baseline.",
         "Future work"],
        ["Y5", "LLM-assisted extraction behind the high-precision rule-based trigger.",
         "Future work"],
        ["Y6", "A user study on de-identified corpora, and on whether damping is preferred "
               "to removal by real users.",
         "Future work"],
    ], [22, W - 92, 70]))

    # =====================================================================
    # STAGE 4
    # =====================================================================
    story.append(PageBreak())
    story.append(Section("Stage 4 - Experimental Plan"))
    story.append(P(
        "Each experiment below is specified so that it can be run as written. Every one "
        "removes a [REQUIRES EXPERIMENT] marker from the revised paper. The baseline column "
        "names the comparison actually used, not an aspiration."))

    story.append(Sub("E1 - Component-wise ablation"))
    story.extend(table([
        ["Field", "Specification"],
        ["Objective", "Attribute the measured effect to individual mechanisms rather than to "
                      "the post-retrieval layer as a whole."],
        ["Research question", "Which of the five mechanisms (temporal validity, contradiction "
                              "damping, consolidation, forgetting, importance weighting) "
                              "produces the MRR and stale@1 improvements?"],
        ["Input / data", "PersonalBrain-Bench as evaluated in the paper; same corpus, same "
                         "questions, same candidate generation."],
        ["Baseline", "Hybrid retrieval with the entire research layer disabled (row 1)."],
        ["Proposed system", "Cumulative rows, each adding exactly one mechanism: "
                            "+temporal, +contradiction, +consolidation, +forgetting, "
                            "+importance."],
        ["Variables", "Independent: the five mechanism switches. Controlled: corpus, "
                      "questions, k = 5, dense backend, corpus scope."],
        ["Metrics", "Hit@5, MRR, stale@1, forgotten-leak rate, duplicate rate, latency."],
        ["Expected output", "One row per configuration (6 rows), one table. Prediction to "
                            "test: stale@1 falls on the temporal and contradiction rows; "
                            "duplicate rate falls only on the consolidation row; leak rate "
                            "only on the forgetting row."],
        ["Failure condition", "If a mechanism's row shows no change on the metric it targets, "
                              "the mechanism is not doing the work its description implies, "
                              "and the paper must say so."],
    ], [76, W - 76]))

    story.append(Sub("E2 - End-to-end generation evaluation"))
    story.extend(table([
        ["Field", "Specification"],
        ["Objective", "Establish whether retrieval-level gains survive generation, which is "
                      "the paper's actual claim about answers."],
        ["Research question", "Do lower stale@1 and higher MRR produce fewer temporally wrong "
                              "or contradicted answers in generated prose?"],
        ["Input / data", "The 11 benchmark questions, each run against all four pipelines."],
        ["Baseline", "Same model, same prompt, same context length, with context supplied by "
                     "each of the four retrievers."],
        ["Proposed system", "Adaptive retrieval supplying the context."],
        ["Variables", "Independent: retrieval pipeline. Controlled: model and version, "
                      "temperature, prompt template, context budget, question order."],
        ["Metrics", "Answer correctness, temporal correctness, contradiction resolution, "
                    "evidence correctness, forgotten-content leakage in the generated text, "
                    "abstention correctness. Two independent human raters, blind to the "
                    "condition, with a stated disagreement rule (third rater or majority)."],
        ["Expected output", "Six metrics x four systems table, plus a per-question "
                            "disagreement log."],
        ["Note", "Automatic judges introduce their own error modes; if an LLM judge is used "
                 "it must be reported with a human-agreement rate on a subset."],
    ], [76, W - 76]))

    story.append(Sub("E3 - Conflict-detection accuracy"))
    story.extend(table([
        ["Field", "Specification"],
        ["Objective", "Measure the detector's precision and recall, which are currently "
                      "unknown; only its downstream effect has been observed."],
        ["Research question", "How accurate is three-class rule-based conflict detection on "
                              "personal memory text?"],
        ["Input / data", "A manually annotated set of memory pairs: genuine conflicts by "
                         "class (temporal, negation, value change) plus matched "
                         "non-conflicts, including the negative cases the rules are most "
                         "likely to confuse."],
        ["Baseline", "The current rule-based detector."],
        ["Proposed system", "Not applicable - this measures an existing component."],
        ["Variables", "Independent: conflict class. Controlled: annotation guideline, "
                      "annotator training, adjudication rule."],
        ["Metrics", "Per-class precision, recall, F1; confusion matrix; false-positive "
                    "examples quoted in the paper."],
        ["Expected output", "3x3 confusion matrix plus a per-class metric table."],
        ["Known risk", "Negation detection previously produced false positives by substring "
                       "matching; recall is expected to be the weaker figure."],
    ], [76, W - 76]))

    story.append(Sub("E4 - Threshold and parameter sensitivity"))
    story.extend(table([
        ["Field", "Specification"],
        ["Objective", "Show that the consolidation threshold and the scoring constants are "
                      "not arbitrary, and find where behaviour changes."],
        ["Research question", "How sensitive are merge behaviour and retrieval quality to "
                              "the similarity threshold, the recency half-life and the "
                              "importance weights?"],
        ["Input / data", "A corpus enlarged enough to contain many duplicate and "
                         "near-duplicate pairs (see E6); the current 15-memory corpus is too "
                         "small for a threshold curve."],
        ["Baseline", "Threshold 0.78, half-life 45 days, current weights."],
        ["Proposed system", "Sweeps: threshold 0.60, 0.65, 0.70, 0.75, 0.78, 0.80, 0.85, "
                            "0.90; half-life 15, 30, 45, 90, 180 days; each weight zeroed "
                            "in turn."],
        ["Variables", "One parameter per sweep, all others held at the paper's values."],
        ["Metrics", "Merge count, false merges (merged pairs a human judges unrelated), "
                    "duplicate rate, Hit@5, MRR."],
        ["Expected output", "One curve per sweep, plus a table of the value in use and the "
                            "range over which results are stable."],
    ], [76, W - 76]))

    story.append(Sub("E5 - Scalability"))
    story.extend(table([
        ["Field", "Specification"],
        ["Objective", "Establish whether the per-run conflict and temporal lookups stay "
                      "within an interactive budget as the store grows."],
        ["Research question", "How do retrieval latency and offline maintenance cost grow "
                              "with corpus size?"],
        ["Input / data", "Corpora of 15, 50, 100, 500, 1,000 and 5,000 memories, generated "
                         "from the same templates with the same category distribution."],
        ["Baseline", "Hybrid retrieval at each size."],
        ["Proposed system", "Adaptive retrieval at each size."],
        ["Variables", "Independent: corpus size. Controlled: hardware, database engine, "
                      "question set, k."],
        ["Metrics", "Retrieval latency per query (median and 95th percentile over repeated "
                    "runs); offline time for scoring, conflict detection and consolidation; "
                    "peak memory."],
        ["Expected output", "Latency-versus-size curve for both pipelines, on named "
                            "hardware."],
        ["Reporting rule", "Latency is machine-dependent. Report hardware, give the curve, "
                           "and do not claim cross-machine comparability."],
    ], [76, W - 76]))

    story.append(Sub("E6 - Benchmark expansion and statistical protocol"))
    story.extend(table([
        ["Field", "Specification"],
        ["Objective", "Make per-category claims statistically meaningful and remove the "
                      "small-corpus limitation."],
        ["Research question", "Do the observed differences hold beyond 11 questions and 15 "
                              "memories?"],
        ["Input / data", "Proposed categories: factual, temporal, contradiction, multi-hop, "
                         "duplicate, forgetting, abstention, and mixed "
                         "temporal-contradictory cases with more than one supersession in "
                         "the same predicate chain. Target at least 100 questions and "
                         "several hundred memories, with the count per category stated."],
        ["Baseline", "Three baselines as in the paper."],
        ["Proposed system", "Adaptive pipeline."],
        ["Variables", "Independent: pipeline. Controlled: corpus and question set, fixed "
                      "across pipelines."],
        ["Metrics", "All existing metrics, now reported as mean with standard deviation "
                    "over multiple generated corpora, plus 95% bootstrap confidence "
                    "intervals over resampled questions."],
        ["Statistical tests", "Paired over the shared question set: Wilcoxon signed-rank "
                              "for MRR-type statistics, McNemar's test for per-question hit "
                              "and stale outcomes. State the number of questions and the "
                              "significance level."],
        ["Expected output", "One results table with CIs, one per-category table with counts "
                            "and CIs, one statistical test table."],
    ], [76, W - 76]))

    story.append(Sub("E7 - Removal completeness audit"))
    story.extend(table([
        ["Field", "Specification"],
        ["Objective", "Replace the single-surface leakage check with a complete audit of "
                      "every surface from which removed content could re-enter."],
        ["Research question", "Which surfaces retain recoverable traces of a removed "
                              "memory?"],
        ["Input / data", "A memory with a distinctive marker string, ingested, indexed, "
                         "graphed, embedded and extracted into temporal facts; then removed."],
        ["Baseline", "Row-deletion only: delete the memory row and query every surface."],
        ["Proposed system", "The five-surface forgetting service."],
        ["Variables", "Independent: removal strategy. Controlled: the memory and the query "
                      "used to probe each surface."],
        ["Metrics", "Per-surface recovery of the marker (binary), plus an end-to-end query "
                    "test per retrieval mode."],
        ["Expected output", "Surfaces x strategies matrix showing which combinations leave "
                            "the content recoverable."],
        ["Note", "This is also the experiment that justifies the phrasing "
                 "\u201cretrieval-level forgetting\u201d rather than \u201cmachine "
                 "unlearning\u201d."],
    ], [76, W - 76]))

    # =====================================================================
    # STAGE 5
    # =====================================================================
    story.append(PageBreak())
    story.append(Section("Stage 5 - Novelty Statement"))
    story.append(P(
        "The paragraph below is written to be defensible: each clause names what is claimed "
        "and distinguishes it from what is adopted from prior work. It contains no absolute "
        "priority claim, because establishing one would require a systematic review this "
        "work has not performed."))
    story.extend(callout(
        "Novelty statement (one paragraph, for the introduction or the response letter)",
        "This work addresses retrieval-augmented generation over <i>personal</i> knowledge "
        "stores, where the difficulty is not finding relevant evidence but determining which "
        "of several stored, individually faithful memories is currently true. The "
        "individual techniques it builds on are established and are not claimed as novel: "
        "dense, lexical and hybrid retrieval; graph-augmented retrieval; interval-based "
        "temporal triples; cosine near-duplicate clustering; and the broader problem of "
        "removing data from a system. What is proposed and evaluated here is (i) an "
        "operational treatment of current truth over a personal store - intervals that close "
        "facts rather than delete them, so that historical and current questions remain "
        "answerable from one store; (ii) <i>retrieval-time</i> enforcement of temporal "
        "validity, conflict status, duplication and explicit removal, rather than recording "
        "them as metadata, on the argument that retrieval time is where the failure occurs; "
        "(iii) a five-surface formulation of removal that treats derived indexes, vector "
        "embeddings, graph nodes and extracted facts as independent ways for removed content "
        "to return, which is a retrieval-layer property and is explicitly distinguished from "
        "parameter-level machine unlearning; (iv) an auditable importance score whose eight "
        "terms are persisted and which is used only as a light ordering signal, with the "
        "negative result that ranking by importance alone degrades retrieval reported rather "
        "than suppressed; and (v) PersonalBrain-Bench, a controlled corpus and question set "
        "containing superseded, contradictory, duplicated and deliberately forgotten "
        "memories, which makes these failures measurable in aggregate. The empirical "
        "contribution is a negative and a positive result together: on this corpus Hit@5 "
        "saturates for all four pipelines and therefore does not discriminate, while "
        "rank-sensitive and staleness measures do, with the proposed pipeline improving MRR "
        "and reducing stale@1 to zero in a reproducible, model-free configuration. The "
        "paper does not claim that its results generalise beyond the controlled corpus, and "
        "states the component-wise attribution, generation-level, detection-accuracy and "
        "scalability experiments that remain to be run."))

    # =====================================================================
    # APPENDIX A - REFERENCE AUDIT
    # =====================================================================
    story.append(PageBreak())
    story.append(Section("Appendix A - Reference Audit"))
    story.append(P(
        "Every reference in the draft was checked against the published record. Entries "
        "marked \u201cnot located\u201d could not be found under the given title, authors or "
        "venue, and should be removed unless the authors can supply the correct record. "
        "The revised paper's reference list (25 entries reduced to 21, renumbered in order "
        "of first citation) contains only locatable works that are actually cited."))

    story.extend(table([
        ["Draft ref", "Audit result", "Action taken"],
        ["[1] Lewis et al., RAG, NeurIPS 2020", "Correct", "Kept as [1]"],
        ["[2] Gao et al., RAG survey, arXiv 2312.10997", "Correct", "Kept as [2]"],
        ["[3] Edge et al., Graph RAG, arXiv 2404.16130", "Correct", "Kept as [6]"],
        ["[4] Peng et al., Graph RAG survey, arXiv 2408.08921", "Correct", "Kept as [7]"],
        ["[5] Wang et al., LLM autonomous agents survey, Frontiers Comput. Sci.",
         "Correct", "Kept as [10]"],
        ["[6] Bruch, Nedelkoski, Mandal, vector stores, IEEE Big Data 2024",
         "Verified in IEEE Xplore", "Kept as [5]"],
        ["[7] Hou et al., factual reliability, IEEE Access",
         "Not located under this title/author combination", "Removed"],
        ["[8] Ji et al., RAG Certainty",
         "The work exists and is on IEEE Xplore, but the year given in the draft (2026) "
         "is not supported by the record located. Confirm the venue and year from the "
         "paper's own IEEE Xplore entry before resubmitting.",
         "Retained as [17]; year flagged for confirmation, not asserted"],
        ["[9] \u201cK. R. Z. et al.\u201d, ReRag, IEEE Access 2025",
         "Found, but author names are truncated to initials and the venue and year are "
         "wrong: Ko, G\u00fcrkan and Yarman Vural, UBMK (9th Int. Conf. Comput. Sci. Eng.), "
         "2024, pp. 961-965",
         "Authors, venue and year corrected; kept as [16]"],
        ["[10] Asai et al., Self-RAG, ICLR 2024", "Correct", "Kept as [14]"],
        ["[11] Yan et al., Corrective RAG, arXiv 2401.15884", "Correct", "Kept as [15]"],
        ["[12] Prompt injection review, IEEE Access 2025",
         "Not located as cited (the review found is dated later and the author list differs)",
         "Removed - not cited in the argument anyway"],
        ["[13] Zhu et al., LLMs concise review, IEEE Access 2025",
         "Not located under this title; a different LLM review was found with different "
         "authors", "Removed"],
        ["[14] Brown et al., GPT-3, NeurIPS 2020", "Correct, but not cited in the text",
         "Kept as [20] and now cited where the LLM substrate is described"],
        ["[15] Reimers & Gurevych, Sentence-BERT, EMNLP 2019",
         "Correct, but not cited", "Kept as [18] and cited in the retrieval section"],
        ["[16] Karpukhin et al., DPR, EMNLP 2020", "Correct", "Kept as [3]"],
        ["[17] Robertson & Zaragoza, BM25, FnTIR 2009", "Correct", "Kept as [4]"],
        ["[18] Johnson et al., FAISS, IEEE Trans. Big Data",
         "Correct, but not cited", "Kept as [19] and cited with the vector-store discussion"],
        ["[19] Hogan et al., Knowledge Graphs, ACM CSUR", "Correct", "Kept as [8]"],
        ["[20] Bourtoule et al., Machine Unlearning, IEEE S&P 2021", "Correct",
         "Kept as [13] - now the anchor for the unlearning distinction"],
        ["[21] Wu et al., complex reasoning survey, IEEE Trans. Artif. Intell. 2026",
         "Not located as cited", "Removed"],
        ["[22] Zhang et al., personalised learning recommendation, IEEE Trans. Learning "
               "Technol. 2025",
         "Not located under this title; a different paper with a similar title exists in a "
         "different journal", "Removed"],
        ["[23] \u201cR. Wang et al.\u201d, Lifelong Learning of LLM-based Agents, TPAMI 2026",
         "Real work, wrong authors: Zheng, Shi, Cai, Li, Zhang, Li, Yu and Ma, IEEE TPAMI "
         "2026 (early access) / arXiv 2501.07278",
         "Author list corrected; kept as [12] and now central to the agent-memory gap"],
        ["[24] Li et al., Make LLMs Efficient, IEEE Access 2025",
         "Not located as cited", "Removed - not cited in the argument"],
        ["[25] Radford et al., Whisper, ICML 2023",
         "Correct, but not cited in the text", "Kept as [21] and cited for the voice "
         "capture path"],
    ], [140, 216, W - 356]))

    story.append(Sub("References added that the draft lacked"))
    story.append(P(
        "Four areas the argument depends on were unrepresented in the draft. These additions "
        "are all verified records and are cited where the corresponding claim is made:"))
    story.extend(B([
        "Temporal knowledge representation: Cai <i>et al.</i>, \u201cTemporal Knowledge Graph "
        "Completion: A Survey\u201d, IJCAI 2023 (ref [9] in the revised paper). Without this, "
        "the temporal contribution reads as though interval validity were new.",
        "Agent memory mechanisms: Zhang <i>et al.</i>, \u201cA Survey on the Memory Mechanism "
        "of Large Language Model based Agents\u201d, arXiv 2404.13501 (ref [11]). This is the "
        "closest prior work to the memory-persistence claim and must be cited to define the "
        "gap honestly.",
        "Lifelong learning for LLM agents: Zheng <i>et al.</i>, IEEE TPAMI 2026 (ref [12]) - "
        "the corrected version of the draft's [23].",
        "Machine unlearning: the draft's [20], now cited at the point where the distinction "
        "from retrieval-level forgetting is drawn.",
    ]))

    story.append(PageBreak())
    story.append(Section("Summary of Reviewer Verdict"))
    story.append(P(
        "The draft's central idea is sound and its framing is better than its execution. "
        "The blocking problems are not conceptual: two reported figures cannot be "
        "reproduced from the code, several references do not match the published record, and "
        "the contribution statement does not distinguish adopted techniques from proposed "
        "mechanisms. Each has been corrected in the accompanying revised paper."))
    story.append(P(
        "The revised paper is, in my assessment, publishable at a conference as an "
        "<i>evaluation and architecture</i> paper with the small-corpus limitation stated "
        "prominently. It is not yet publishable as a systems result with general claims, "
        "because component-wise attribution, generation-level evaluation and detection "
        "accuracy are all unmeasured; the revised paper says so rather than implying "
        "otherwise. Completing E1 to E3 would raise it to a journal submission where the "
        "component attribution and the end-to-end result carry the argument."))

    # =====================================================================
    # BUILD
    # =====================================================================
    doc = Report(
        OUT,
        pagesize=(595.28, 841.89),          # A4
        leftMargin=62, rightMargin=62, topMargin=62, bottomMargin=60,
        title="Reviewer Report and Revision Plan",
        author="Dr. P S Anu Rakhi; Maria Immanuel L; Vigneshwaran S",
        subject="Critical review, required changes, experimental plan, novelty statement",
    )
    doc.report_title = "Reviewer Report and Revision Plan"
    frame = Frame(62, 60, W, 841.89 - 62 - 60, id="body")
    doc.addPageTemplates([PageTemplate(id="review", frames=[frame], onPage=doc.header_footer)])
    doc.multiBuild(story)

    print(f"[OK] wrote {OUT}")
    try:
        import pymupdf
        d = pymupdf.open(OUT)
        words = sum(len(d[i].get_text().split()) for i in range(d.page_count))
        print(f"     pages : {d.page_count}")
        print(f"     words : approximately {words:,}")
        d.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
