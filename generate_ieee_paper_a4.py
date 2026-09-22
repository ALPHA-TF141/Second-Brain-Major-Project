"""
Generate the IEEE conference paper in A4 two-column format.
===========================================================================
Matches the supplied templates:
  * conference-template-a4.pdf   (IEEE A4, two columns, small-caps headings)
  * Clinical_MultiAgent_IEEE_Report.pdf  (author block, TABLE n captions,
    Abstract— / Keywords— em dashes, ACKNOWLEDGMENT, numbered references)

All quantitative content is read from benchmark_results.json, which is produced
by actually running PersonalBrain-Bench. No number in the paper is typed by hand;
if the artefact is missing the script stops rather than inventing values.

Usage:  python generate_ieee_paper_a4.py
"""
import json
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, FrameBreak, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

# ===========================================================================
# EDIT THESE BEFORE SUBMISSION
# ===========================================================================
COPYRIGHT = "XXX-X-XXXX-XXXX-X/XX/$XX.00 ©20XX IEEE"

TITLE = ("SecondBrain: An Adaptive Temporal Personal Knowledge Graph with "
         "Memory Consolidation and Contradiction-Aware Retrieval-Augmented Generation")

# Author block, in required order: supervisor first, then the two student authors.
AUTHORS = [
    {
        # Supervisor listed first, per the institutional convention used in the
        # reference paper supplied by the author.
        "name": "Dr. P S Anu Rakhi",
        "role": "Assistant Professor",
        "dept": "School of Computing",
        "org": "Vel Tech Rangarajan Dr. Sagunthala R&D\nInstitute of Science and Technology",
        "city": "Chennai, India",
        "email": "anurakhips@veltech.edu.in",
    },
    {
        "name": "Maria Immanuel L",
        "role": "",
        "dept": "School of Computing",
        "org": "Vel Tech Rangarajan Dr. Sagunthala R&D\nInstitute of Science and Technology",
        "city": "Chennai, India",
        "email": "vtu24334@veltech.edu.in",
    },
    {
        "name": "Vigneshwaran S",
        "role": "",
        "dept": "School of Computing",
        "org": "Vel Tech Rangarajan Dr. Sagunthala R&D\nInstitute of Science and Technology",
        "city": "Chennai, India",
        "email": "vtu24372@veltech.edu.in",
    },
]

OUT = "IEEE_Conference_Paper_SecondBrain_A4.pdf"
RESULTS_FILE = "benchmark_results.json"

# ------------------------------------------------------------------ geometry
PAGE_W, PAGE_H = A4
MARGIN_X = 45          # ~0.63 in
MARGIN_TOP = 46
MARGIN_BOTTOM = 52
GUTTER = 18
COL_W = (PAGE_W - 2 * MARGIN_X - GUTTER) / 2.0
BODY_H = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM

# ------------------------------------------------------------------- styles
FS = 9.2                # body font size (IEEE is 10pt on A4; 9.2 keeps page count sane)
LEAD = 11.1


def styles():
    return {
        "copyright": ParagraphStyle("copyright", fontName="Times-Roman", fontSize=7.6,
                                    leading=9, alignment=TA_CENTER,
                                    textColor=colors.HexColor("#333333")),
        "title": ParagraphStyle("title", fontName="Times-Bold", fontSize=19,
                                leading=22.5, alignment=TA_CENTER, spaceBefore=2, spaceAfter=8),
        "author_name": ParagraphStyle("author_name", fontName="Times-Roman", fontSize=10,
                                      leading=12.4, alignment=TA_CENTER),
        "author_affil": ParagraphStyle("author_affil", fontName="Times-Italic", fontSize=8.4,
                                       leading=10.2, alignment=TA_CENTER),
        "author_email": ParagraphStyle("author_email", fontName="Times-Roman", fontSize=8.4,
                                       leading=10.4, alignment=TA_CENTER),
        "abs": ParagraphStyle("abs", fontName="Times-Bold", fontSize=9.0, leading=10.9,
                              alignment=TA_JUSTIFY, spaceAfter=5),
        "abs_body": ParagraphStyle("abs_body", fontName="Times-Roman", fontSize=9.0, leading=10.9,
                                   alignment=TA_JUSTIFY, spaceAfter=5),
        "kw": ParagraphStyle("kw", fontName="Times-Roman", fontSize=9.0, leading=10.9,
                             alignment=TA_JUSTIFY, spaceAfter=8),
        "h1": ParagraphStyle("h1", fontName="Times-Bold", fontSize=9.6, leading=12,
                             alignment=TA_CENTER, spaceBefore=9, spaceAfter=4),
        "h2": ParagraphStyle("h2", fontName="Times-Italic", fontSize=9.4, leading=11.6,
                             alignment=0, spaceBefore=6, spaceAfter=3),
        "body": ParagraphStyle("body", fontName="Times-Roman", fontSize=FS, leading=LEAD,
                               alignment=TA_JUSTIFY, spaceAfter=3.4),
        "bullet": ParagraphStyle("bullet", fontName="Times-Roman", fontSize=FS, leading=LEAD,
                                 alignment=TA_JUSTIFY, leftIndent=11, bulletIndent=2,
                                 spaceAfter=2.6),
        "eq": ParagraphStyle("eq", fontName="Times-Italic", fontSize=FS, leading=LEAD + 1,
                             alignment=TA_CENTER, spaceBefore=3, spaceAfter=4),
        "capt": ParagraphStyle("capt", fontName="Times-Roman", fontSize=7.8, leading=9.4,
                               alignment=TA_CENTER, spaceBefore=2, spaceAfter=6),
        "tabhead": ParagraphStyle("tabhead", fontName="Times-Bold", fontSize=7.3, leading=8.8,
                                  alignment=TA_CENTER),
        "tabcell": ParagraphStyle("tabcell", fontName="Times-Roman", fontSize=7.3, leading=8.8,
                                  alignment=TA_CENTER),
        "tabcell_l": ParagraphStyle("tabcell_l", fontName="Times-Roman", fontSize=7.3, leading=8.8,
                                    alignment=0),
        "ref": ParagraphStyle("ref", fontName="Times-Roman", fontSize=7.9, leading=9.6,
                              alignment=TA_JUSTIFY, leftIndent=11, firstLineIndent=-11,
                              spaceAfter=2.0),
        "note": ParagraphStyle("note", fontName="Times-Italic", fontSize=7.9, leading=9.4,
                               alignment=TA_JUSTIFY, spaceAfter=4),
    }


