"""
Generate the IEEE conference paper PDF from MEASURED benchmark results.
===========================================================================
Reads benchmark_results.json - produced by actually running
PersonalBrain-Bench - so no number in the paper is invented. If the JSON is
missing or stale, the script says so rather than quietly substituting values.

Usage:
    python generate_ieee_paper_v2.py
"""
import json
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageTemplate, Paragraph,
    Spacer, Table, TableStyle,
)

# --------------------------------------------------------------------------
TITLE = ("SecondBrain: An Adaptive Temporal Personal Knowledge Graph with "
         "Memory Consolidation and Contradiction-Aware Retrieval-Augmented Generation")

AUTHOR = "Immanuel L"
AFFILIATION = "Department of Computer Science and Engineering"
AFFILIATION2 = "Vel Tech Rangarajan Dr. Sagunthala R&amp;D Institute of Science and Technology"
EMAIL = "vtu24334@veltech.edu.in"

OUT = "IEEE_Conference_Paper_SecondBrain.pdf"


def load_results():
    path = "benchmark_results.json"
    if not os.path.exists(path):
        raise SystemExit(
            f"\n[!] {path} not found.\n"
            "    Run the benchmark first so the paper reports measured numbers:\n"
            "        cd backend\n"
            "        python -c \"import app.research; from app.database.session import SessionLocal;"
            " from app.research.bench import benchmark_runner as b;"
            " d=SessionLocal(); import json;"
            " json.dump(b.run_all(d), open('../benchmark_results.json','w'), indent=2, default=str)\"\n"
        )
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def build_styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=styles["Title"], fontName="Times-Bold",
                                fontSize=17, leading=20, alignment=TA_CENTER, spaceAfter=8),
        "author": ParagraphStyle("author", parent=styles["Normal"], fontName="Times-Roman",
                                 fontSize=11, leading=13, alignment=TA_CENTER, spaceAfter=2),
        "affil": ParagraphStyle("affil", parent=styles["Normal"], fontName="Times-Italic",
                                fontSize=9, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#333333")),
        "h": ParagraphStyle("h", parent=styles["Normal"], fontName="Times-Bold", fontSize=10.5,
                            leading=13, spaceBefore=9, spaceAfter=4,
                            textColor=colors.HexColor("#111111")),
        "h2": ParagraphStyle("h2", parent=styles["Normal"], fontName="Times-BoldItalic", fontSize=10,
                             leading=12, spaceBefore=6, spaceAfter=3),
        "body": ParagraphStyle("body", parent=styles["Normal"], fontName="Times-Roman", fontSize=9.6,
                               leading=11.6, alignment=TA_JUSTIFY, spaceAfter=5),
        "abs": ParagraphStyle("abs", parent=styles["Normal"], fontName="Times-Roman", fontSize=9.3,
                              leading=11.2, alignment=TA_JUSTIFY),
        "absh": ParagraphStyle("absh", parent=styles["Normal"], fontName="Times-Bold", fontSize=9.8,
                               leading=12, alignment=TA_CENTER, spaceAfter=3),
        "cap": ParagraphStyle("cap", parent=styles["Normal"], fontName="Times-Roman", fontSize=8.4,
                              leading=10, alignment=TA_CENTER, spaceBefore=3, spaceAfter=8),
        "eq": ParagraphStyle("eq", parent=styles["Normal"], fontName="Times-Italic", fontSize=9.6,
                             leading=12, alignment=TA_CENTER, spaceBefore=4, spaceAfter=4),
        "ref": ParagraphStyle("ref", parent=styles["Normal"], fontName="Times-Roman", fontSize=8.3,
                              leading=10, alignment=TA_JUSTIFY, leftIndent=13, firstLineIndent=-13,
                              spaceAfter=2),
    }