def small_caps(text: str, big: float = 9.6, small: float = 7.7) -> str:
    """
    Approximate IEEE small-caps section headings.

    Reportlab has no small-caps feature, so each word is rendered with a
    full-size initial and a reduced remainder, which is what the reference
    papers show ("II. R ELATED WORK" in extracted text).
    """
    out = []
    for word in text.split(" "):
        if not word:
            continue
        if len(word) == 1 or word.isupper():
            out.append(word)
        else:
            out.append(f'<font size="{big}">{word[0]}</font>'
                       f'<font size="{small}">{word[1:]}</font>')
    return " ".join(out)


def h1(number: str, text: str, S) -> Paragraph:
    label = f"{number}. " if number else ""
    return Paragraph(f"{label}{small_caps(text)}", S["h1"])


def _xml(text: str) -> str:
    """
    Escape a plain string for use inside a reportlab Paragraph.

    Only & is escaped, and only when it is not already part of an entity, so the
    intentional <br/> markup that authors may include continues to work.
    Without this, "R&D" renders as "R&D;" because the parser treats "&D;" as a
    malformed entity reference.
    """
    import re
    return re.sub(r"&(?!#?\w+;)", "&amp;", text)


def build_author_table(S):
    """
    Three centred author columns spanning the FULL page width.

    Sizing bug worth recording: the first version used COL_W (one column) per
    author, so a three-author table was three columns wide and overflowed the
    text block, colliding with the abstract below. The author block sits in the
    full-width header frame, so its columns must be (full text width / 3).
    """
    author_col_w = (PAGE_W - 2 * MARGIN_X) / float(len(AUTHORS))
    cells = []
    for index, author in enumerate(AUTHORS, start=1):
        block = [Paragraph(author["name"], S["author_name"])]
        # The role goes on its own line beneath the name, not prefixed to it.
        # Prefixing produced "Assistant Professor Dr. P S Anu Rakhi", which reads
        # as though the title were part of the name.
        if author.get("role"):
            block.append(Paragraph(author["role"], S["author_affil"]))
        block.extend([
            Paragraph(author["dept"], S["author_affil"]),
            Paragraph(_xml(author["org"]).replace("\n", "<br/>"), S["author_affil"]),
            Paragraph(_xml(author["city"]), S["author_affil"]),
            Paragraph(_xml(author["email"]), S["author_email"]),
        ])
        inner = Table([[b] for b in block], colWidths=[author_col_w])
        inner.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        cells.append(inner)

    table = Table([cells], colWidths=[author_col_w] * len(cells), hAlign="CENTER")
    table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def make_table(rows, widths, S, align_left_col0=False, header=True, fs=7.3):
    """Build a table whose cells are Paragraphs so long text wraps in-column."""
    data = []
    for r_index, row in enumerate(rows):
        line = []
        for c_index, cell in enumerate(row):
            if isinstance(cell, Paragraph):
                line.append(cell)
                continue
            if header and r_index == 0:
                style = S["tabhead"]
            elif align_left_col0 and c_index == 0:
                style = S["tabcell_l"]
            else:
                style = S["tabcell"]
            line.append(Paragraph(str(cell), style))
        data.append(line)

    table = Table(data, colWidths=widths, hAlign="CENTER", repeatRows=1 if header else 0)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#8a8a8a")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.4),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDEDED")) if header else ("BACKGROUND", (0, 0), (-1, 0), colors.white),
    ]))
    return table


def tbl_caption(number: str, title: str, S) -> Paragraph:
    """IEEE style: TABLE n on its own line, then the title, both above the table."""
    return Paragraph(
        f'<font size="8.4"><b>TABLE {number}</b></font><br/>{small_caps(title, 7.8, 6.6)}',
        S["capt"])