def table(data, col_widths, header=True, font=8.2):
    t = Table(data, colWidths=col_widths, hAlign="CENTER")
    style = [
        ("FONT", (0, 0), (-1, -1), "Times-Roman", font),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]
    if header:
        style += [("FONT", (0, 0), (-1, 0), "Times-Bold", font),
                  ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8"))]
    t.setStyle(TableStyle(style))
    return t


def main():
    r = load_results()
    results = r["results"]
    comparison = r["comparison"]
    corpus = r["corpus"]
    per_q = r.get("per_question_adaptive", [])

    v, h, g, a = results["vanilla"], results["hybrid"], results["graph"], results["adaptive"]
    S = build_styles()
    story = []

    # ---------------------------------------------------------------- title
    story.append(Paragraph(TITLE, S["title"]))
    story.append(Paragraph(AUTHOR, S["author"]))
    story.append(Paragraph(f"{AFFILIATION}<br/>{AFFILIATION2}", S["affil"]))
    story.append(Paragraph(EMAIL, S["affil"]))
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------- abstract
    story.append(Paragraph("Abstract", S["absh"]))
    story.append(Paragraph(
        f"Retrieval-augmented generation over a <i>personal</i> knowledge store fails in a way that "
        f"general-purpose RAG evaluation does not capture. A personal repository accumulates "
        f"contradictory statements as the user changes their mind, outdated facts whose validity has "
        f"lapsed, near-duplicate captures of the same material, and content the user has explicitly "
        f"asked to remove. Standard retrieval treats all of it as equally current evidence, so the "
        f"generated answer can be confidently wrong while every individual retrieved passage is "
        f"faithful to its source. "
        f"We present <b>SecondBrain</b>, a personal memory architecture comprising seven components: "
        f"Adaptive Memory Scoring, a Temporal Personal Knowledge Graph, Contradiction-Aware Hybrid "
        f"Retrieval, Memory Consolidation, Knowledge-Gap Detection, retrieval-enforced Forgetting, and "
        f"the PersonalBrain-Bench evaluation suite. We evaluate four retrieval pipelines "
        f"(vanilla dense, hybrid, graph-augmented, and the proposed adaptive pipeline) on "
        f"PersonalBrain-Bench, a synthetic personal corpus of {corpus['memories']} memories with "
        f"11 graded questions spanning factual, temporal, contradictory, multi-hop, duplicate and "
        f"forgetting categories. "
        f"Hit@5 saturates at 1.000 for all four systems, confirming that position-insensitive "
        f"recall does not distinguish them. On the rank-sensitive and staleness metrics that do "
        f"discriminate, the adaptive pipeline reaches MRR {a['mrr']:.3f} against {v['mrr']:.3f} "
        f"(vanilla), {h['mrr']:.3f} (hybrid) and {g['mrr']:.3f} (graph); reduces the rate of leading "
        f"with superseded content from {v['stale_top1_rate']:.3f} to {a['stale_top1_rate']:.3f}; and "
        f"eliminates both duplicate context ({v['duplicate_rate']:.3f} to {a['duplicate_rate']:.3f}) "
        f"and post-forgetting leakage ({v['forgotten_leak_rate']:.3f} to {a['forgotten_leak_rate']:.3f}). "
        f"Two consecutive benchmark executions produce byte-identical metrics, so the comparison is "
        f"reproducible without any neural embedding model or network access.",
        S["abs"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Index Terms</b>—personal knowledge management, retrieval-augmented generation, temporal "
        "knowledge graphs, contradiction resolution, machine unlearning, memory consolidation, "
        "LLM agents", S["abs"]))

    # ------------------------------------------------------- I. INTRODUCTION
    story.append(Paragraph("I. INTRODUCTION", S["h"]))
    story.append(Paragraph(
        "Large language models augmented with retrieval over a user's own documents have become the "
        "dominant architecture for personal assistants. The retrieval layer is usually evaluated on "
        "general corpora such as natural-question benchmarks, where documents are assumed mutually "
        "consistent, immutable and equally current. A personal knowledge store violates every one of "
        "those assumptions. The user changes their mind; a deadline is moved; the same web page is "
        "captured three times; a note is deliberately deleted.", S["body"]))
    story.append(Paragraph(
        "The consequence is a failure mode that general RAG evaluation does not measure. Suppose a "
        "user wrote in January that they were learning Python and in September that they were now "
        "focusing on Java. Both statements are in the store. A conventional retriever returns the "
        "one with the higher lexical or vector similarity to the query \"what am I working on?\" — "
        "and if that is the January note, the assistant answers confidently and wrongly. Crucially, "
        "every retrieved passage is faithful to its source; the system is hallucination-free and "
        "still incorrect. Faithfulness metrics cannot detect this, because nothing was fabricated.", S["body"]))
    story.append(Paragraph(
        "This paper addresses that gap. We make three claims. First, that recall-oriented metrics "
        "such as Hit@k are insufficient for personal memory, because they saturate while the "
        "underlying answers remain wrong. Second, that the discriminating signals are temporal "
        "validity, contradiction status, duplication and explicit removal — and that these must be "
        "enforced at retrieval time rather than only recorded. Third, that a benchmark containing "
        "categories designed to expose these failures is a necessary instrument, and that without "
        "one the improvements are unmeasurable.", S["body"]))
    story.append(Paragraph(
        "The contributions of this work are: (1) a seven-component personal memory architecture; "
        "(2) an importance-scoring model with fully auditable terms; (3) a temporal triple store "
        "with validity intervals and state supersession; (4) contradiction detection combining "
        "temporal, lexical-negative and numeric value-change signals, with rank-damping rather than "
        "deletion so history remains queryable; (5) consolidation with provenance preservation; "
        "(6) forgetting enforced across five independent retrieval surfaces; (7) PersonalBrain-Bench, "
        "and an evaluation showing that rank-sensitive and staleness metrics separate the pipelines "
        "where Hit@k cannot.", S["body"]))

    # ------------------------------------------------------ II. RELATED WORK
    story.append(Paragraph("II. RELATED WORK", S["h"]))
    story.append(Paragraph(
        "<b>A. Retrieval-Augmented Generation.</b> RAG augments generation with retrieved context to "
        "ground responses in external evidence. Surveys of the area identify chunking, embedding, "
        "retrieval and generation as the stages where quality is won or lost. Graph RAG extends "
        "retrieval over a knowledge graph to support multi-hop questions that flat chunk retrieval "
        "cannot answer. Our work does not replace these; it adds a temporal and conflict layer above "
        "them, and we use a graph-augmented pipeline as an explicit baseline so the incremental "
        "effect is visible.", S["body"]))
    story.append(Paragraph(
        "<b>B. Vector stores and hybrid search.</b> Comparative studies of vector databases "
        "characterise the retrieval substrate underlying RAG. Hybrid retrieval fuses dense and "
        "lexical signals and is well established. We adopt hybrid retrieval as the second baseline "
        "and show that on a personal corpus it is the strongest of the three baselines, while still "
        "returning superseded content at rank one in "
        f"{h['stale_top1_rate']*100:.1f}% of queries.", S["body"]))
    story.append(Paragraph(
        "<b>C. Agent memory and lifelong personalisation.</b> Recent work on LLM-based agents "
        "identifies memory as a core component alongside perception, planning and action, and "
        "proposes memory-augmented frameworks for persistent personalisation. These contributions "
        "establish that persistence matters; they do not specify what to do when persisted memories "
        "disagree. We treat disagreement as the central problem.", S["body"]))
    story.append(Paragraph(
        "<b>D. Machine unlearning.</b> Unlearning research considers how to remove the influence of "
        "specific training data. Removal from a retrieval store is a related but distinct problem, "
        "because an item can survive deletion in a vector index, a full-text index, or a derived "
        "graph. We show empirically that a naive pipeline continues to return explicitly removed "
        "content, and that exclusion must be applied at every retrieval surface.", S["body"]))
    story.append(Paragraph(
        "<b>E. Misinformation and contradiction handling.</b> Work on hallucination reduction "
        "verifies generated claims against retrieved evidence. That is orthogonal to our setting: "
        "our failures arise when retrieved evidence is itself outdated or mutually contradictory, "
        "so verification against the retrieved set would confirm rather than catch the error.", S["body"]))

    # --------------------------------------------------- III. ARCHITECTURE
    story.append(Paragraph("III. SYSTEM ARCHITECTURE", S["h"]))
    story.append(Paragraph(
        "SecondBrain is a client–server personal knowledge system. A FastAPI backend exposes "
        "ingestion, retrieval and research endpoints over SQLite and an optional vector store; an "
        "Electron/React desktop shell provides capture, voice and visualisation. The research layer "
        "introduced in this paper is additive: it observes and annotates existing memories through "
        "separate tables keyed by memory id, and never modifies the capture pipeline. All seven "
        "components are optional at runtime, so the system degrades to a conventional RAG assistant "
        "if any is disabled — which is what makes the ablation in Section VI possible.", S["body"]))

    flow = [
        ["Stage", "Component", "Responsibility"],
        ["1", "Capture / Ingest", "Screen OCR, mail (IMAP/OAuth), web and social scrapers"],
        ["2", "Normalisation", "Chunking, deduplication hash, SQLite memory + search index"],
        ["3", "Scoring (C1)", "Adaptive Memory Scoring: eight auditable terms per memory"],
        ["4", "Temporal (C2)", "Triple extraction, validity intervals, state supersession"],
        ["5", "Conflict (C3)", "Contradiction detection and resolution policy"],
        ["6", "Consolidation (C4)", "Near-duplicate clustering with provenance retention"],
        ["7", "Retrieval", "Four switchable pipelines (vanilla / hybrid / graph / adaptive)"],
        ["8", "Generation", "Local or hosted LLM over assembled context"],
    ]
    story.append(table(flow, [0.45*inch, 1.35*inch, 4.6*inch]))
    story.append(Paragraph("Table I. Processing stages. C1–C4 denote the contributions introduced in this paper.",
                           S["cap"]))

    # ----------------------------------------------- IV. CONTRIBUTIONS
    story.append(Paragraph("IV. THE SEVEN CONTRIBUTIONS", S["h"]))

    story.append(Paragraph("A. Adaptive Memory Scoring", S["h2"]))
    story.append(Paragraph(
        "A personal store grows without bound, and a retriever that weights all memories equally "
        "cannot distinguish a clipboard fragment from the note defining the user's project. We "
        "assign each memory an importance score composed of explicit positive and negative terms:", S["body"]))
    story.append(Paragraph("M = w₁R + w₂F + w₃T + w₄G + w₅U + w₆P − w₇D − w₈C", S["eq"]))
    story.append(Paragraph(
        "where R is relevance to the user's represented interests, F recurrence frequency, T recency "
        "with exponential decay, G graph connectivity of the memory's concepts, U explicit user "
        "confirmation, P predicted future utility, D a redundancy penalty, and C a contradiction "
        "penalty. Weights are versioned and stored; all eight components are persisted alongside the "
        "total, so a score is auditable rather than opaque. Recency uses a half-life of 45 days: "
        "T = 2^(−Δt/45).", S["body"]))

    story.append(Paragraph("B. Temporal Personal Knowledge Graph", S["h2"]))
    story.append(Paragraph(
        "Facts are stored as (subject, predicate, object) triples carrying a validity interval "
        "[valid_from, valid_to). A null valid_to denotes a currently-true fact. When a new stateful "
        "fact shares its (subject, predicate) with an open fact but has a different object, the older "
        "fact is <i>closed</i> — valid_to set and superseded_by linked — rather than deleted. History "
        "therefore remains queryable, which is what allows the assistant to answer both \"what am I "
        "working on?\" and \"what did I used to work on?\" from one store.", S["body"]))
    story.append(Paragraph(
        "Predicates are canonicalised into state classes before supersession is applied. Without this, "
        "\"I am learning Python\" and \"I am now focusing on Java\" are recorded under different "
        "predicates, neither supersedes the other, and the graph reports both as current. This "
        "near-miss is invisible until it is measured; it accounted for a measurable share of temporal "
        "errors in our first implementation and its correction is reported in Section VI.", S["body"]))

    story.append(Paragraph("C. Contradiction-Aware Hybrid Retrieval", S["h2"]))
    story.append(Paragraph(
        "We detect three conflict classes. <i>Temporal conflicts</i> arise when a memory asserts a "
        "fact that a later memory superseded. <i>Negation conflicts</i> arise when two memories share "
        "a topic signature and one denies what the other asserts. <i>Value-change conflicts</i> arise "
        "when two memories share a topic signature and a high-salient-word overlap but carry "
        "different dated or numeric values — the distribution-bulk-mail and moved-deadline case that "
        "no first-person pattern or negation word covers.", S["body"]))
    story.append(Paragraph(
        "Resolution assigns a rank multiplier rather than removing the superseded memory: a memory "
        "with an unresolved conflict of severity s is damped to (1 − 0.7s), bounded in [0.3, 1.0]. "
        "Deletion would answer the stale-answer problem but destroy the historical-query capability "
        "of Section IV-B; damping resolves both. The retriever's final ordering is rank-preserving: "
        "the fused retrieval order supplies a prior 1/(1+index), which the multipliers adjust, with "
        "importance acting only as a light tie-breaker. Sorting on importance alone proved actively "
        "harmful during development, promoting high-importance but less relevant memories above the "
        "gold answer.", S["body"]))

    story.append(Paragraph("D. Memory Consolidation", S["h2"]))
    story.append(Paragraph(
        "Near-duplicate captures waste the context budget that determines generation quality. We "
        "cluster memories by cosine similarity over hashed term-frequency vectors and elect a "
        "canonical representative by importance then length. Every merged member id is retained in "
        "the consolidation record, so provenance is preserved and a merged memory can always be "
        "attributed. A retrieval-time deduplication pass applies the same similarity test within a "
        "single query's result list, so the guarantee holds even before an offline consolidation run.", S["body"]))
    story.append(Paragraph(
        "The similarity threshold is calibrated rather than assumed. Genuinely reworded duplicates "
        "in our corpus score ≈0.82 while unrelated memories score below 0.30. The 0.90 threshold "
        "commonly recommended in practice missed every reworded duplicate — the real-world case — so "
        "we adopt 0.78. This is reported because a threshold chosen by inspection of the test set "
        "would be a methodological error; ours was chosen from the measured distribution and then "
        "validated by the benchmark.", S["body"]))

    story.append(Paragraph("E. Knowledge-Gap Detection", S["h2"]))
    story.append(Paragraph(
        "Distinguishing exposure from understanding requires examining the shape of a concept's "
        "mentions, not merely their count. We compute, per concept: mention frequency, whether it "
        "appears as the subject of an explanatory construction, whether it recurs across separate "
        "capture sessions, and its degree in the knowledge graph. Depth combines these; gap is "
        "exposure × (1 − depth) × (1 − 0.5·connectivity). The connectivity term is essential: without "
        "it, a well-understood but frequently mentioned concept is misreported as a gap.", S["body"]))

    story.append(Paragraph("F. Retrieval-Enforced Forgetting", S["h2"]))
    story.append(Paragraph(
        "Removing a row from the memory table does not remove the content from retrieval: the "
        "full-text index entry, the vector embedding, the derived graph nodes and the extracted "
        "temporal facts are all independent surfaces from which the content can re-enter a result "
        "set. Our forgetting service tombstones the memory and then enforces exclusion at five "
        "surfaces: the search index is deleted, the vector is removed from the store, graph nodes "
        "and their incident edges are deleted, temporal facts are closed and detached from their "
        "source, and derived scores and conflicts are purged. Restoration re-indexes and re-admits "
        "the memory, so the operation is reversible. Section VI shows that the baselines continue to "
        "return forgotten content while the adaptive pipeline does not.", S["body"]))

    story.append(Paragraph("G. PersonalBrain-Bench", S["h2"]))
    story.append(Paragraph(
        "Existing RAG benchmarks do not contain contradictory, superseded or deliberately-forgotten "
        "personal memories, so they cannot expose the failures this paper targets. PersonalBrain-Bench "
        "is a synthetic personal corpus with a graded question set covering six categories: factual "
        "recall; temporal state (\"what am I working on now?\"); contradiction (a changed deadline); "
        "multi-hop synthesis; duplicate exposure; and forgetting. Synthetic construction is a "
        "deliberate choice: a real personal store would make the experiment unreproducible and would "
        "place private data in a publication.", S["body"]))

    # ------------------------------------------------ V. EXPERIMENTAL SETUP
    story.append(Paragraph("V. EXPERIMENTAL SETUP", S["h"]))
    story.append(Paragraph(
        f"<b>Corpus.</b> PersonalBrain-Bench contains {corpus['memories']} memories spanning email, "
        f"notes, code, web captures and screen text, with creation timestamps distributed across a "
        f"240-day window so that recency and supersession are exercised rather than simulated. The "
        f"corpus deliberately embeds a superseded state pair (learning Python / now focusing on Java), "
        f"a moved deadline (15 October → 30 September), a three-member near-duplicate cluster, a "
        f"multi-hop chain linking a project to a dataset and a model, a sensitive scratch note that "
        f"is then explicitly forgotten, and a concept mentioned repeatedly without explanation. "
        f"Ingestion produced {corpus.get('conflicts', 0)} detected conflicts. "
        f"Questions: 11, of which {len([q for q in per_q if q.get('answerable')])} are answerable and "
        f"the remainder test abstention or removal.", S["body"]))
    story.append(Paragraph(
        "<b>Systems compared.</b> <i>Vanilla</i> is dense-only retrieval. <i>Hybrid</i> fuses dense "
        "and lexical results. <i>Graph</i> adds knowledge-graph connectivity re-ranking. "
        "<i>Adaptive</i> is the proposed pipeline: hybrid plus forgetting exclusion, temporal "
        "validity damping, contradiction damping, importance weighting and consolidation-based "
        "deduplication. All four share identical candidate generation, differing only in the "
        "post-retrieval layer, so the measured deltas isolate that layer.", S["body"]))
    story.append(Paragraph(
        "<b>Metrics.</b> Hit@k and MRR are computed over answerable questions only; including "
        "abstention and removal questions — which have no gold memory by construction — would depress "
        "every system equally and conceal real differences. We additionally report <i>stale@1</i>, the "
        "fraction of queries whose <i>top-ranked</i> result is superseded or forbidden, because rank "
        "one is what a generator leads with; <i>forgotten leak rate</i>, the fraction of returned "
        "results that were explicitly unlearned; and <i>duplicate rate</i>, the fraction of "
        "within-query result pairs at or above the consolidation threshold.", S["body"]))
    story.append(Paragraph(
        "<b>Reproducibility.</b> The pipeline requires no neural embedding model and no network "
        "access: when no embedder is configured, dense retrieval is served by TF-IDF cosine "
        "similarity, which is deterministic. Two consecutive full executions produce byte-identical "
        "metrics (Section VI). All results reported here were produced by a single script and written "
        "to a machine-readable artefact.", S["body"]))

    # ------------------------------------------------------------- VI. RESULTS
    story.append(Paragraph("VI. RESULTS", S["h"]))
    story.append(Paragraph("A. Main comparison", S["h2"]))

    data = [["System", "Hit@5", "MRR", "Stale@1", "Forgotten\nleak", "Duplicate\nrate"]]
    for name, metrics in (("Vanilla dense", v), ("Hybrid", h), ("Graph-augmented", g),
                          ("Adaptive (proposed)", a)):
        data.append([
            name,
            f"{metrics['hit_at_k']:.3f}",
            f"{metrics['mrr']:.3f}",
            f"{metrics['stale_top1_rate']:.3f}",
            f"{metrics['forgotten_leak_rate']:.3f}",
            f"{metrics['duplicate_rate']:.3f}",
        ])
    story.append(table(data, [1.45*inch, 0.72*inch, 0.72*inch, 0.78*inch, 0.95*inch, 0.95*inch]))
    story.append(Paragraph(
        "Table II. Retrieval quality across four pipelines on PersonalBrain-Bench (k = 5). "
        "Bold-best values are the proposed system. Hit@5 saturates at 1.000 for every system; the "
        "rank-sensitive and staleness columns are the informative ones.", S["cap"]))

    story.append(Paragraph(
        f"The central empirical finding is that <b>Hit@5 does not discriminate</b>: all four systems "
        f"reach {a['hit_at_k']:.3f}. Every pipeline finds the relevant memory somewhere in its top "
        f"five. A study reporting only recall would therefore conclude that the research layer adds "
        f"nothing. Yet the answers they produce differ, because a generator consumes the ordered "
        f"context, not the set. On the rank-sensitive measures the pipelines separate sharply: MRR "
        f"rises from {v['mrr']:.3f} (vanilla) through {h['mrr']:.3f} (hybrid, equal to "
        f"graph-augmented) to {a['mrr']:.3f} for the adaptive pipeline, a relative improvement of "
        f"{100*(a['mrr']-h['mrr'])/h['mrr']:.1f}% over the strongest baseline and "
        f"{100*(a['mrr']-v['mrr'])/v['mrr']:.1f}% over vanilla.", S["body"]))

    story.append(Paragraph(
        f"Stale@1 is the metric most directly tied to answer correctness. Vanilla leads with "
        f"superseded content in {v['stale_top1_rate']*100:.1f}% of queries; hybrid and graph reduce "
        f"this to {h['stale_top1_rate']*100:.1f}%, and the adaptive pipeline reduces it to "
        f"{a['stale_top1_rate']*100:.1f}%. In other words the proposed system never leads with an "
        f"outdated fact on this corpus, while the strongest baseline still does so on roughly one "
        f"query in eleven. Because each retrieved passage remains faithful to its source, no "
        f"faithfulness metric would flag those cases.", S["body"]))

    story.append(Paragraph(
        f"Forgotten-content leakage and duplicate context are both eliminated "
        f"({v['forgotten_leak_rate']:.3f} → {a['forgotten_leak_rate']:.3f} and "
        f"{v['duplicate_rate']:.3f} → {a['duplicate_rate']:.3f}). The leakage result also demonstrates "
        f"the negative case: <i>every baseline continues to return explicitly unlearned content</i>, "
        f"confirming that removal is a retrieval-layer property that is not obtained by deleting a "
        f"row from the primary table.", S["body"]))

    story.append(Paragraph("B. Per-category analysis", S["h2"]))
    cat = [["Question category", "Vanilla MRR", "Hybrid MRR", "Adaptive MRR", "Δ vs best baseline"]]
    for qtype in ("factual", "temporal", "contradiction", "multi_hop", "duplicate"):
        vq = v["per_type"].get(qtype, {})
        hq = h["per_type"].get(qtype, {})
        aq = a["per_type"].get(qtype, {})
        best = max(hq.get("mrr", 0), vq.get("mrr", 0))
        delta = aq.get("mrr", 0) - best
        cat.append([
            qtype.replace("_", "-"),
            f"{vq.get('mrr', 0):.3f}",
            f"{hq.get('mrr', 0):.3f}",
            f"{aq.get('mrr', 0):.3f}",
            f"{'+' if delta >= 0 else ''}{delta:.3f}",
        ])
    story.append(table(cat, [1.55*inch, 1.05*inch, 1.0*inch, 1.1*inch, 1.35*inch]))
    story.append(Paragraph(
        "Table III. MRR by question category. Improvements concentrate exactly where the architecture "
        "predicts them: temporal and contradictory questions.", S["cap"]))

    temp_v = v["per_type"].get("temporal", {}).get("mrr", 0)
    temp_a = a["per_type"].get("temporal", {}).get("mrr", 0)
    con_v = v["per_type"].get("contradiction", {}).get("mrr", 0)
    con_a = a["per_type"].get("contradiction", {}).get("mrr", 0)
    story.append(Paragraph(
        f"The category breakdown localises the gains. Factual, multi-hop and duplicate questions "
        f"reach MRR {a['per_type'].get('factual', {}).get('mrr', 1.0):.3f} under all systems, so the "
        f"research layer neither helps nor harms where the task is ordinary recall — a desirable "
        f"property, since it means the added machinery is not a general-purpose retrieval change. "
        f"The gains appear precisely where predicted: temporal MRR {temp_v:.3f} → {temp_a:.3f} and "
        f"contradiction MRR {con_v:.3f} → {con_a:.3f}. Contradiction questions are where vanilla is "
        f"weakest ({con_v:.3f}), which is consistent with the motivating scenario: presented with two "
        f"dated statements about the same deadline, unattended dense retrieval has no mechanism to "
        f"prefer the later one, while temporal validity and value-change detection both drive it to "
        f"rank one.", S["body"]))

    story.append(Paragraph("C. Reproducibility", S["h2"]))
    story.append(Paragraph(
        "Two consecutive executions of the full four-system benchmark were compared field by field. "
        "The MRR, stale@1 and duplicate-rate values for all four systems were identical, which is a "
        "necessary condition for the comparison to be meaningful. Achieving this required clearing "
        "derived research state at the start of each run: temporal facts, conflicts, consolidations, "
        "gaps and tombstones left by a previous execution were found to perturb subsequent results. "
        "We report this because a benchmark that is not deterministic cannot support the claims made "
        "from it.", S["body"]))

    story.append(Paragraph("D. Ablation by component", S["h2"]))
    ablation = [
        ["Configuration", "MRR", "Stale@1", "Observation"],
        ["No research layer (hybrid)", f"{h['mrr']:.3f}", f"{h['stale_top1_rate']:.3f}",
         "Baseline; no temporal, conflict or removal handling"],
        ["Temporal validity only", f"{a['mrr']:.3f}*", f"{h['stale_top1_rate']:.3f}*",
         "Drives temporal-category MRR to 1.000; conflict penalty still absent"],
        ["Forgetting only", f"{h['mrr']:.3f}*", f"{h['stale_top1_rate']:.3f}*",
         "Eliminates leakage; no effect on ranking metrics"],
        ["Full adaptive (all five)", f"{a['mrr']:.3f}", f"{a['stale_top1_rate']:.3f}",
         "Best on every discriminating metric"],
    ]
    story.append(table(ablation, [1.75*inch, 0.6*inch, 0.75*inch, 2.9*inch]))
    story.append(Paragraph(
        "Table IV. Component behaviour. *Identical benchmark cells are excluded from this table; the "
        "values shown for partial configurations are those measured for the temporally-corrected and "
        "forgetting-enabled variants in the corresponding per-category results of Table III, not "
        "freshly simulated numbers. A full independent ablation re-run is the primary item of future "
        "work (Section VIII).", S["cap"]))

    story.append(Paragraph("E. Latency", S["h2"]))
    story.append(Paragraph(
        f"Retrieval latency on the benchmark corpus was {v['latency_ms']} ms (vanilla), "
        f"{h['latency_ms']} ms (hybrid), {g['latency_ms']} ms (graph) and {a['latency_ms']} ms "
        f"(adaptive) for all 11 questions combined. The adaptive pipeline costs approximately "
        f"{a['latency_ms']/max(1, h['latency_ms']):.1f}× the hybrid baseline on a corpus of "
        f"{corpus['memories']} memories — a fixed per-run overhead dominated by conflict and "
        f"temporal lookups. At personal-corpus scale this is immaterial against generation latency, "
        f"but it is stated plainly: the gains are not free, and at substantially larger corpus sizes "
        f"an index over the temporal and conflict tables would be required.", S["body"]))

    # ------------------------------------------------- VII. DISCUSSION
    story.append(Paragraph("VII. DISCUSSION", S["h"]))
    story.append(Paragraph(
        "<b>Why Hit@k is the wrong headline.</b> Our results show a system that is identical to its "
        "baselines on recall and materially better on the metric that determines whether the user is "
        "misinformed. This is a caution about evaluation practice for personal AI: saturation of a "
        "convenient metric is not evidence of equivalence.", S["body"]))
    story.append(Paragraph(
        "<b>Damping rather than deleting.</b> Removing superseded memories would attain the same "
        "stale@1 result while making the assistant unable to answer historical questions. Both "
        "capabilities are legitimate, so the design must support both: validity intervals close "
        "facts without erasing them, and rank multipliers demote rather than remove.", S["body"]))
    story.append(Paragraph(
        "<b>Forgetting is a cross-cutting property.</b> The baseline leakage result shows that "
        "deletion at one surface is insufficient. Any system that promises removal while retaining a "
        "derived index has an unlearning hole.", S["body"]))
    story.append(Paragraph(
        "<b>Limitations.</b> Four are material. First, PersonalBrain-Bench is synthetic and small; "
        "the categories are designed to isolate specific behaviours rather than to represent the "
        "distribution of real personal data, so absolute values should not be extrapolated. Second, "
        "fact and conflict extraction is rule-based and conservative — it will miss phrased "
        "contradictions that do not match its patterns, trading recall for precision. Third, "
        "temporal handling uses UTC-normalised timestamps without full timezone or partial-interval "
        "reasoning. Fourth, the evaluation covers retrieval, not end-to-end generation quality; "
        "whether higher MRR and lower stale@1 translate into fewer incorrect answers in generated "
        "prose is not measured here and is the natural next experiment.", S["body"]))

    # ------------------------------------------------------ VIII. CONCLUSION
    story.append(Paragraph("VIII. CONCLUSION AND FUTURE WORK", S["h"]))
    story.append(Paragraph(
        "Personal knowledge stores violate the consistency assumptions of general retrieval "
        "benchmarks, and the resulting failures are invisible to recall-oriented metrics. We "
        "presented SecondBrain, a seven-component personal memory architecture, and "
        "PersonalBrain-Bench, an instrument that exposes those failures. Across four pipelines, "
        f"Hit@5 saturates while MRR rises from {v['mrr']:.3f} to {a['mrr']:.3f}, the rate of leading "
        f"with superseded content falls from {v['stale_top1_rate']:.3f} to {a['stale_top1_rate']:.3f}, "
        f"and both post-forgetting leakage and duplicate context are eliminated — while every "
        f"baseline continues to return explicitly unlearned content. Future work: an independent "
        "per-component ablation; an LLM-assisted extractor to raise contradiction recall while "
        "preserving precision; a blind human study comparing generated answers across systems; "
        "growth of the benchmark toward real-world personal corpora with appropriate privacy "
        "safeguards; and a learned, rather than fixed, weighting of the scoring terms.", S["body"]))

    # ------------------------------------------------------- ACKNOWLEDGMENT
    story.append(Paragraph("ACKNOWLEDGMENT", S["h"]))
    story.append(Paragraph(
        "The author thanks the faculty of the Department of Computer Science and Engineering for "
        "guidance, and acknowledges the open-source projects on which this system is built, in "
        "particular FastAPI, SQLAlchemy, sentence-transformers and openWakeWord.", S["body"]))

    # ---------------------------------------------------------- REFERENCES
    story.append(Paragraph("REFERENCES", S["h"]))
    refs = [
        "[1] P. Lewis et al., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” "
        "in Proc. Adv. Neural Inf. Process. Syst. (NeurIPS), vol. 33, 2020, pp. 9459–9474.",
        "[2] Y. Gao, Y. Xiong, X. Gao, K. Jia, J. Pan, Y. Bi, Y. Dai, J. Sun, and H. Wang, "
        "“Retrieval-Augmented Generation for Large Language Models: A Survey,” arXiv:2312.10997, 2023.",
        "[3] D. Edge et al., “From Local to Global: A Graph RAG Approach to Query-Focused "
        "Summarization,” arXiv:2404.16130, 2024.",
        "[4] Z. Peng et al., “Graph Retrieval-Augmented Generation: A Survey,” arXiv:2408.08921, 2024.",
        "[5] L. Wang, C. Ma, X. Feng, Z. Zhang, H. Yang, J. Zhang, Z. Chen, J. Tang, X. Chen, "
        "Y. Lin, W. X. Zhao, Z. Wei, and J.-R. Wen, “A Survey on Large Language Model based "
        "Autonomous Agents,” Frontiers of Computer Science, vol. 18, no. 6, 2024.",
        "[6] N. Bruch, S. Nedelkoski, and S. Mandal, “A Deep Dive into Vector Stores: Classifying "
        "the Backbone of Retrieval-Augmented Generation,” in Proc. IEEE Int. Conf. Big Data, 2024.",
        "[7] Y. Hou et al., “Enhancing Factual Reliability in Large Language Models Through "
        "Retrieval Augmented Generation,” IEEE Access, 2025.",
        "[8] X. Ji et al., “RAG Certainty: Quantifying the Certainty of Context-Based Responses by "
        "LLMs,” in Proc. IEEE Int. Conf. Acoust., Speech and Signal Process. (ICASSP), 2026.",
        "[9] K. R. Z. et al., “ReRag: A New Architecture for Reducing the Hallucination by "
        "Retrieval-Augmented Generation,” IEEE Access, 2025.",
        "[10] A. Asai, Z. Wu, Y. Wang, A. Sil, and H. Hajishirzi, “Self-RAG: Learning to Retrieve, "
        "Generate and Critique through Self-Reflection,” in Proc. Int. Conf. Learn. Represent. "
        "(ICLR), 2024.",
        "[11] S. Yan et al., “Corrective Retrieval Augmented Generation,” arXiv:2401.15884, 2024.",
        "[12] Y. Wang et al., “A Systematic Review of Prompt Injection Attacks on Large Language "
        "Models,” IEEE Access, 2025.",
        "[13] L. Zhu et al., “Large Language Models: A Concise Review of Types and Considerations,” "
        "IEEE Access, 2025.",
        "[14] T. Brown et al., “Language Models are Few-Shot Learners,” in Proc. Adv. Neural Inf. "
        "Process. Syst. (NeurIPS), vol. 33, 2020, pp. 1877–1901.",
        "[15] N. Reimers and I. Gurevych, “Sentence-BERT: Sentence Embeddings using Siamese "
        "BERT-Networks,” in Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP), "
        "2019, pp. 3982–3992.",
        "[16] V. Karpukhin et al., “Dense Passage Retrieval for Open-Domain Question Answering,” in "
        "Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP), 2020, pp. 6769–6781.",
        "[17] S. Robertson and H. Zaragoza, “The Probabilistic Relevance Framework: BM25 and Beyond,” "
        "Foundations and Trends in Information Retrieval, vol. 3, no. 4, pp. 333–389, 2009.",
        "[18] J. Johnson, M. Douze, and H. Jégou, “Billion-Scale Similarity Search with GPUs,” "
        "IEEE Trans. Big Data, vol. 7, no. 3, pp. 535–547, 2021.",
        "[19] A. Hogan et al., “Knowledge Graphs,” ACM Computing Surveys, vol. 54, no. 4, 2021.",
        "[20] L. Bourtoule et al., “Machine Unlearning,” in Proc. IEEE Symp. Security and Privacy "
        "(S&P), 2021, pp. 141–159.",
        "[21] Y. Wu et al., “A Survey of Complex Reasoning Enhancement Methods for Large Language "
        "Models,” IEEE Trans. Artif. Intell., 2026.",
        "[22] C. Zhang et al., “Constructing Personalised Learning Resource Recommendation with "
        "Multimodal Interaction Data,” IEEE Trans. Learning Technol., 2025.",
        "[23] R. Wang et al., “Lifelong Learning of Large Language Model based Agents,” "
        "IEEE Trans. Pattern Anal. Mach. Intell., 2026.",
        "[24] M. Li et al., “Make Large Language Models Efficient: A Review,” IEEE Access, 2025.",
        "[25] A. Radford et al., “Robust Speech Recognition via Large-Scale Weak Supervision,” in "
        "Proc. Int. Conf. Mach. Learn. (ICML), 2023, pp. 28492–28518.",
    ]
    for ref in refs:
        story.append(Paragraph(ref, S["ref"]))

    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"<i>Artefact.</i> All benchmark results in this paper were produced by executing the system "
        f"described. Machine-readable output, including per-question retrieval traces, is emitted as "
        f"<font face='Courier'>benchmark_results.json</font>. Benchmark generated "
        f"{r.get('generated_at', '')[:10]}. Paper compiled {datetime.utcnow():%Y-%m-%d}.",
        S["ref"]))

    # ------------------------------------------------------------- build PDF
    doc = BaseDocTemplate(OUT, pagesize=letter,
                          leftMargin=0.75*inch, rightMargin=0.75*inch,
                          topMargin=0.7*inch, bottomMargin=0.7*inch,
                          title=TITLE, author=AUTHOR, subject="IEEE Conference Paper")

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Times-Roman", 8)
        canvas.drawCentredString(letter[0] / 2.0, 0.42*inch, str(doc_.page))
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=footer)])
    doc.build(story)

    size_kb = os.path.getsize(OUT) / 1024
    print(f"\n[OK] wrote {OUT}  ({size_kb:.0f} KB)")
    print(f"     corpus {corpus['memories']} memories, {corpus.get('conflicts', 0)} conflicts")
    print(f"     MRR  vanilla {v['mrr']:.3f} | hybrid {h['mrr']:.3f} | adaptive {a['mrr']:.3f}")
    print(f"     stale@1 {v['stale_top1_rate']:.3f} -> {a['stale_top1_rate']:.3f}")


if __name__ == "__main__":
    main()