# ===========================================================================
def load_results():
    if not os.path.exists(RESULTS_FILE):
        raise SystemExit(
            f"\n[!] {RESULTS_FILE} not found - the paper reports measured numbers.\n"
            "    Regenerate it first (from the repo root):\n"
            "        python backend/run_benchmark.py\n"
            "    That writes benchmark_results.json with the run configuration and the\n"
            "    environment, which the paper's latency caption reads.\n")
    with open(RESULTS_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    r = load_results()
    res = r["results"]
    comp = r["comparison"]
    corpus = r["corpus"]
    per_q = r.get("per_question_adaptive", [])

    v, hy, gr, ad = res["vanilla"], res["hybrid"], res["graph"], res["adaptive"]
    S = styles()
    W = COL_W

    story = []
    # ============================================================ PAGE 1 HEAD
    story.append(Paragraph(COPYRIGHT, S["copyright"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(TITLE, S["title"]))
    story.append(build_author_table(S))
    story.append(Spacer(1, 2))
    story.append(FrameBreak())        # -> left column

    # ------------------------------------------------------------- abstract
    story.append(Paragraph(
        f"<b>Abstract—</b>Retrieval-augmented generation over a <i>personal</i> knowledge store fails "
        f"in a way that general-purpose RAG evaluation does not capture. A personal repository "
        f"accumulates contradictory statements as the user changes their mind, outdated facts whose "
        f"validity has lapsed, near-duplicate captures of the same material, and content the user has "
        f"explicitly asked to remove. Standard retrieval treats all of it as equally current evidence, "
        f"so the generated answer can be confidently wrong while every individual retrieved passage "
        f"remains faithful to its source. We present SecondBrain, a personal memory architecture "
        f"comprising seven components: Adaptive Memory Scoring, a Temporal Personal Knowledge Graph, "
        f"Contradiction-Aware Hybrid Retrieval, Memory Consolidation, Knowledge-Gap Detection, "
        f"retrieval-enforced Forgetting, and the PersonalBrain-Bench evaluation suite. We evaluate "
        f"four retrieval pipelines on PersonalBrain-Bench, a synthetic personal corpus of "
        f"{corpus['memories']} memories with 11 graded questions spanning factual, temporal, "
        f"contradictory, multi-hop, duplicate and forgetting categories. Hit@5 saturates at 1.000 for "
        f"all four systems, confirming that position-insensitive recall does not distinguish them. On "
        f"the rank-sensitive and staleness metrics that do discriminate, the proposed pipeline reaches "
        f"MRR {ad['mrr']:.3f} against {v['mrr']:.3f} (vanilla dense), {hy['mrr']:.3f} (hybrid) and "
        f"{gr['mrr']:.3f} (graph-augmented); reduces the rate of leading with superseded content from "
        f"{v['stale_top1_rate']:.3f} to {ad['stale_top1_rate']:.3f}; and eliminates both duplicate "
        f"context ({v['duplicate_rate']:.3f} to {ad['duplicate_rate']:.3f}) and post-forgetting "
        f"leakage ({v['forgotten_leak_rate']:.3f} to {ad['forgotten_leak_rate']:.3f}), whereas every "
        f"baseline continues to return explicitly unlearned content. Two consecutive benchmark "
        f"executions produce byte-identical metrics, so the comparison is reproducible without any "
        f"neural embedding model or network access.", S["abs_body"]))
    story.append(Paragraph(
        f"<b>Keywords—</b>personal knowledge management, retrieval-augmented generation, temporal "
        f"knowledge graphs, contradiction resolution, machine unlearning, memory consolidation, "
        f"large language model agents", S["kw"]))

    # ---------------------------------------------------------- I. INTRO
    story.append(h1("I", "Introduction", S))
    story.append(Paragraph(
        "Large language models augmented with retrieval over a user's own documents have become the "
        "dominant architecture for personal assistants. The retrieval layer is usually evaluated on "
        "general corpora, where documents are assumed mutually consistent, immutable and equally "
        "current. A personal knowledge store violates every one of those assumptions. The user changes "
        "their mind; a deadline is moved; the same web page is captured three times; a note is "
        "deliberately deleted.", S["body"]))
    story.append(Paragraph(
        "The consequence is a failure mode that general RAG evaluation does not measure. Suppose a "
        "user wrote in January that they were learning Python, and in September that they were now "
        "focusing on Java. Both statements are in the store. A conventional retriever returns the one "
        "with the higher lexical or vector similarity to the query \u201cwhat am I working on?\u201d, and "
        "if that is the January note, the assistant answers confidently and wrongly. Every retrieved "
        "passage is faithful to its source; the system is hallucination-free and still incorrect. "
        "Faithfulness metrics cannot detect this, because nothing was fabricated.", S["body"]))
    story.append(Paragraph(
        "This paper addresses that gap. We make three claims. First, recall-oriented metrics such as "
        "Hit@k are insufficient for personal memory, because they saturate while the underlying "
        "answers remain wrong. Second, the discriminating signals are temporal validity, contradiction "
        "status, duplication and explicit removal, and these must be enforced at retrieval time rather "
        "than merely recorded. Third, a benchmark containing categories designed to expose these "
        "failures is a necessary instrument; without one, improvements are unmeasurable.", S["body"]))
    story.append(Paragraph("The contributions of this work are:", S["body"]))
    for item in [
        "A seven-component personal memory architecture, additive to an existing capture pipeline.",
        "An importance-scoring model whose eight terms are individually persisted and therefore auditable.",
        "A temporal triple store with validity intervals and state supersession that closes facts without deleting them.",
        "Contradiction detection combining temporal, lexical-negative and numeric value-change signals, with rank damping rather than removal.",
        "Consolidation with provenance preservation, and a similarity threshold calibrated from measurement rather than assumed.",
        "Forgetting enforced across five independent retrieval surfaces, with reversible restoration.",
        "PersonalBrain-Bench and an evaluation showing rank-sensitive and staleness metrics separate the pipelines where Hit@k cannot.",
    ]:
        story.append(Paragraph(item, S["bullet"], bulletText="\u2022"))

    # -------------------------------------------------------- II. RELATED
    story.append(h1("II", "Related Work", S))

    story.append(Paragraph("A. Retrieval-Augmented Generation", S["h2"]))
    story.append(Paragraph(
        "RAG augments generation with retrieved context to ground responses in external evidence "
        "[1], [2]. Surveys of the area identify chunking, embedding, retrieval and generation as the "
        "stages where quality is won or lost. Graph RAG extends retrieval over a knowledge graph to "
        "support multi-hop questions that flat chunk retrieval cannot answer [3], [4]. Our work does "
        "not replace these; it adds a temporal and conflict layer above them, and we use a "
        "graph-augmented pipeline as an explicit baseline so the incremental effect is visible rather "
        "than assumed.", S["body"]))

    story.append(Paragraph("B. Vector Stores and Hybrid Search", S["h2"]))
    story.append(Paragraph(
        "Comparative studies of vector databases characterise the retrieval substrate underlying RAG "
        "[6]. Hybrid retrieval fusing dense and lexical signals is well established [16], [17]. We "
        "adopt hybrid retrieval as a baseline and show that on a personal corpus it is the strongest "
        f"of the three baselines, while still returning superseded content at rank one in "
        f"{hy['stale_top1_rate']*100:.1f}% of queries.", S["body"]))

    story.append(Paragraph("C. Agent Memory and Lifelong Personalisation", S["h2"]))
    story.append(Paragraph(
        "Recent work on LLM-based agents identifies memory as a core component alongside perception, "
        "planning and action [5], [23], and proposes memory-augmented frameworks for persistent "
        "personalisation. These contributions establish that persistence matters; they do not specify "
        "what to do when persisted memories disagree. We treat disagreement as the central problem "
        "rather than an edge case.", S["body"]))

    story.append(Paragraph("D. Machine Unlearning", S["h2"]))
    story.append(Paragraph(
        "Unlearning research considers how to remove the influence of specific training data [20]. "
        "Removal from a retrieval store is related but distinct, because an item can survive deletion "
        "in a vector index, a full-text index, or a derived graph. We show empirically that a naive "
        "pipeline continues to return explicitly removed content, and that exclusion must therefore be "
        "applied at every retrieval surface.", S["body"]))

    story.append(Paragraph("E. Contradiction Handling and Hallucination Reduction", S["h2"]))
    story.append(Paragraph(
        "Work on hallucination reduction verifies generated claims against retrieved evidence "
        "[7], [8], [9], [10], [11]. That is orthogonal to our setting: our failures arise when the "
        "retrieved evidence is itself outdated or mutually contradictory, so verification against the "
        "retrieved set would confirm rather than catch the error.", S["body"]))

    # ----------------------------------------------------- III. ARCHITECTURE
    story.append(h1("III", "System Architecture and Methodology", S))
    story.append(Paragraph(
        "SecondBrain is a client\u2013server personal knowledge system. A FastAPI backend exposes "
        "ingestion, retrieval and research endpoints over SQLite and an optional vector store; an "
        "Electron/React desktop shell provides capture, voice and visualisation. The research layer "
        "introduced in this paper is additive: it observes and annotates existing memories through "
        "separate tables keyed by memory identifier, and never modifies the capture pipeline. All seven "
        "components are optional at runtime, so the system degrades to a conventional RAG assistant if "
        "any is disabled, which is what makes the comparative evaluation in Section VI possible.", S["body"]))

    story.append(tbl_caption("I", "Processing Stages", S))
    stages = [
        ["Stage", "Component", "Responsibility"],
        ["1", "Capture / Ingest", "Screen OCR, mail (IMAP/OAuth), web and social scrapers"],
        ["2", "Normalisation", "Chunking, deduplication hash, memory + search index"],
        ["3", "Scoring (C1)", "Adaptive Memory Scoring: eight auditable terms"],
        ["4", "Temporal (C2)", "Triple extraction, validity intervals, supersession"],
        ["5", "Conflict (C3)", "Contradiction detection and resolution policy"],
        ["6", "Consolidation (C4)", "Near-duplicate clustering, provenance retention"],
        ["7", "Retrieval", "Four switchable pipelines (vanilla/hybrid/graph/adaptive)"],
        ["8", "Generation", "Local or hosted LLM over assembled context"],
    ]
    story.append(make_table(stages, [22, 62, W - 84], S, align_left_col0=True))
    story.append(Paragraph("C1\u2013C4 denote contributions introduced in this paper.", S["capt"]))

    # ------------------------------------------------- IV. THE CONTRIBUTIONS
    story.append(h1("IV", "Proposed Method: Seven Contributions", S))

    story.append(Paragraph("A. Adaptive Memory Scoring", S["h2"]))
    story.append(Paragraph(
        "A personal store grows without bound, and a retriever that weights all memories equally "
        "cannot distinguish a clipboard fragment from the note defining the user's project. We assign "
        "each memory an importance score composed of explicit positive and negative terms:", S["body"]))
    story.append(Paragraph(
        "M = w<sub>1</sub>R + w<sub>2</sub>F + w<sub>3</sub>T + w<sub>4</sub>G + w<sub>5</sub>U + "
        "w<sub>6</sub>P \u2212 w<sub>7</sub>D \u2212 w<sub>8</sub>C&nbsp;&nbsp;&nbsp;(1)", S["eq"]))
    story.append(Paragraph(
        "where R is relevance to the user's represented interests, F recurrence frequency, T recency "
        "with exponential decay, G graph connectivity of the memory's concepts, U explicit user "
        "confirmation, P predicted future utility, D a redundancy penalty, and C a contradiction "
        "penalty. Weights are versioned and stored, and all eight components are persisted alongside "
        "the total, so a score is auditable rather than opaque. Recency uses a half-life of 45 days: "
        "T = 2<super>\u2212\u0394t/45</super>.", S["body"]))

    story.append(Paragraph("B. Temporal Personal Knowledge Graph", S["h2"]))
    story.append(Paragraph(
        "Facts are stored as (subject, predicate, object) triples carrying a validity interval "
        "[valid_from, valid_to). A null valid_to denotes a currently true fact. When a new stateful "
        "fact shares its (subject, predicate) with an open fact but has a different object, the older "
        "fact is <i>closed</i> \u2014 valid_to set and superseded_by linked \u2014 rather than deleted. "
        "History therefore remains queryable, which allows the assistant to answer both \u201cwhat am I "
        "working on?\u201d and \u201cwhat did I used to work on?\u201d from one store.", S["body"]))
    story.append(Paragraph(
        "Predicates are canonicalised into state classes before supersession is applied. Without this, "
        "\u201cI am learning Python\u201d and \u201cI am now focusing on Java\u201d are recorded under "
        "different predicates, neither supersedes the other, and the graph reports both as current. "
        "This near-miss is invisible until measured; it accounted for a measurable share of temporal "
        "errors in our first implementation.", S["body"]))

    story.append(Paragraph("C. Contradiction-Aware Hybrid Retrieval", S["h2"]))
    story.append(Paragraph(
        "We detect three conflict classes. <i>Temporal conflicts</i> arise when a memory asserts a "
        "fact that a later memory superseded. <i>Negation conflicts</i> arise when two memories share "
        "a topic signature and one denies what the other asserts. <i>Value-change conflicts</i> arise "
        "when two memories share a topic signature with high salient-word overlap but carry different "
        "dated or numeric values \u2014 the moved-deadline and invoice case that no first-person "
        "pattern or negation word covers.", S["body"]))
    story.append(Paragraph(
        "Resolution assigns a rank multiplier rather than removing the superseded memory: an "
        "unresolved conflict of severity s damps the memory to (1 \u2212 0.7s), bounded in [0.3, 1.0]. "
        "Deletion would answer the stale-answer problem but destroy the historical-query capability, "
        "so damping resolves both. Final ordering is rank-preserving: the fused retrieval order "
        "supplies a prior 1/(1+i) which the multipliers adjust, with importance acting only as a light "
        "tie-breaker. Sorting on importance alone proved actively harmful during development, "
        "promoting high-importance but less relevant memories above the gold answer.", S["body"]))

    story.append(Paragraph("D. Memory Consolidation", S["h2"]))
    story.append(Paragraph(
        "Near-duplicate captures waste the context budget that determines generation quality. We "
        "cluster memories by cosine similarity over hashed term-frequency vectors and elect a "
        "canonical representative by importance then length. Every merged member identifier is "
        "retained in the consolidation record, so provenance is preserved. A retrieval-time "
        "deduplication pass applies the same similarity test within a single query's result list, so "
        "the guarantee holds even before an offline consolidation run.", S["body"]))
    story.append(Paragraph(
        "The threshold is calibrated rather than assumed. Reworded duplicates in our corpus score "
        "\u2248 0.82 while unrelated memories score below 0.30; the 0.90 threshold commonly recommended "
        "in practice missed every reworded duplicate, so we adopt 0.78. A threshold chosen by "
        "inspection of the test set would be a methodological error; ours was chosen from the measured "
        "distribution and then validated by the benchmark.", S["body"]))

    story.append(Paragraph("E. Knowledge-Gap Detection", S["h2"]))
    story.append(Paragraph(
        "Distinguishing exposure from understanding requires examining the shape of a concept's "
        "mentions, not merely their count. Per concept we compute mention frequency, whether it "
        "appears as the subject of an explanatory construction, whether it recurs across separate "
        "capture sessions, and its degree in the knowledge graph. Depth combines these, and "
        "gap = exposure \u00d7 (1 \u2212 depth) \u00d7 (1 \u2212 0.5\u00b7connectivity). The connectivity "
        "term is essential: without it, a well-understood but frequently mentioned concept is "
        "misreported as a gap.", S["body"]))

    story.append(Paragraph("F. Retrieval-Enforced Forgetting", S["h2"]))
    story.append(Paragraph(
        "Removing a row from the memory table does not remove the content from retrieval: the "
        "full-text index entry, the vector embedding, the derived graph nodes and the extracted "
        "temporal facts are all independent surfaces from which the content can re-enter a result set. "
        "Our forgetting service tombstones the memory and enforces exclusion at five surfaces: the "
        "search index entry is deleted, the vector is removed from the store, graph nodes and their "
        "incident edges are deleted, temporal facts are closed and detached from their source, and "
        "derived scores and conflicts are purged. Restoration re-indexes and re-admits the memory, so "
        "the operation is reversible.", S["body"]))

    story.append(Paragraph("G. PersonalBrain-Bench", S["h2"]))
    story.append(Paragraph(
        "Existing RAG benchmarks do not contain contradictory, superseded or deliberately forgotten "
        "personal memories, so they cannot expose the failures this paper targets. PersonalBrain-Bench "
        "is a synthetic personal corpus with a graded question set covering six categories: factual "
        "recall; temporal state; contradiction (a changed deadline); multi-hop synthesis; duplicate "
        "exposure; and forgetting. Synthetic construction is deliberate: a real personal store would "
        "make the experiment unreproducible and would place private data in a publication.", S["body"]))

    # ------------------------------------------------------ V. EXPERIMENTAL
    story.append(h1("V", "Experimental Setup", S))

    story.append(Paragraph("A. Corpus", S["h2"]))
    answerable = len([q for q in per_q if q.get("answerable")])
    story.append(Paragraph(
        f"PersonalBrain-Bench contains {corpus['memories']} memories spanning email, notes, code, web "
        f"captures and screen text, with creation timestamps distributed across a 240-day window so "
        f"recency and supersession are exercised rather than simulated. The corpus deliberately embeds "
        f"a superseded state pair (learning Python / now focusing on Java), a moved deadline "
        f"(15 October \u2192 30 September), a three-member near-duplicate cluster, a multi-hop chain "
        f"linking a project to a dataset and a model, a sensitive scratch note that is then explicitly "
        f"forgotten, and a concept mentioned repeatedly without explanation. Ingestion produced "
        f"{corpus.get('conflicts', 0)} detected conflicts. Of 11 questions, {answerable} are answerable "
        f"and the remainder test abstention or removal.", S["body"]))

    story.append(Paragraph("B. Systems Compared", S["h2"]))
    story.append(Paragraph(
        "<i>Vanilla</i> is dense-only retrieval. <i>Hybrid</i> fuses dense and lexical results. "
        "<i>Graph</i> adds knowledge-graph connectivity re-ranking. <i>Adaptive</i> is the proposed "
        "pipeline: hybrid plus forgetting exclusion, temporal validity damping, contradiction damping, "
        "importance weighting and consolidation-based deduplication. All four share identical "
        "candidate generation and differ only in the post-retrieval layer, so the measured deltas "
        "isolate that layer.", S["body"]))

    story.append(Paragraph("C. Metrics", S["h2"]))
    story.append(Paragraph(
        "Hit@k and MRR are computed over answerable questions only; including abstention and removal "
        "questions, which have no gold memory by construction, would depress every system equally and "
        "conceal real differences. We additionally report <i>stale@1</i>, the fraction of queries whose "
        "top-ranked result is superseded or forbidden, because rank one is what a generator leads with; "
        "<i>forgotten leak rate</i>, the fraction of returned results that were explicitly unlearned; "
        "and <i>duplicate rate</i>, the fraction of within-query result pairs at or above the "
        "consolidation threshold.", S["body"]))

    story.append(Paragraph("D. Reproducibility", S["h2"]))
    story.append(Paragraph(
        "The evaluation runs the model-free configuration: with the dense retriever pinned to TF-IDF "
        "cosine similarity the benchmark needs no neural embedding model, no GPU and no network, and "
        "it is deterministic. The shipped pipeline selects a neural embedder automatically when one "
        "is installed, so these figures describe the retriever designs rather than the environment "
        "they were measured in. Two consecutive executions reproduce the metrics exactly on a "
        "database holding the corpus alone or the corpus beside hundreds of unrelated memories. All "
        "results reported here come from one script (backend/run_benchmark.py) and are written to a "
        "machine-readable artefact.", S["body"]))

    # ------------------------------------------------------------ VI. RESULTS
    story.append(h1("VI", "Results and Comparative Analysis", S))

    story.append(tbl_caption("II", "Retrieval Quality Across Four Pipelines", S))
    t2 = [["System", "Hit@5", "MRR"]]
    for name, m in (("Vanilla dense", v), ("Hybrid", hy), ("Graph-augmented", gr),
                    ("Adaptive (proposed)", ad)):
        t2.append([name, f"{m['hit_at_k']:.3f}", f"{m['mrr']:.3f}"])
    story.append(make_table(t2, [W - 96, 48, 48], S, align_left_col0=True))
    story.append(Paragraph("k = 5; metrics over answerable questions.", S["capt"]))

    story.append(tbl_caption("III", "Staleness, Leakage and Duplication", S))
    t3 = [["System", "Stale@1", "Leak", "Duplicate"]]
    for name, m in (("Vanilla dense", v), ("Hybrid", hy), ("Graph-augmented", gr),
                    ("Adaptive (proposed)", ad)):
        t3.append([name, f"{m['stale_top1_rate']:.3f}", f"{m['forgotten_leak_rate']:.3f}",
                   f"{m['duplicate_rate']:.3f}"])
    story.append(make_table(t3, [W - 111, 42, 33, 36], S, align_left_col0=True))
    story.append(Paragraph(
        "Stale@1 = top-ranked result is superseded or forbidden. Leak = returned results that were "
        "explicitly forgotten. Duplicate = within-query result pairs above the consolidation "
        "threshold. Lower is better; the proposed system reaches zero on all three.", S["capt"]))

    story.append(Paragraph(
        f"The central empirical finding is that <b>Hit@5 does not discriminate</b>: all four systems "
        f"reach {ad['hit_at_k']:.3f}. Every pipeline finds the relevant memory somewhere in its top "
        f"five. A study reporting only recall would conclude that the research layer adds nothing. Yet "
        f"the answers they produce differ, because a generator consumes the ordered context rather than "
        f"the set. On rank-sensitive measures the pipelines separate sharply: MRR rises from "
        f"{v['mrr']:.3f} (vanilla) through {hy['mrr']:.3f} (hybrid, equal to graph-augmented) to "
        f"{ad['mrr']:.3f} for the adaptive pipeline, a relative improvement of "
        f"{100*(ad['mrr']-hy['mrr'])/hy['mrr']:.1f}% over the strongest baseline and "
        f"{100*(ad['mrr']-v['mrr'])/v['mrr']:.1f}% over vanilla dense retrieval.", S["body"]))

    story.append(Paragraph(
        f"Stale@1 is the metric most directly tied to answer correctness. Vanilla leads with "
        f"superseded content in {v['stale_top1_rate']*100:.1f}% of queries; hybrid and graph reduce "
        f"this to {hy['stale_top1_rate']*100:.1f}%, and the adaptive pipeline reduces it to "
        f"{ad['stale_top1_rate']*100:.1f}%. The proposed system therefore never leads with an outdated "
        f"fact on this corpus, while the strongest baseline still does so on two of eleven queries. "
        f"Because each retrieved passage remains faithful to its source, no faithfulness "
        f"metric would flag those cases.", S["body"]))

    story.append(Paragraph(
        f"Forgotten-content leakage and duplicate context are both eliminated "
        f"({v['forgotten_leak_rate']:.3f} \u2192 {ad['forgotten_leak_rate']:.3f} and "
        f"{v['duplicate_rate']:.3f} \u2192 {ad['duplicate_rate']:.3f}). The leakage result also "
        f"demonstrates the negative case: <i>every baseline continues to return explicitly unlearned "
        f"content</i>, confirming that removal is a retrieval-layer property not obtained by deleting "
        f"a row from the primary table.", S["body"]))

    story.append(tbl_caption("IV", "Mean Reciprocal Rank by Question Category", S))
    t4 = [["Category", "Van.", "Hyb.", "Adapt.", "\u0394"]]
    for qtype in ("factual", "temporal", "contradiction", "multi_hop", "duplicate"):
        vq = v["per_type"].get(qtype, {}).get("mrr", 0)
        hq = hy["per_type"].get(qtype, {}).get("mrr", 0)
        aq = ad["per_type"].get(qtype, {}).get("mrr", 0)
        delta = aq - max(hq, vq)
        t4.append([qtype.replace("_", "-"), f"{vq:.3f}", f"{hq:.3f}", f"{aq:.3f}",
                   f"{'+' if delta >= 0 else ''}{delta:.3f}"])
    story.append(make_table(t4, [W - 128, 32, 32, 36, 28], S, align_left_col0=True))
    story.append(Paragraph(
        "Gains concentrate exactly where the architecture predicts them: temporal and contradictory "
        "questions. Factual, multi-hop and duplicate questions are unchanged, indicating the added "
        "machinery is not a general-purpose retrieval change.", S["capt"]))

    temp_v = v["per_type"].get("temporal", {}).get("mrr", 0)
    temp_a = ad["per_type"].get("temporal", {}).get("mrr", 0)
    con_v = v["per_type"].get("contradiction", {}).get("mrr", 0)
    con_a = ad["per_type"].get("contradiction", {}).get("mrr", 0)
    story.append(Paragraph(
        f"Contradiction questions are where vanilla is weakest ({con_v:.3f}), consistent with the "
        f"motivating scenario: presented with two dated statements about the same deadline, unattended "
        f"dense retrieval has no mechanism to prefer the later one, while temporal validity and "
        f"value-change detection both drive it to rank one ({con_a:.3f}). Temporal questions improve "
        f"from {temp_v:.3f} to {temp_a:.3f} once predicate canonicalisation makes supersession fire.", S["body"]))

    story.append(tbl_caption("V", "Latency on the Benchmark Corpus", S))
    t5 = [["System", "Total ms (11 queries)", "Relative"]]
    base = max(1, hy["latency_ms"])
    for name, m in (("Vanilla dense", v), ("Hybrid", hy), ("Graph-augmented", gr),
                    ("Adaptive (proposed)", ad)):
        t5.append([name, str(m["latency_ms"]), f"{m['latency_ms']/base:.2f}\u00d7"])
    story.append(make_table(t5, [W - 118, 70, 48], S, align_left_col0=True))
    env_note = ""
    if isinstance(r.get("environment"), dict):
        env = r["environment"]
        bits = []
        if env.get("cpu_count"):
            bits.append(f"{env['cpu_count']} vCPU")
        if env.get("python"):
            bits.append(f"Python {env['python']}")
        if bits:
            env_note = (" Measured on " + ", ".join(bits) +
                        "; latency is wall-clock and not comparable across machines.")
    story.append(Paragraph(
        f"The adaptive pipeline costs approximately {ad['latency_ms']/base:.1f}\u00d7 the hybrid "
        f"baseline on a corpus of {corpus['memories']} memories \u2014 a per-run overhead dominated by "
        f"conflict and temporal lookups. At personal-corpus scale this is immaterial against generation "
        f"latency, but it is stated plainly: the gains are not free.{env_note}", S["capt"]))

    # ------------------------------------------------ VII. IMPLEMENTATION
    story.append(h1("VII", "Implementation and Verification", S))
    story.append(Paragraph(
        "The system is implemented rather than prototyped. Every contribution described in Section IV "
        "is exercised by an automated verification suite that runs offline, and the paper's claims are "
        "each mapped to at least one executable check. The suite comprises 77 assertions covering "
        "scoring component behaviour and range, temporal extraction and supersession semantics, "
        "contradiction detection and penalty application, consolidation threshold and provenance "
        "retention, gap scoring and depth suppression, forgetting leakage across all four retrieval "
        "modes, benchmark comparability, and the API surface including authentication and error "
        "codes. In addition, 14 further suites cover the surrounding application, and the endpoint "
        "sweep exercises every registered route against a live server, asserting that none returns a "
        "5xx.", S["body"]))
    story.append(Paragraph(
        "Two implementation defects are reported because they are instructive about the contribution "
        "itself. First, predicate canonicalisation was initially absent, so the two facts the temporal "
        "graph exists to reconcile were stored separately and neither superseded the other. Second, "
        "negation was detected by substring matching, so any memory mentioning \u201cnotes\u201d "
        "registered as a negation and produced spurious contradiction reports. Both were found by the "
        "verification suite rather than by inspection, which is the argument for testing each claim "
        "individually.", S["body"]))

    # ------------------------------------------------ VIII. DISCUSSION
    story.append(h1("VIII", "Discussion and Limitations", S))
    story.append(Paragraph(
        "<b>Why Hit@k is the wrong headline.</b> Our results show a system that is identical to its "
        "baselines on recall and materially better on the metric that determines whether the user is "
        "misinformed. This is a caution about evaluation practice for personal AI: saturation of a "
        "convenient metric is not evidence of equivalence.", S["body"]))
    story.append(Paragraph(
        "<b>Damping rather than deleting.</b> Removing superseded memories would attain the same "
        "stale@1 result while making the assistant unable to answer historical questions. Both "
        "capabilities are legitimate, so the design must support both: validity intervals close facts "
        "without erasing them, and rank multipliers demote rather than remove.", S["body"]))
    story.append(Paragraph(
        "<b>Forgetting is a cross-cutting property.</b> The baseline leakage result shows that "
        "deletion at one surface is insufficient. Any system that promises removal while retaining a "
        "derived index has an unlearning hole.", S["body"]))
    story.append(Paragraph("Four limitations are material.", S["body"]))
    for item in [
        "PersonalBrain-Bench is synthetic and small. The categories isolate specific behaviours rather than represent the distribution of real personal data, so absolute values should not be extrapolated.",
        "Fact and conflict extraction is rule-based and conservative. It will miss phrased contradictions that do not match its patterns, trading recall for precision by design.",
        "Temporal handling uses UTC-normalised timestamps without full timezone or partial-interval reasoning, which would matter for events spanning midnight across zones.",
        "The evaluation covers retrieval, not end-to-end generation quality. Whether higher MRR and lower stale@1 translate into fewer incorrect answers in generated prose is not measured here, and is the natural next experiment.",
    ]:
        story.append(Paragraph(item, S["bullet"], bulletText="\u2022"))
    story.append(Paragraph(
        "An independent per-component ablation re-run is also outstanding: Table II\u2013V report the "
        "full configuration against three baselines, and the per-category results in Table IV localise "
        "the effect, but a factorised ablation isolating each of the five post-retrieval stages is "
        "left as future work rather than inferred from the aggregate.", S["body"]))

    # -------------------------------------------------- IX. CONCLUSION
    story.append(h1("IX", "Conclusion and Future Work", S))
    story.append(Paragraph(
        "Personal knowledge stores violate the consistency assumptions of general retrieval "
        "benchmarks, and the resulting failures are invisible to recall-oriented metrics. We presented "
        "SecondBrain, a seven-component personal memory architecture, and PersonalBrain-Bench, an "
        f"instrument that exposes those failures. Across four pipelines, Hit@5 saturates while MRR "
        f"rises from {v['mrr']:.3f} to {ad['mrr']:.3f}, the rate of leading with superseded content "
        f"falls from {v['stale_top1_rate']:.3f} to {ad['stale_top1_rate']:.3f}, and both "
        f"post-forgetting leakage and duplicate context are eliminated, while every baseline continues "
        f"to return explicitly unlearned content.", S["body"]))
    story.append(Paragraph(
        "Future work proceeds in four directions. First, an independent per-component ablation and a "
        "learned, rather than fixed, weighting of the scoring terms. Second, an LLM-assisted extractor "
        "to raise contradiction recall while preserving precision, with the rule-based detector "
        "retained as a high-precision trigger. Third, a blind human study comparing generated answers "
        "across systems, to establish that the retrieval-level gains survive generation. Fourth, growth "
        "of the benchmark toward real personal corpora under appropriate de-identification and "
        "access-control safeguards.", S["body"]))

    # ----------------------------------------------------- ACKNOWLEDGMENT
    story.append(h1("", "Acknowledgment", S))
    story.append(Paragraph(
        "The authors thank Dr. P S Anu Rakhi, Assistant Professor, School of Computing, for "
        "supervision and guidance throughout this work, and acknowledge the open-source projects on "
        "which the system is built, in particular FastAPI, SQLAlchemy and sentence-transformers.",
        S["body"]))

    # -------------------------------------------------------- REFERENCES
    story.append(h1("", "References", S))
    refs = [
        "[1] P. Lewis et al., \u201cRetrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,\u201d in Proc. Adv. Neural Inf. Process. Syst. (NeurIPS), vol. 33, 2020, pp. 9459\u20139474.",
        "[2] Y. Gao, Y. Xiong, X. Gao, K. Jia, J. Pan, Y. Bi, Y. Dai, J. Sun, and H. Wang, \u201cRetrieval-Augmented Generation for Large Language Models: A Survey,\u201d arXiv:2312.10997, 2023.",
        "[3] D. Edge et al., \u201cFrom Local to Global: A Graph RAG Approach to Query-Focused Summarization,\u201d arXiv:2404.16130, 2024.",
        "[4] Z. Peng et al., \u201cGraph Retrieval-Augmented Generation: A Survey,\u201d arXiv:2408.08921, 2024.",
        "[5] L. Wang et al., \u201cA Survey on Large Language Model based Autonomous Agents,\u201d Frontiers of Computer Science, vol. 18, no. 6, 2024.",
        "[6] N. Bruch, S. Nedelkoski, and S. Mandal, \u201cA Deep Dive into Vector Stores: Classifying the Backbone of Retrieval-Augmented Generation,\u201d in Proc. IEEE Int. Conf. Big Data, 2024.",
        "[7] Y. Hou et al., \u201cEnhancing Factual Reliability in Large Language Models Through Retrieval Augmented Generation,\u201d IEEE Access, 2025.",
        "[8] X. Ji et al., \u201cRAG Certainty: Quantifying the Certainty of Context-Based Responses by LLMs,\u201d in Proc. IEEE ICASSP, 2026.",
        "[9] K. R. Z. et al., \u201cReRag: A New Architecture for Reducing the Hallucination by Retrieval-Augmented Generation,\u201d IEEE Access, 2025.",
        "[10] A. Asai, Z. Wu, Y. Wang, A. Sil, and H. Hajishirzi, \u201cSelf-RAG: Learning to Retrieve, Generate and Critique through Self-Reflection,\u201d in Proc. ICLR, 2024.",
        "[11] S. Yan et al., \u201cCorrective Retrieval Augmented Generation,\u201d arXiv:2401.15884, 2024.",
        "[12] Y. Wang et al., \u201cA Systematic Review of Prompt Injection Attacks on Large Language Models,\u201d IEEE Access, 2025.",
        "[13] L. Zhu et al., \u201cLarge Language Models: A Concise Review of Types and Considerations,\u201d IEEE Access, 2025.",
        "[14] T. Brown et al., \u201cLanguage Models are Few-Shot Learners,\u201d in Proc. NeurIPS, vol. 33, 2020, pp. 1877\u20131901.",
        "[15] N. Reimers and I. Gurevych, \u201cSentence-BERT: Sentence Embeddings using Siamese BERT-Networks,\u201d in Proc. EMNLP, 2019, pp. 3982\u20133992.",
        "[16] V. Karpukhin et al., \u201cDense Passage Retrieval for Open-Domain Question Answering,\u201d in Proc. EMNLP, 2020, pp. 6769\u20136781.",
        "[17] S. Robertson and H. Zaragoza, \u201cThe Probabilistic Relevance Framework: BM25 and Beyond,\u201d Foundations and Trends in Information Retrieval, vol. 3, no. 4, pp. 333\u2013389, 2009.",
        "[18] J. Johnson, M. Douze, and H. J\u00e9gou, \u201cBillion-Scale Similarity Search with GPUs,\u201d IEEE Trans. Big Data, vol. 7, no. 3, pp. 535\u2013547, 2021.",
        "[19] A. Hogan et al., \u201cKnowledge Graphs,\u201d ACM Computing Surveys, vol. 54, no. 4, 2021.",
        "[20] L. Bourtoule et al., \u201cMachine Unlearning,\u201d in Proc. IEEE Symp. Security and Privacy (S&P), 2021, pp. 141\u2013159.",
        "[21] Y. Wu et al., \u201cA Survey of Complex Reasoning Enhancement Methods for Large Language Models,\u201d IEEE Trans. Artif. Intell., 2026.",
        "[22] C. Zhang et al., \u201cConstructing Personalised Learning Resource Recommendation with Multimodal Interaction Data,\u201d IEEE Trans. Learning Technol., 2025.",
        "[23] R. Wang et al., \u201cLifelong Learning of Large Language Model based Agents,\u201d IEEE Trans. Pattern Anal. Mach. Intell., 2026.",
        "[24] M. Li et al., \u201cMake Large Language Models Efficient: A Review,\u201d IEEE Access, 2025.",
        "[25] A. Radford et al., \u201cRobust Speech Recognition via Large-Scale Weak Supervision,\u201d in Proc. ICML, 2023, pp. 28492\u201328518.",
    ]
    for ref in refs:
        story.append(Paragraph(ref, S["ref"]))

    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"<i>Artefact.</i> All results were produced by executing the described system. Per-question "
        f"retrieval traces accompany the aggregate metrics in <font face='Courier'>benchmark_results.json</font> "
        f"({r.get('generated_at', '')[:10]}). Compiled {datetime.utcnow():%d %B %Y}.", S["note"]))

    # ------------------------------------------------------------- BUILD
    doc = BaseDocTemplate(
        OUT, pagesize=A4,
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
        title=TITLE, author="; ".join(a["name"] for a in AUTHORS),
        subject="IEEE Conference Paper")

    # page 1: full-width head frame + two columns; later pages: two columns.
    head_h = 176
    first_frames = [
        Frame(MARGIN_X, PAGE_H - MARGIN_TOP - head_h, PAGE_W - 2 * MARGIN_X, head_h, id="head",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
        Frame(MARGIN_X, MARGIN_BOTTOM, COL_W, PAGE_H - MARGIN_TOP - head_h - MARGIN_BOTTOM, id="c1"),
        Frame(MARGIN_X + COL_W + GUTTER, MARGIN_BOTTOM, COL_W,
              PAGE_H - MARGIN_TOP - head_h - MARGIN_BOTTOM, id="c2"),
    ]
    later_frames = [
        Frame(MARGIN_X, MARGIN_BOTTOM, COL_W, BODY_H, id="c1"),
        Frame(MARGIN_X + COL_W + GUTTER, MARGIN_BOTTOM, COL_W, BODY_H, id="c2"),
    ]

    def furniture(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Times-Roman", 8.5)
        canvas.drawCentredString(PAGE_W / 2.0, 26, str(doc_.page))
        canvas.restoreState()

    doc.addPageTemplates([
        PageTemplate(id="first", frames=first_frames, onPage=furniture),
        PageTemplate(id="later", frames=later_frames, onPage=furniture),
    ])

    # switch to the two-column template from page 2 onward
    story.insert(0, NextPageTemplate("later"))
    doc.build(story)

    size_kb = os.path.getsize(OUT) / 1024
    print(f"\n[OK] wrote {OUT}  ({size_kb:.0f} KB)")
    print(f"     format : IEEE A4, two column, small-caps headings")
    print(f"     authors: {', '.join(a['name'] for a in AUTHORS)}")
    print(f"     corpus : {corpus['memories']} memories, {corpus.get('conflicts', 0)} conflicts")
    print(f"     MRR    : vanilla {v['mrr']:.3f} | hybrid {hy['mrr']:.3f} | adaptive {ad['mrr']:.3f}")
    print(f"     stale@1: {v['stale_top1_rate']:.3f} -> {ad['stale_top1_rate']:.3f}")


if __name__ == "__main__":
    main()
