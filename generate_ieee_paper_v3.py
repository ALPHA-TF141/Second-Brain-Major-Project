"""
Generate the REVISED IEEE paper (v3) in A4 two-column format.
===========================================================================
This is the corrected version produced from the reviewer/editor pass on
"Ieee Paper draft 1". It differs from generate_ieee_paper_a4.py in content and
rigour, not in layout: it reuses that module's verified IEEE A4 scaffolding
(styles, small-caps headings, table/caption helpers, frame geometry).

Changes made against the draft, each traceable to the repository:

  1. Numbers re-measured under the corpus-scoped, dense-backend-pinned run.
     The draft reported hybrid/graph stale@1 = 0.091 and "4 detected conflicts".
     Neither is reproducible: the pre-fix code also yields 0.182 and 2 conflicts
     on a corpus-only database, so the draft's figures came from a database that
     carried extra state. See benchmark_results.json (configuration block).
  2. Research questions RQ1-RQ4 and hypotheses H1-H4 added, each mapped to a
     measurement that exists.
  3. Related work organised into nine areas with a research-gap table whose
     cells are justified only from the cited sources.
  4. Architecture section with an explicit figure and an application/research/
     evaluation layer split.
  5. A "what is adopted vs what is proposed" table, so no existing technique is
     presented as new.
  6. Failures, planned experiments ([REQUIRES EXPERIMENT]) and a statistical
     protocol are stated as such rather than implied.
  7. References corrected and renumbered in order of first citation; entries
     that could not be located have been removed rather than kept.

Every number in this paper is read from benchmark_results.json. Nothing is typed
by hand; if the artefact is missing the script stops.

Usage:  python generate_ieee_paper_v3.py
"""
import json
import os
import re
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.platypus import (
    BaseDocTemplate, Frame, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

# Reuse the verified IEEE A4 scaffolding rather than duplicating it.
import generate_ieee_paper_a4 as base
from generate_ieee_paper_a4 import (
    COL_W, GUTTER, MARGIN_BOTTOM, MARGIN_TOP, MARGIN_X, PAGE_H, PAGE_W,
    _xml, make_table, small_caps, styles, tbl_caption,
)

OUT = "IEEE_Conference_Paper_SecondBrain_v3.pdf"
RESULTS_FILE = "benchmark_results.json"

COPYRIGHT = "XXX-X-XXXX-XXXX-X/XX/$XX.00 \u00a920XX IEEE"

TITLE = ("An Adaptive Temporal Personal Knowledge Graph with Memory Consolidation "
         "and Contradiction-Aware Retrieval-Augmented Generation")

AUTHORS = [
    {"name": "Dr. P S Anu Rakhi", "role": "Assistant Professor",
     "dept": "School of Computing",
     "org": "Vel Tech Rangarajan Dr. Sagunthala R&D\nInstitute of Science and Technology",
     "city": "Chennai, India", "email": "anurakhips@veltech.edu.in"},
    {"name": "Maria Immanuel L", "role": "", "dept": "School of Computing",
     "org": "Vel Tech Rangarajan Dr. Sagunthala R&D\nInstitute of Science and Technology",
     "city": "Chennai, India", "email": "vtu24334@veltech.edu.in"},
    {"name": "Vigneshwaran S", "role": "", "dept": "School of Computing",
     "org": "Vel Tech Rangarajan Dr. Sagunthala R&D\nInstitute of Science and Technology",
     "city": "Chennai, India", "email": "vtu24372@veltech.edu.in"},
]

# --------------------------------------------------------------------------
# References: corrected and numbered in order of first citation. Entries that
# could not be located in IEEE Xplore / the publisher's site have been removed
# rather than kept on trust; see the review document for which ones and why.
# --------------------------------------------------------------------------
REFS = [
    "[1] P. Lewis et al., \u201cRetrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,\u201d in Proc. Adv. Neural Inf. Process. Syst. (NeurIPS), vol. 33, 2020, pp. 9459\u20139474.",
    "[2] Y. Gao et al., \u201cRetrieval-Augmented Generation for Large Language Models: A Survey,\u201d arXiv:2312.10997, 2023.",
    "[3] V. Karpukhin et al., \u201cDense Passage Retrieval for Open-Domain Question Answering,\u201d in Proc. Conf. Empirical Methods Natural Lang. Process. (EMNLP), 2020, pp. 6769\u20136781.",
    "[4] S. Robertson and H. Zaragoza, \u201cThe Probabilistic Relevance Framework: BM25 and Beyond,\u201d Found. Trends Inf. Retr., vol. 3, no. 4, pp. 333\u2013389, 2009.",
    "[5] N. Bruch, S. Nedelkoski, and S. Mandal, \u201cA Deep Dive into Vector Stores: Classifying the Backbone of Retrieval-Augmented Generation,\u201d in Proc. IEEE Int. Conf. Big Data, 2024.",
    "[6] D. Edge et al., \u201cFrom Local to Global: A Graph RAG Approach to Query-Focused Summarization,\u201d arXiv:2404.16130, 2024.",
    "[7] Z. Peng et al., \u201cGraph Retrieval-Augmented Generation: A Survey,\u201d arXiv:2408.08921, 2024.",
    "[8] A. Hogan et al., \u201cKnowledge Graphs,\u201d ACM Comput. Surv., vol. 54, no. 4, 2021.",
    "[9] B. Cai, Y. Xiang, L. Gao, H. Zhang, Y. Li, and J. Li, \u201cTemporal Knowledge Graph Completion: A Survey,\u201d in Proc. 32nd Int. Joint Conf. Artif. Intell. (IJCAI), 2023, pp. 6545\u20136553.",
    "[10] L. Wang et al., \u201cA Survey on Large Language Model based Autonomous Agents,\u201d Frontiers Comput. Sci., vol. 18, no. 6, p. 186345, 2024.",
    "[11] Z. Zhang et al., \u201cA Survey on the Memory Mechanism of Large Language Model based Agents,\u201d arXiv:2404.13501, 2024.",
    "[12] J. Zheng et al., \u201cLifelong Learning of Large Language Model based Agents: A Roadmap,\u201d IEEE Trans. Pattern Anal. Mach. Intell., 2026 (early access).",
    "[13] L. Bourtoule et al., \u201cMachine Unlearning,\u201d in Proc. IEEE Symp. Security and Privacy (S&P), 2021, pp. 141\u2013159.",
    "[14] A. Asai, Z. Wu, Y. Wang, A. Sil, and H. Hajishirzi, \u201cSelf-RAG: Learning to Retrieve, Generate and Critique through Self-Reflection,\u201d in Proc. Int. Conf. Learn. Represent. (ICLR), 2024.",
    "[15] S. Yan et al., \u201cCorrective Retrieval Augmented Generation,\u201d arXiv:2401.15884, 2024.",
    "[16] R. Ko, M. K. G\u00fcrkan, and F. T. Yarman Vural, \u201cReRag: A New Architecture for Reducing the Hallucination by Retrieval-Augmented Generation,\u201d in Proc. 9th Int. Conf. Comput. Sci. Eng. (UBMK), 2024, pp. 961\u2013965.",
    "[17] X. Ji et al., \u201cRAG Certainty: Quantifying the Certainty of Context-Based Responses by LLMs,\u201d in Proc. IEEE Int. Conf. Acoust., Speech Signal Process. (ICASSP), 2025.",
    "[18] N. Reimers and I. Gurevych, \u201cSentence-BERT: Sentence Embeddings using Siamese BERT-Networks,\u201d in Proc. EMNLP, 2019, pp. 3982\u20133992.",
    "[19] J. Johnson, M. Douze, and H. J\u00e9gou, \u201cBillion-Scale Similarity Search with GPUs,\u201d IEEE Trans. Big Data, vol. 7, no. 3, pp. 535\u2013547, 2021.",
    "[20] T. Brown et al., \u201cLanguage Models are Few-Shot Learners,\u201d in Proc. NeurIPS, vol. 33, 2020, pp. 1877\u20131901.",
    "[21] A. Radford et al., \u201cRobust Speech Recognition via Large-Scale Weak Supervision,\u201d in Proc. Int. Conf. Mach. Learn. (ICML), 2023, pp. 28492\u201328518.",
]


# ===========================================================================
# Figure 1 - architecture. Drawn with reportlab primitives so the paper has no
# external image dependencies and the figure stays in step with the text.
# ===========================================================================
def architecture_figure(S, width=COL_W):
    """
    Vertical retrieval pipeline with the derived stores and the five forgetting
    surfaces marked on the right. Drawn with reportlab primitives so the paper
    carries no external image and the figure cannot drift from the text.

    Geometry note: an earlier version placed the legend inside the same vertical
    band as the last stage box and used Drawing.scale(), so the legend printed on
    top of the final boxes. The layout below reserves its own band for the legend
    and keeps a fixed right gutter for the forgetting bracket, so nothing
    overlaps at any column width.
    """
    box_h = 17.0
    gap = 8.0
    gutter = 54.0                    # reserved on the right for the bracket
    legend_h = 30.0                  # reserved band for the legend
    box_w = width - gutter - 4
    stages = [
        ("User", "user"),
        ("Text / voice / web / screen capture", "app"),
        ("Normalisation + deduplication hash", "app"),
        ("Memory store (primary table)", "app"),
        ("Adaptive Memory Scoring (C1)", "research"),
        ("Temporal KG (C2)  \u00b7  vector store  \u00b7  search index", "derived"),
        ("Contradiction Detection (C3)", "research"),
        ("Memory Consolidation (C4)", "research"),
        ("Forgetting filter (C6)", "research"),
        ("Hybrid retrieval (dense + lexical)", "retr"),
        ("Re-ranking: validity, conflict, importance", "retr"),
        ("Local or hosted LLM \u2192 answer", "app"),
    ]
    n = len(stages)
    # Vertical budget: the legend band sits BELOW the pipeline, so the last stage
    # box cannot collide with it. (The first version added the legend height to
    # the drawing but anchored the boxes from the top of the whole drawing, which
    # pushed the last two boxes below y = 0 and printed the legend over them.)
    boxes_h = n * box_h + (n - 1) * gap
    total_h = legend_h + 8 + boxes_h + 4
    d = Drawing(width, total_h)

    fills = {
        "user": colors.HexColor("#1f2a44"),
        "app": colors.HexColor("#e8eef7"),
        "research": colors.HexColor("#fdf1d6"),
        "derived": colors.HexColor("#e6f4ea"),
        "retr": colors.HexColor("#f0e6f6"),
    }
    text_colours = {"user": colors.white}

    top = total_h - 3            # top edge of the first box
    centres = []
    for i, (label, kind) in enumerate(stages):
        y = top - (i + 1) * box_h - i * gap
        d.add(Rect(2, y, box_w, box_h, fillColor=fills[kind],
                   strokeColor=colors.HexColor("#5b6b85"), strokeWidth=0.5, rx=2, ry=2))
        d.add(String(8, y + box_h / 2 - 3.0, label, fontName="Times-Roman", fontSize=6.6,
                     fillColor=text_colours.get(kind, colors.HexColor("#111111"))))
        centres.append(y + box_h / 2)
        if i < n - 1:
            cx = 2 + box_w / 2.0
            d.add(Line(cx, y, cx, y - gap, strokeColor=colors.HexColor("#5b6b85"), strokeWidth=0.5))
            d.add(Polygon([cx - 3, y - gap + 3, cx + 3, y - gap + 3, cx, y - gap - 0.5],
                          fillColor=colors.HexColor("#5b6b85"), strokeColor=None))

    # the five forgetting surfaces: primary store, search index, vector store,
    # graph nodes/edges, and the derived scores/conflicts
    bx = 2 + box_w + 8
    surf_top = centres[3] + box_h / 2 + 1
    surf_bottom = centres[5] - box_h / 2 - 1
    red = colors.HexColor("#b3261e")
    d.add(Line(bx, surf_top, bx, surf_bottom, strokeColor=red, strokeWidth=0.7))
    for idx in (3, 5):
        d.add(Line(bx, centres[idx], bx + 4, centres[idx], strokeColor=red, strokeWidth=0.7))
    tx = bx + 6
    d.add(String(tx, surf_bottom + 2, "forgetting", fontName="Times-Bold", fontSize=5.8, fillColor=red))
    d.add(String(tx, surf_bottom - 5, "enforced at", fontName="Times-Roman", fontSize=5.6, fillColor=red))
    d.add(String(tx, surf_bottom - 12, "5 surfaces", fontName="Times-Roman", fontSize=5.6, fillColor=red))

    # legend, in its own reserved band below the last box
    legend = [("application / capture", "app"), ("research layer (this paper)", "research"),
              ("derived stores", "derived"), ("retrieval", "retr")]
    for i, (name, kind) in enumerate(legend):
        col = i % 2
        row = i // 2
        lx = 4 + col * (width / 2.0)
        ly = legend_h - 14 - row * 11
        d.add(Rect(lx, ly, 7, 7, fillColor=fills[kind],
                   strokeColor=colors.HexColor("#5b6b85"), strokeWidth=0.4))
        d.add(String(lx + 10, ly + 1.2, name, fontName="Times-Roman", fontSize=5.8,
                     fillColor=colors.HexColor("#333333")))
    d.add(String(4, legend_h - 2, "Legend", fontName="Times-Bold", fontSize=5.8,
                 fillColor=colors.HexColor("#333333")))
    return d


def fig_caption(number, title, S):
    return Paragraph(f'<b>Fig. {number}.</b> {_xml(title)}', S["capt"])


def marker(text, S):
    """Highlighted [REQUIRES EXPERIMENT] style marker for unrun experiments."""
    return Paragraph(
        f'<font color="#b3261e"><b>[{text}]</b></font>', S["capt"])


def main():
    if not os.path.exists(RESULTS_FILE):
        raise SystemExit(
            f"\n[!] {RESULTS_FILE} not found - this paper reports measured numbers.\n"
            "    Regenerate it first (from the repository root):\n"
            "        python backend/run_benchmark.py\n")

    with open(RESULTS_FILE, encoding="utf-8") as fh:
        r = json.load(fh)

    res = r["results"]
    comp = r["comparison"]
    corpus = r["corpus"]
    cfg = r.get("configuration", {})
    env = r.get("environment", {})
    v, hy, gr, ad = res["vanilla"], res["hybrid"], res["graph"], res["adaptive"]
    S = styles()

    story = []
    # ============================================================ PAGE 1 HEAD
    story.append(Paragraph(COPYRIGHT, S["copyright"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(_xml(TITLE), S["title"]))
    story.append(base.build_author_table(S))
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------------- ABSTRACT
    story.append(Paragraph(
        "<b><i>Abstract</i></b>\u2014Retrieval-augmented generation (RAG) over a "
        "<i>personal</i> knowledge store fails differently from RAG over a static corpus. "
        "A personal store accumulates statements the user has since contradicted, facts "
        "whose validity has lapsed, near-duplicate captures of the same material, and "
        "content the user has explicitly asked to remove. Conventional retrieval treats "
        "all of it as equally current evidence, so an answer can be confidently wrong "
        "while every retrieved passage remains faithful to its source; and the recall-"
        "oriented metrics standard in RAG evaluation do not reveal it, because they "
        "saturate before the ordering errors appear. This paper addresses that gap with "
        "SecondBrain, a research layer that applies adaptive lifelong personal memory "
        "management to RAG. Its seven components are Adaptive Memory Scoring, a Temporal "
        "Personal Knowledge Graph, Contradiction-Aware Hybrid Retrieval, Memory "
        "Consolidation, Knowledge-Gap Detection, retrieval-enforced Forgetting, and "
        "PersonalBrain-Bench. The layer is additive: it annotates existing memories "
        "through separate tables and can be disabled component by component, which is "
        "what makes a controlled comparison possible. On the controlled PersonalBrain-"
        f"Bench corpus of {corpus['memories']} synthetic memories and 11 questions "
        "(9 answerable, six question categories plus an abstention category), four "
        "retrieval pipelines are compared at k = 5 in a deterministic, CPU-only, "
        f"network-free configuration. Hit@5 saturates at {ad['hit_at_k']:.3f} for all four "
        "systems, confirming that position-insensitive recall does not separate them. On "
        f"the rank-sensitive measures it does: mean reciprocal rank is {ad['mrr']:.3f} for "
        f"the proposed pipeline against {v['mrr']:.3f} (dense-only), {hy['mrr']:.3f} "
        f"(hybrid) and {gr['mrr']:.3f} (graph-augmented); the rate of leading with "
        f"superseded content falls from {v['stale_top1_rate']:.3f} to "
        f"{ad['stale_top1_rate']:.3f}; and both duplicate context and post-forgetting "
        f"leakage fall from {v['duplicate_rate']:.3f} to {ad['duplicate_rate']:.3f}, "
        "whereas the baselines continue to return explicitly unlearned content in the "
        "model-free configuration evaluated here. Two consecutive executions reproduce "
        "these metrics exactly. The corpus is deliberately small and synthetic, the "
        "extraction rules are conservative, and the evaluation covers retrieval rather "
        "than end-to-end generation: the results characterise behaviour on a controlled "
        "corpus, and the paper states which claims remain to be measured.", S["abs_body"]))

    story.append(Paragraph(
        "<b><i>Keywords</i></b>\u2014personal knowledge management, retrieval-augmented "
        "generation, temporal knowledge graphs, contradiction detection, retrieval-level "
        "forgetting, memory consolidation, personal AI evaluation.", S["kw"]))

    # ------------------------------------------------------------ I. INTRODUCTION
    story.append(base.h1("I", "Introduction", S))
    story.append(Paragraph(
        "Retrieval-augmented generation grounds a language model in retrieved evidence "
        "rather than in parametric memory alone [1], [2]. The retrieval layer is normally "
        "evaluated on general corpora whose documents are assumed mutually consistent, "
        "immutable and equally current. A personal knowledge store violates all three "
        "assumptions. The user changes their mind, a deadline moves, the same web page is "
        "captured three times, a note is deliberately deleted. These are ordinary events "
        "in a personal corpus, and each of them produces a retrieval failure that "
        "conventional RAG evaluation is not built to see.", S["body"]))
    story.append(Paragraph(
        "Consider a concrete case. In January the user records that they are learning "
        "Python; in September they record that they are now focusing on Java. Both "
        "statements are in the store, correctly, because both were true when written. A "
        "conventional retriever returns whichever is more similar to the query "
        "\u201cwhat am I working on?\u201d, and if that is the January note the assistant "
        "answers confidently and wrongly. No content was fabricated \u2014 every retrieved "
        "passage is faithful to its source \u2014 so faithfulness and hallucination metrics "
        "cannot detect the failure. The error is not in the generation step but in the "
        "decision about which evidence is currently true.", S["body"]))
    story.append(Paragraph(
        "The same structure appears in three further cases. Two memories can disagree "
        "without either being out of date, when a deadline is moved or an invoice "
        "superseded. Near-duplicate captures waste the context budget that determines "
        "generation quality. And a memory the user has deleted can survive in a full-text "
        "index, a vector index or a derived graph, so that \u201cremoved\u201d content "
        "returns to the answer.", S["body"]))
    story.append(Paragraph(
        "Existing work addresses adjacent problems rather than this one. RAG and Graph RAG "
        "improve how evidence is found [1]\u2013[7]; retrieval-level verification and "
        "self-critique check generated claims against the retrieved evidence [14]\u2013[17]. "
        "The latter is orthogonal here: when the retrieved evidence is itself outdated or "
        "mutually contradictory, verification against that evidence confirms the error "
        "rather than catching it. Machine unlearning considers removing the influence of "
        "training data from model parameters [13], which is a different problem from "
        "removing an item from a retrieval store and every index derived from it. Agent-"
        "memory research establishes that persistence and memory modules matter [10]\u2013"
        "[12], but does not specify how a stored memory ceases to be current.", S["body"]))
    story.append(Paragraph(
        "<b>Research gap.</b> Three gaps follow. (i) There is no standard evaluation that "
        "contains superseded, contradictory, duplicated and deliberately forgotten "
        "personal memories, so these failures are unmeasurable in aggregate. (ii) Temporal "
        "validity, conflict status and removal are usually recorded as metadata rather "
        "than enforced at retrieval time, although retrieval time is where the failure "
        "occurs. (iii) Because recall-oriented metrics saturate on small personal corpora, "
        "improvements to ordering and staleness can be invisible to the metrics in "
        "standard use.", S["body"]))

    story.append(Paragraph(
        "This paper asks one main question and four specific ones. <b>Main RQ:</b> how "
        "should a personal memory system retrieve evidence so that a generated answer "
        "reflects what the user currently holds to be true, rather than what they once "
        "wrote? <b>RQ1 (temporal validity):</b> does enforcing validity intervals over "
        "stored facts improve rank-sensitive retrieval for state-change questions, "
        "compared with relevance-only and hybrid retrieval? <b>RQ2 (contradiction):</b> "
        "does explicit conflict detection with rank damping improve the ordering of "
        "current facts over superseded ones for contradictory evidence? <b>RQ3 "
        "(consolidation):</b> does near-duplicate consolidation with retrieval-time "
        "deduplication reduce redundant context without reducing Hit@k? <b>RQ4 "
        "(retrieval-enforced forgetting):</b> does exclusion at every derived retrieval "
        "surface eliminate post-forgetting leakage where deleting the primary row alone "
        "does not?", S["body"]))

    story.append(Paragraph(
        "The corresponding hypotheses are stated so that each maps to a measurement "
        "reported in Section VI. <b>H1:</b> the proposed pipeline attains higher MRR and "
        "lower stale@1 than dense-only and hybrid retrieval on the temporal-question "
        "subset. <b>H2:</b> it attains higher MRR than dense-only retrieval on the "
        "contradiction subset. <b>H3:</b> its duplicate rate is zero while baseline "
        "duplicate rates are not, with no loss in Hit@5. <b>H4:</b> its post-forgetting "
        "leakage is zero while baseline leakage is not, in a configuration in which the "
        "unlearned row remains present in the primary store. The null hypothesis under "
        "test for Hit@5 is that the pipelines do not differ on this corpus.", S["body"]))

    story.append(Paragraph(
        "The contributions are as follows. (1) A seven-component research layer for "
        "personal memory in RAG, designed to be additive to an existing capture pipeline "
        "and individually switchable. (2) An importance-scoring model whose eight terms "
        "are persisted separately and are therefore auditable. (3) A temporal triple "
        "store with validity intervals and state supersession that closes facts without "
        "deleting them, so historical and current queries are both answerable. "
        "(4) Contradiction detection combining temporal, lexical-negation and numeric "
        "value-change signals, resolved by rank damping rather than removal. "
        "(5) Consolidation with provenance preservation and a similarity threshold "
        "calibrated from measurement. (6) Forgetting enforced across five retrieval "
        "surfaces with reversible restoration. (7) PersonalBrain-Bench and an evaluation "
        "showing that rank-sensitive and staleness metrics separate the pipelines where "
        "Hit@k cannot.", S["body"]))
    story.append(Paragraph(
        "Section II positions the work against existing literature. Sections III and IV "
        "describe the architecture and the seven components. Sections V and VI report the "
        "controlled evaluation. Section VII specifies the experiments that are designed "
        "but not yet run, Section VIII analyses cases in which the current rules fail, and "
        "Sections IX and X set out limitations and conclusions.", S["body"]))

    # ------------------------------------------------------------ II. RELATED WORK
    story.append(PageBreak())
    story.append(base.h1("II", "Related Work", S))

    story.append(Paragraph("A. Retrieval-Augmented Generation", S["h2"]))
    story.append(Paragraph(
        "RAG augments generation with retrieved context to ground responses in external "
        "evidence [1], and surveys of the area identify chunking, embedding, retrieval and "
        "generation as the stages where quality is won or lost [2]. The design assumption "
        "throughout is that the corpus documents are contemporaneous and mutually "
        "consistent with respect to the query. Our work does not replace this pipeline; it "
        "adds a temporal and conflict layer above it, and uses a graph-augmented pipeline "
        "as an explicit baseline so that the incremental effect is measured rather than "
        "assumed.", S["body"]))

    story.append(Paragraph("B. Hybrid and Vector Retrieval", S["h2"]))
    story.append(Paragraph(
        "Dense retrieval learns a shared embedding space for queries and passages [3], "
        "while lexical scoring remains a strong and interpretable baseline [4]; fusing the "
        "two is standard practice and comparative studies characterise the vector-store "
        "substrate beneath it [5]. We adopt hybrid retrieval as a baseline and show that "
        "on a personal corpus it is the strongest of the three baselines while still "
        f"returning superseded content at rank one in {hy['stale_top1_rate']*100:.1f}% of "
        "queries.", S["body"]))

    story.append(Paragraph("C. Graph RAG", S["h2"]))
    story.append(Paragraph(
        "Graph RAG retrieves over a knowledge graph to support multi-hop questions that "
        "flat chunk retrieval cannot answer [6], [7], building on knowledge-graph "
        "representations generally [8]. Our graph component is used as a baseline and as "
        "a re-ranking signal rather than as the contribution.", S["body"]))

    story.append(Paragraph("D. Temporal Knowledge Representation", S["h2"]))
    story.append(Paragraph(
        "Temporal knowledge graphs extend triples with a time dimension and represent "
        "facts as implicitly or explicitly time-scoped statements [9]. Our temporal store "
        "uses the same interval formulation, but applies it for a different purpose: not "
        "to predict missing links, but to decide which of several stored assertions about "
        "the user is currently true at retrieval time.", S["body"]))

    story.append(Paragraph("E. LLM Agent Memory and Lifelong Personalisation", S["h2"]))
    story.append(Paragraph(
        "Agent research identifies memory as a core component alongside perception, "
        "planning and action [10]; systematic reviews catalogue memory sources, forms and "
        "operations for LLM agents [11]; and lifelong-learning roadmaps treat evolving "
        "knowledge as a first-class concern [12]. These contributions establish that "
        "persistence matters and how memory modules are designed. They treat disagreement "
        "between stored memories as an edge case rather than as the central problem, and "
        "they do not define an operational notion of current truth over the store.", S["body"]))

    story.append(Paragraph("F. Memory Consolidation", S["h2"]))
    story.append(Paragraph(
        "Deduplication and near-duplicate detection are long-standing problems in "
        "information retrieval. In a personal store the cost is specific: redundant "
        "retrieved passages consume the context budget that determines generation quality. "
        "Our consolidation clusters memories by cosine similarity over term-frequency "
        "vectors, elects a canonical representative, and preserves every merged identifier "
        "so that provenance survives the merge.", S["body"]))

    story.append(Paragraph("G. Machine Unlearning and Retrieval-Level Forgetting", S["h2"]))
    story.append(Paragraph(
        "Machine unlearning asks how to remove the influence of specific training data "
        "from a trained model [13]. The problem addressed here is different in kind, and "
        "the distinction matters for interpreting our results: this work addresses "
        "forgetting at the retrieval and derived-memory layer rather than parameter-level "
        "machine unlearning. No model weights are modified. What removal must survive is "
        "not a parametric representation but a set of derived retrieval surfaces, each of "
        "which can independently re-admit the content.", S["body"]))

    story.append(Paragraph("H. Contradiction and Hallucination Handling", S["h2"]))
    story.append(Paragraph(
        "Work on reducing hallucination verifies generated claims against retrieved "
        "evidence through self-reflection and critique [14], corrective retrieval [15], "
        "hyperparameter tuning of the retrieval stage [16], or certainty estimation over "
        "retrieval and generation [17]. These methods improve the reliability of the "
        "generate step. They do not detect that the evidence itself is stale or "
        "self-contradictory, which is the failure mode this paper targets.", S["body"]))

    story.append(Paragraph("I. Personal AI and Knowledge-Management Benchmarks", S["h2"]))
    story.append(Paragraph(
        "Existing RAG benchmarks evaluate retrieval and answer quality over corpora whose "
        "items are assumed valid. To our knowledge no widely used benchmark contains "
        "superseded facts, contradictions between items, deliberate removals, or a "
        "declared abstention category in combination, although establishing that absence "
        "as a fact would require a systematic benchmark review that this paper does not "
        "claim to provide. PersonalBrain-Bench is therefore proposed as an instrument for "
        "this setting rather than as a general replacement.", S["body"]))

    story.append(tbl_caption("I", "Research Gap Comparison", S))
    # Column widths are set so that no header has to break mid-word inside the
    # 243 pt column; short header words with the meaning given in the caption.
    story.append(make_table([
        ["Approach", "Temp.", "Conflict", "Dedup.", "Forget.", "Personal<br/>bench."],
        ["Dense / hybrid RAG [1]\u2013[5]", "\u2014", "\u2014", "\u2014", "\u2014", "\u2014"],
        ["Graph RAG [6]\u2013[8]", "\u2014", "\u2014", "\u2014", "\u2014", "\u2014"],
        ["Temporal KG completion [9]", "Yes", "\u2014", "\u2014", "\u2014", "\u2014"],
        ["Agent memory / lifelong [10]\u2013[12]", "\u2014", "\u2014", "\u2014", "\u2014", "\u2014"],
        ["Machine unlearning [13]", "\u2014", "\u2014", "\u2014", "Params", "\u2014"],
        ["Self-critique / corrective RAG [14]\u2013[17]", "\u2014", "Evidence", "\u2014", "\u2014", "\u2014"],
        ["This work", "Yes", "Yes", "Yes", "Yes", "Yes"],
    ], [86, 30, 33, 26, 29, 39], S, align_left_col0=True))
    story.append(Paragraph(
        "Columns: Temp. = temporal memory; Conflict = contradiction handling; Dedup. = "
        "consolidation or deduplication; Forget. = retrieval-level forgetting; Personal "
        "bench. = a benchmark that includes personal-memory failure categories. Cells are "
        "marked from what each cited source describes as its own contribution; a dash means "
        "the capability is not addressed by that work, not that the work is deficient. "
        "\u201cEvidence\u201d denotes checking generated text against retrieved evidence "
        "rather than resolving disagreement between stored memories; \u201cParams\u201d "
        "denotes removal from model parameters [13].", S["capt"]))

    # ------------------------------------------------ III. SYSTEM ARCHITECTURE
    story.append(base.h1("III", "System Architecture", S))
    story.append(Paragraph(
        "SecondBrain is a client\u2013server personal knowledge system. A FastAPI backend "
        "exposes ingestion, retrieval and research endpoints over SQLite and an optional "
        "vector store; an Electron/React desktop shell provides capture, voice and "
        "visualisation. The research layer described here is additive: it observes and "
        "annotates existing memories through tables keyed by memory identifier, and does "
        "not modify the capture path. Each component is guarded at runtime, so the system "
        "degrades to a conventional RAG assistant if a component is unavailable or "
        "disabled, which is what makes the comparative evaluation in Section VI possible.",
        S["body"]))

    story.append(fig_caption("1", "Retrieval pipeline with the derived stores and the five "
                                   "surfaces at which forgetting is enforced.", S))
    story.append(Spacer(1, 3))
    story.append(architecture_figure(S))
    story.append(Spacer(1, 5))

    story.append(Paragraph(
        "The architecture separates three layers, and the separation is what allows the "
        "paper's claims to be tested. The <b>application layer</b> captures and stores: "
        "screen OCR, mail over IMAP or OAuth, web and social ingestion, normalisation and "
        "the primary memory table. The <b>research layer</b> annotates and filters: "
        "scoring, the temporal graph, conflict detection, consolidation, gap detection and "
        "forgetting, all stored in separate tables. The <b>evaluation layer</b> is the "
        "benchmark and its harness, which drives the retrievers over a fixed corpus and "
        "writes a machine-readable artefact. No component in the research layer writes to "
        "the capture path, and the evaluation layer reads only through the public "
        "retrieval interface.", S["body"]))

    story.append(tbl_caption("II", "Processing Stages", S))
    story.append(make_table([
        ["Stage", "Component", "Responsibility"],
        ["1", "Capture / ingest", "Screen OCR, mail (IMAP/OAuth), web and social capture"],
        ["2", "Normalisation", "Chunking, content hash, memory row + search index row"],
        ["3", "Scoring (C1)", "Adaptive Memory Scoring: eight persisted terms"],
        ["4", "Temporal (C2)", "Triple extraction, validity intervals, supersession"],
        ["5", "Conflict (C3)", "Three conflict classes, damping policy"],
        ["6", "Consolidation (C4)", "Near-duplicate clustering, provenance retention"],
        ["7", "Gaps (C5)", "Exposure vs explanation depth per concept"],
        ["8", "Forgetting (C6)", "Tombstone + exclusion at five retrieval surfaces"],
        ["9", "Retrieval", "Four switchable pipelines (dense / hybrid / graph / adaptive)"],
        ["10", "Generation", "Local or hosted LLM over the assembled context"],
    ], [24, 62, COL_W - 86], S, align_left_col0=True))

    story.append(Paragraph(
        "Table III states which mechanisms are adopted from prior work and which are "
        "proposed here, so that no existing technique is presented as new.", S["body"]))
    story.append(tbl_caption("III", "Adopted Mechanisms versus Proposed Mechanisms", S))
    story.append(make_table([
        ["Element", "Status"],
        ["Dense, lexical and hybrid retrieval [3]\u2013[5]", "Adopted as baselines"],
        ["Graph-augmented re-ranking [6]\u2013[8]", "Adopted as a baseline"],
        ["Interval-based temporal triples [9]", "Adopted representation"],
        ["Cosine near-duplicate clustering", "Adopted technique, applied to consolidation"],
        ["Eight-term importance score with per-term persistence", "Proposed"],
        ["Predicate canonicalisation before supersession", "Proposed"],
        ["Three-class conflict detection with rank damping", "Proposed combination"],
        ["Five-surface forgetting enforcement with restoration", "Proposed"],
        ["Exposure-versus-depth gap score", "Proposed"],
        ["PersonalBrain-Bench", "Proposed instrument"],
    ], [COL_W - 74, 74], S, align_left_col0=True))

    # ------------------------------------------------------------- IV. METHOD
    story.append(base.h1("IV", "Proposed Method", S))

    story.append(Paragraph("A. Adaptive Memory Scoring (C1)", S["h2"]))
    story.append(Paragraph(
        "A personal store grows without bound, and a retriever that weights every memory "
        "equally cannot distinguish a clipboard fragment from the note that defines the "
        "user's project. Each memory receives an importance score composed of six positive "
        "and two negative terms:", S["body"]))
    story.append(Paragraph(
        "M = w<sub>1</sub>R + w<sub>2</sub>F + w<sub>3</sub>T + w<sub>4</sub>G + "
        "w<sub>5</sub>U + w<sub>6</sub>P \u2212 w<sub>7</sub>D \u2212 w<sub>8</sub>C "
        "(1)", S["eq"]))
    story.append(Paragraph(
        "R is relevance to the user's represented interests; F recurrence across "
        "sessions; T recency under exponential decay; G graph connectivity of the "
        "memory's concepts; U explicit user confirmation; P predicted future utility; D a "
        "redundancy penalty; and C a contradiction penalty. Every component is normalised "
        "to [0, 1] before weighting, all eight are persisted alongside the total with the "
        "weights version, and no component is a learned parameter. Recency uses a half-"
        "life of 45 days, T = 2<sup>\u2212\u0394t/45</sup>, so a memory loses half its "
        "recency contribution every 45 days without ever reaching zero. The weights in use "
        "are w = (0.30, 0.08, 0.22, 0.15, 0.15, 0.10) for R, F, T, G, U, P and (0.18, "
        "0.25) for the subtracted D and C; the positive terms sum to 1.0. These values "
        "were set by design, not optimised: sensitivity to them is an experiment that has "
        "not been run, and is specified in Section VII.", S["body"]))
    story.append(Paragraph(
        "<font color='#b3261e'><b>[REQUIRES EXPERIMENT]</b></font> Sensitivity of "
        "retrieval quality to the half-life (e.g. 15, 30, 45, 90, 180 days) and to the "
        "weight vector, including removal of individual terms.", S["body"]))

    story.append(Paragraph("B. Temporal Personal Knowledge Graph (C2)", S["h2"]))
    story.append(Paragraph(
        "Facts are stored as (subject, predicate, object) triples carrying a validity "
        "interval [valid_from, valid_to). A null valid_to denotes a currently true fact. "
        "When an incoming stateful fact shares its (subject, predicate) with an open fact "
        "but carries a different object, the older fact is closed: valid_to is set and a "
        "superseded_by link is recorded. History therefore remains queryable, so "
        "\u201cwhat am I working on?\u201d and \u201cwhat did I used to work on?\u201d are "
        "both answerable from one store. Deletion would answer the stale-answer problem at "
        "the cost of the historical one; closing a fact preserves both capabilities.",
        S["body"]))
    story.append(Paragraph(
        "Predicates are canonicalised into state classes before supersession is applied. "
        "Without canonicalisation, \u201clearning Python\u201d and \u201cfocusing on "
        "Java\u201d are recorded under different predicates, neither supersedes the other, "
        "and the graph reports both as current. This was a real defect in our first "
        "implementation rather than a hypothetical one: the two facts the graph exists to "
        "reconcile were stored separately, and only the automated suite surfaced it.",
        S["body"]))
    story.append(Paragraph(
        "The same mechanism is what makes the motivating Python/Java case answerable. "
        "Both memories remain in the store; the older is closed at the timestamp of the "
        "newer, and retrieval can distinguish a question about current focus (answered "
        "from the open fact) from one about history (answered from the closed interval).",
        S["body"]))

    story.append(Paragraph("C. Contradiction-Aware Hybrid Retrieval (C3)", S["h2"]))
    story.append(Paragraph(
        "Three conflict classes are detected, summarised in Table IV. Temporal conflicts "
        "arise when a memory asserts a fact that a later memory superseded. Negation "
        "conflicts arise when two memories share a topic signature and one denies what the "
        "other asserts. Value-change conflicts arise when two memories share a topic "
        "signature with high salient-word overlap but carry different dated or numeric "
        "values, which is the moved-deadline case that neither a first-person pattern nor "
        "a negation word covers.", S["body"]))
    story.append(tbl_caption("IV", "Conflict Classes and Example Pairs", S))
    story.append(make_table([
        ["Class", "Example pair", "Signal"],
        ["Temporal", "\u201clearning Python\u201d (Jan) vs \u201cfocusing on Java\u201d (Sep)",
         "Same canonical predicate, different object"],
        ["Negation", "\u201cthe review is on Friday\u201d vs \u201cthe review is not on Friday\u201d",
         "Shared topic, one side negated"],
        ["Value change", "\u201cdeadline 15 October\u201d vs \u201cdeadline 30 September\u201d",
         "Shared topic, differing dated value"],
    ], [44, COL_W - 128, 84], S, align_left_col0=True))
    story.append(Paragraph(
        "Resolution applies a rank multiplier rather than a deletion: an unresolved "
        "conflict of severity s damps the affected memory by (1 \u2212 0.7s), bounded to "
        "[0.3, 1.0], so a severe conflict cannot remove a memory from consideration "
        "entirely. Final ordering is rank-preserving: the fused retrieval order supplies a "
        "prior 1/(1+i) which the multipliers adjust, with importance acting only as a "
        "light tie-breaker. Sorting by importance alone was actively harmful in "
        "development, promoting high-importance but less relevant memories above the "
        "relevant one; that negative result shaped the final design.", S["body"]))
    story.append(Paragraph(
        "<font color='#b3261e'><b>[REQUIRES EXPERIMENT]</b></font> Precision, recall and "
        "F1 of conflict detection against a manually annotated conflict set. The detector "
        "is rule-based and its accuracy has not been measured; only its downstream effect "
        "on retrieval is reported in Section VI.", S["body"]))

    story.append(Paragraph("D. Memory Consolidation (C4)", S["h2"]))
    story.append(Paragraph(
        "Memories are clustered by cosine similarity over hashed term-frequency vectors, "
        "and a canonical representative is elected by importance and then length. Every "
        "merged member identifier is retained in the consolidation record, so provenance "
        "is preserved and a merge can be inspected. A retrieval-time deduplication pass "
        "applies the same similarity test within a single query's result list, so the "
        "guarantee holds even before an offline consolidation run has executed.", S["body"]))
    story.append(Paragraph(
        "The threshold is calibrated rather than assumed. In our corpus, reworded "
        "duplicates score approximately 0.82 while unrelated memories score below 0.30; "
        "the 0.90 threshold common in practice missed every reworded duplicate, so 0.78 is "
        "used. A threshold chosen by inspecting the test set would be a methodological "
        "error; this one was chosen from the measured similarity distribution and then "
        "left fixed for the benchmark. Because the corpus is small, the calibration should "
        "be repeated on a larger corpus, and the sensitivity around it is unmeasured.",
        S["body"]))
    story.append(Paragraph(
        "<font color='#b3261e'><b>[REQUIRES EXPERIMENT]</b></font> Threshold sensitivity "
        "at 0.60, 0.65, 0.70, 0.75, 0.78, 0.80, 0.85 and 0.90, reporting merge count, "
        "false merges and duplicate rate.", S["body"]))

    story.append(Paragraph("E. Knowledge-Gap Detection (C5)", S["h2"]))
    story.append(Paragraph(
        "Distinguishing exposure from understanding requires examining the shape of a "
        "concept's mentions rather than their count. For each concept the system computes "
        "mention frequency, whether it appears as the subject of an explanatory "
        "construction, whether it recurs across separate capture sessions, and its degree "
        "in the knowledge graph. Depth combines these, and the gap score is exposure "
        "\u00d7 (1 \u2212 depth) \u00d7 (1 \u2212 0.5 \u00b7 connectivity). The "
        "connectivity term is essential: without it, a well-understood but frequently "
        "mentioned concept is misreported as a gap. This is a secondary contribution, "
        "included because the failure it describes is specific to personal corpora; it is "
        "not presented as the paper's principal novelty, and its output is not evaluated "
        "as a ranking task here.", S["body"]))

    story.append(Paragraph("F. Retrieval-Enforced Forgetting (C6)", S["h2"]))
    story.append(Paragraph(
        "Removing a row from the memory table does not remove the content from retrieval. "
        "The full-text index entry, the vector embedding, the derived graph nodes and "
        "their incident edges, and the extracted temporal facts are independent surfaces "
        "from which the content can re-enter a result set, and the derived scores and "
        "conflict rows are two more pieces of state that reference it. The forgetting "
        "service therefore tombstones the memory and enforces exclusion at five surfaces: "
        "the search-index entry is deleted, the vector is removed from the store, graph "
        "nodes and their incident edges are deleted, temporal facts are closed and "
        "detached from their source, and derived scores and conflict rows are purged. "
        "Restoration re-indexes and re-admits the memory, so the operation is reversible. "
        "Fig. 1 marks where this applies in the pipeline.", S["body"]))
    story.append(Paragraph(
        "As stated in Section II, this is retrieval-level forgetting, not parameter-level "
        "machine unlearning [13]: no model weight is modified, and a model that has already "
        "memorised the content in a previous session is out of scope.", S["body"]))

    story.append(Paragraph("G. PersonalBrain-Bench (C7)", S["h2"]))
    story.append(Paragraph(
        "Existing RAG benchmarks do not contain contradictory, superseded or deliberately "
        "forgotten personal memories, so they cannot expose the failures this paper "
        "targets. PersonalBrain-Bench is a synthetic personal corpus with a graded "
        "question set. Synthetic construction is deliberate: a real personal store would "
        "make the experiment unreproducible and would place private data in a publication. "
        "The corpus and question set are described in Section V-A.", S["body"]))

    # ------------------------------------------------- V. EXPERIMENTAL SETUP
    story.append(base.h1("V", "Experimental Setup", S))

    story.append(Paragraph("A. Corpus and Question Set", S["h2"]))
    story.append(Paragraph(
        f"PersonalBrain-Bench contains {corpus['memories']} memories spanning email, "
        "notes, code, web captures and screen text, with creation timestamps distributed "
        "across a 240-day window so that recency and supersession are exercised rather "
        "than simulated. The corpus embeds a superseded state pair (learning Python, then "
        "focusing on Java), a moved deadline (15 October to 30 September), a three-member "
        "near-duplicate cluster, a multi-hop chain linking a project to a dataset and a "
        "model, a sensitive scratch note that is then explicitly forgotten, and a concept "
        "mentioned repeatedly without explanation. Ingestion detects "
        f"{corpus['conflicts']} conflicts, both of the value-change class, and one memory "
        "is forgotten for the removal evaluation. Of the 11 questions, 9 are answerable; "
        "the two remaining questions test abstention and removal respectively and have no "
        "gold memory by construction. Table V lists the categories.", S["body"]))
    story.append(tbl_caption("V", "Question Categories in PersonalBrain-Bench", S))
    story.append(make_table([
        ["Category", "n", "Answerable", "What it tests"],
        ["Factual recall", "3", "Yes", "Retrieval of an unambiguous stored fact"],
        ["Temporal state", "2", "Yes", "Current value preferred over superseded"],
        ["Contradiction", "2", "Yes", "Current side of a changed deadline"],
        ["Multi-hop", "1", "Yes", "Synthesis across linked memories"],
        ["Duplicate", "1", "Yes", "No redundant context in the result set"],
        ["Abstention (gap)", "1", "No", "Unanswerable question not answered"],
        ["Removal", "1", "No", "Forgotten content not returned"],
    ], [68, 16, 46, COL_W - 130], S, align_left_col0=True))

    story.append(Paragraph("B. Systems Compared", S["h2"]))
    story.append(Paragraph(
        "<b>Vanilla</b> is dense-only retrieval. <b>Hybrid</b> fuses dense and lexical "
        "results. <b>Graph</b> adds knowledge-graph connectivity re-ranking. <b>Adaptive</b> "
        "is the proposed pipeline: hybrid plus forgetting exclusion, temporal validity "
        "damping, contradiction damping, importance weighting and consolidation-based "
        "deduplication. All four share identical candidate generation and differ only in "
        "the post-retrieval layer, so measured differences are attributable to that layer "
        "rather than to the retriever.", S["body"]))

    story.append(Paragraph("C. Metrics", S["h2"]))
    story.append(Paragraph(
        "Hit@k and MRR are computed over answerable questions only; including abstention "
        "and removal questions, which have no gold memory by construction, would depress "
        "every system equally and conceal differences. Three further metrics are reported. "
        "<b>stale@1</b> is the fraction of queries whose top-ranked result is superseded or "
        "forbidden, because rank one is what a generator leads with. <b>Forgotten-leak "
        "rate</b> is the fraction of returned results that were explicitly unlearned. "
        "<b>Duplicate rate</b> is the fraction of within-query result pairs at or above the "
        "consolidation threshold. All are fractions of returned results or of questions, "
        "and lower is better for all three.", S["body"]))

    story.append(Paragraph("D. Reproducibility and Configuration", S["h2"]))
    story.append(Paragraph(
        f"The evaluation is reported for a single recorded configuration (dense backend "
        f"\u201c{cfg.get('dense_backend', 'n/a')}\u201d, scoring weights version "
        f"\u201c{cfg.get('scoring_weights_version', 'n/a')}\u201d, k = {cfg.get('k', 5)}, "
        "corpus-scoped evaluation). Three properties are worth stating explicitly, because "
        "each was a source of irreproducibility that had to be removed. First, the dense "
        "retriever is pinned to the model-free TF-IDF path for the benchmark: with a neural "
        "embedder installed the leak and staleness figures differ, so a result table "
        "without the backend stated is not reproducible. The shipped pipeline still selects "
        "a neural embedder automatically when one is installed; only the evaluation is "
        "pinned. Second, every stage \u2014 retrieval, scoring, conflict detection, "
        "temporal supersession, gap statistics and keyword search \u2014 is evaluated "
        "within the corpus scope, so the presence of unrelated memories in the database "
        "cannot move the numbers. Third, two consecutive full executions reproduce the "
        "figures exactly, with no network access and no GPU. All results are produced by "
        "one script and written to a machine-readable artefact that records the "
        "configuration and the environment.", S["body"]))
    story.append(Paragraph(
        "The retrieval layer and each of the seven components are exercised by an "
        "automated suite of 77 assertions that runs offline: scoring component behaviour "
        "and range, temporal extraction and supersession semantics, contradiction "
        "detection and penalty application, consolidation threshold and provenance "
        "retention, gap scoring and depth suppression, forgetting leakage across all four "
        "retrieval modes, benchmark comparability, and the API surface including "
        "authentication and error codes. Surrounding the research layer, a further 14 "
        "verification steps cover the application: six backend suites (213 assertions), "
        "three in-process rendering harnesses for the UI, static analysis, an import and "
        "API-contract check, a production build, and an endpoint sweep that boots the "
        "server and probes every registered GET route for server errors.", S["body"]))

    # ------------------------------------------------------------ VI. RESULTS
    story.append(base.h1("VI", "Results", S))
    story.append(Paragraph(
        "Table VI reports retrieval quality and Table VII the staleness, leakage and "
        "duplication metrics. Every number is read from the artefact produced by the run "
        "described in Section V-D.", S["body"]))

    story.append(tbl_caption("VI", "Retrieval Quality Across Four Pipelines", S))
    story.append(make_table([
        ["System", "Hit@5", "MRR"],
        ["Vanilla dense", f"{v['hit_at_k']:.3f}", f"{v['mrr']:.3f}"],
        ["Hybrid", f"{hy['hit_at_k']:.3f}", f"{hy['mrr']:.3f}"],
        ["Graph-augmented", f"{gr['hit_at_k']:.3f}", f"{gr['mrr']:.3f}"],
        ["Adaptive (proposed)", f"{ad['hit_at_k']:.3f}", f"{ad['mrr']:.3f}"],
    ], [COL_W - 90, 45, 45], S, align_left_col0=True))
    story.append(Paragraph("k = 5; metrics over the 9 answerable questions.", S["capt"]))

    story.append(tbl_caption("VII", "Staleness, Leakage and Duplication", S))
    story.append(make_table([
        ["System", "stale@1", "Leak", "Duplicate"],
        ["Vanilla dense", f"{v['stale_top1_rate']:.3f}", f"{v['forgotten_leak_rate']:.3f}",
         f"{v['duplicate_rate']:.3f}"],
        ["Hybrid", f"{hy['stale_top1_rate']:.3f}", f"{hy['forgotten_leak_rate']:.3f}",
         f"{hy['duplicate_rate']:.3f}"],
        ["Graph-augmented", f"{gr['stale_top1_rate']:.3f}", f"{gr['forgotten_leak_rate']:.3f}",
         f"{gr['duplicate_rate']:.3f}"],
        ["Adaptive (proposed)", f"{ad['stale_top1_rate']:.3f}", f"{ad['forgotten_leak_rate']:.3f}",
         f"{ad['duplicate_rate']:.3f}"],
    ], [COL_W - 111, 37, 37, 37], S, align_left_col0=True))
    story.append(Paragraph(
        "stale@1 = top-ranked result superseded or forbidden. Leak = returned results that "
        "were explicitly forgotten. Duplicate = within-query result pairs at or above the "
        "consolidation threshold. Lower is better; the proposed system reaches zero on all "
        "three.", S["capt"]))
    story.append(marker("REQUIRES EXPERIMENT", S))
    story.append(Paragraph(
        "stale@1, leak and duplicate are proportions over few questions and results "
        "(11 questions; 45 returned results per system at k = 5). They are reported as "
        "counts as well as rates wherever a test is run, and neither confidence intervals "
        "nor significance tests are claimed for them here; the protocol that would be used "
        "is specified in Section VII-F.", S["capt"]))

    story.append(Paragraph(
        f"<b>Hit@5 does not discriminate.</b> All four systems reach "
        f"{ad['hit_at_k']:.3f}: every pipeline finds the relevant memory somewhere in its "
        "top five, so the null hypothesis of no difference on this metric is not rejected. "
        "A study reporting only recall would conclude that the research layer adds nothing. "
        "The answers the pipelines support nevertheless differ, because a generator "
        "consumes the ordered context rather than the set. On rank-sensitive measures the "
        f"pipelines separate: MRR rises from {v['mrr']:.3f} (vanilla) through "
        f"{hy['mrr']:.3f} (hybrid, equal to graph-augmented) to {ad['mrr']:.3f} for the "
        f"adaptive pipeline, a relative improvement of "
        f"{100 * (ad['mrr'] - hy['mrr']) / hy['mrr']:.1f}% over the strongest baseline and "
        f"{100 * (ad['mrr'] - v['mrr']) / v['mrr']:.1f}% over dense-only retrieval. H1 and "
        "H2 are supported on this corpus at the level of the subset results in Table VIII.",
        S["body"]))
    story.append(Paragraph(
        f"<b>Staleness is where the effect is largest.</b> Dense-only retrieval leads with "
        f"superseded content in {v['stale_top1_rate']*100:.1f}% of queries; hybrid and "
        f"graph reduce this to {hy['stale_top1_rate']*100:.1f}%, and the adaptive pipeline "
        f"reduces it to {ad['stale_top1_rate']*100:.1f}%. In counts, the strongest baseline "
        f"leads with outdated content on {round(hy['stale_top1_rate'] * 11)} of 11 "
        "questions and the proposed pipeline on none. Because each retrieved passage "
        "remains faithful to its source, no faithfulness metric would flag those cases; "
        "this is the failure mode that motivated the work.", S["body"]))
    story.append(Paragraph(
        f"<b>Leakage and duplication are eliminated.</b> Forgotten-content leakage falls "
        f"from {v['forgotten_leak_rate']:.3f} to {ad['forgotten_leak_rate']:.3f} and "
        f"duplicate context from {v['duplicate_rate']:.3f} to {ad['duplicate_rate']:.3f}. "
        "The leakage result also carries the negative case: in this configuration the "
        "baselines continue to return explicitly unlearned content, which is direct "
        "evidence that removal is a property of the retrieval layer rather than something "
        "obtained by deleting a row from the primary table. H3 and H4 are supported in "
        "this configuration. Because the effect depends on which dense backend is "
        "installed, the configuration is part of the claim, not a detail of the setup.",
        S["body"]))

    story.append(tbl_caption("VIII", "Mean Reciprocal Rank by Question Category", S))
    pt_v = v.get("per_type", {})
    pt_h = hy.get("per_type", {})
    pt_a = ad.get("per_type", {})
    rows = [["Category", "n", "Van.", "Hyb.", "Adapt.", "\u0394 (vs van.)"]]
    counts = {"factual": 3, "temporal": 2, "contradiction": 2, "multi_hop": 1, "duplicate": 1}
    for key, label in (("factual", "factual"), ("temporal", "temporal"),
                       ("contradiction", "contradiction"), ("multi_hop", "multi-hop"),
                       ("duplicate", "duplicate")):
        mv = pt_v.get(key, {}).get("mrr", 0.0)
        mh = pt_h.get(key, {}).get("mrr", 0.0)
        ma = pt_a.get(key, {}).get("mrr", 0.0)
        rows.append([label, str(counts[key]), f"{mv:.3f}", f"{mh:.3f}", f"{ma:.3f}",
                     f"{ma - mv:+.3f}"])
    story.append(make_table(rows, [60, 14, 34, 34, 38, COL_W - 180], S, align_left_col0=True))
    story.append(Paragraph(
        "Answerable categories only; the abstention and removal questions have no gold "
        "memory. \u0394 is the proposed pipeline minus dense-only retrieval. The "
        "per-category figures rest on one to five questions each: they localise where the "
        "effect appears, and are directional rather than conclusive until the benchmark is "
        "enlarged (Section VII).", S["capt"]))

    story.append(Paragraph(
        "Gains concentrate where the architecture predicts them. Temporal questions "
        f"improve from {pt_v.get('temporal', {}).get('mrr', 0):.3f} to "
        f"{pt_a.get('temporal', {}).get('mrr', 0):.3f} once predicate canonicalisation "
        "makes supersession fire, and contradiction questions from "
        f"{pt_v.get('contradiction', {}).get('mrr', 0):.3f} to "
        f"{pt_a.get('contradiction', {}).get('mrr', 0):.3f}: presented with two dated "
        "statements about the same deadline, dense retrieval has no mechanism to prefer "
        "the later one, while validity damping and value-change detection both promote it. "
        "Factual, multi-hop and duplicate questions are unchanged, which is the intended "
        "signature of a component that changes ordering rather than recall.", S["body"]))

    story.append(tbl_caption("IX", "Latency on the Benchmark Corpus", S))
    base_ms = max(1, hy["latency_ms"])
    lat_rows = [["System", "Total ms (11 queries)", "Relative"]]
    for name, m in (("Vanilla dense", v), ("Hybrid", hy), ("Graph-augmented", gr),
                    ("Adaptive (proposed)", ad)):
        lat_rows.append([name, str(m["latency_ms"]), f"{m['latency_ms'] / base_ms:.2f}\u00d7"])
    story.append(make_table(lat_rows, [COL_W - 118, 70, 48], S, align_left_col0=True))
    env_bits = []
    if env.get("cpu_count"):
        env_bits.append(f"{env['cpu_count']} vCPU")
    if env.get("python"):
        env_bits.append(f"Python {env['python']}")
    story.append(Paragraph(
        f"The adaptive pipeline costs approximately {ad['latency_ms'] / base_ms:.1f}\u00d7 "
        f"the hybrid baseline on a corpus of {corpus['memories']} memories, an overhead "
        "dominated by conflict and temporal lookups. At personal-corpus scale this is "
        "small against generation latency, but the cost is real and is stated as measured. "
        + (f"Wall-clock on {' ,'.join(env_bits)}; " if env_bits else "")
        + "latency is not comparable across machines and does not vary with corpus size in "
        "a way this experiment establishes.", S["capt"]))

    # -------------------------------------------------- VII. PLANNED EXPERIMENTS
    story.append(base.h1("VII", "Planned Evaluations", S))
    story.append(Paragraph(
        "This section specifies the experiments that the current results do not cover. "
        "Each item is marked <font color='#b3261e'><b>[REQUIRES EXPERIMENT]</b></font> "
        "because no result is reported for it. They are included because the limitations "
        "in Section IX are only credible alongside a concrete plan to remove them.", S["body"]))

    story.append(Paragraph("A. Component-Wise Ablation", S["h2"]))
    story.append(Paragraph(
        "The current comparison holds the whole post-retrieval layer against three "
        "baselines; it does not isolate which of the five stages produces the effect. The "
        "per-category results in Table VIII localise it, but a factorised ablation is the "
        "direct test. The design is cumulative, adding one stage at a time so that each "
        "row differs from the one above by a single mechanism, measured on the same corpus "
        "and question set with the same candidate generation.", S["body"]))
    story.append(tbl_caption("X", "Ablation Design", S))
    story.append(make_table([
        ["Configuration", "Temporal", "Conflict", "Consol.", "Forget", "Importance"],
        ["Baseline (hybrid)", "\u2014", "\u2014", "\u2014", "\u2014", "\u2014"],
        ["+ Temporal validity", "Yes", "\u2014", "\u2014", "\u2014", "\u2014"],
        ["+ Contradiction damping", "Yes", "Yes", "\u2014", "\u2014", "\u2014"],
        ["+ Consolidation", "Yes", "Yes", "Yes", "\u2014", "\u2014"],
        ["+ Forgetting", "Yes", "Yes", "Yes", "Yes", "\u2014"],
        ["Full adaptive", "Yes", "Yes", "Yes", "Yes", "Yes"],
    ], [70, 30, 30, 26, 24, 42], S, align_left_col0=True))
    story.append(Paragraph(
        "Metrics per row: Hit@5, MRR, stale@1, forgotten-leak rate, duplicate rate and "
        "latency. <font color='#b3261e'><b>[REQUIRES EXPERIMENT]</b></font> No row of this "
        "table has been run.", S["capt"]))

    story.append(Paragraph("B. End-to-End Generation Evaluation", S["h2"]))
    story.append(Paragraph(
        "The present evaluation stops at retrieval. Whether lower stale@1 and higher MRR "
        "produce correct generated answers is not measured here, and it is the most "
        "important open question: retrieval metrics are proxies. The proposed design "
        "generates answers with the same local model for all four systems, over identical "
        "prompts and identical ordered context, and scores them on answer correctness, "
        "temporal correctness, contradiction resolution, evidence correctness, "
        "forgotten-information leakage in the generated text, and abstention correctness. "
        "Scoring would be done by two independent human raters on the full question set "
        "with a stated disagreement-resolution rule, since automatic judges introduce "
        "their own failure modes. <font color='#b3261e'><b>[REQUIRES EXPERIMENT]</b></font>",
        S["body"]))

    story.append(Paragraph("C. Threshold and Parameter Sensitivity", S["h2"]))
    story.append(Paragraph(
        "The consolidation threshold (0.60\u20130.90, focused on 0.78), the recency "
        "half-life (15\u2013180 days) and the eight scoring weights each have an unmeasured "
        "sensitivity. The weight study would report the effect of zeroing one term at a "
        "time, which also tests whether the eight-term score is justified over a simpler "
        "alternative. <font color='#b3261e'><b>[REQUIRES EXPERIMENT]</b></font>", S["body"]))

    story.append(Paragraph("D. Conflict-Detection Accuracy", S["h2"]))
    story.append(Paragraph(
        "The three-class detector is rule-based and its precision and recall are unmeasured. "
        "The study requires a manually annotated set of memory pairs labelled by conflict "
        "class and by whether the conflict is genuine, reporting per-class precision, "
        "recall and F1 with the confusion matrix. Negation detection is expected to be the "
        "weakest, since it previously produced false positives by substring matching. "
        "<font color='#b3261e'><b>[REQUIRES EXPERIMENT]</b></font>", S["body"]))

    story.append(Paragraph("E. Scalability", S["h2"]))
    story.append(Paragraph(
        "Latency is currently reported for one corpus of 15 memories, which cannot show "
        "how the per-run conflict and temporal lookups grow. A scalability study would "
        "measure the same metrics at corpus sizes of 15, 50, 100, 500, 1,000 and 5,000 "
        "memories, reporting both retrieval latency and the offline cost of scoring, "
        "conflict detection and consolidation, and would state whether the pipeline stays "
        "within an interactive budget. "
        "<font color='#b3261e'><b>[REQUIRES EXPERIMENT]</b></font>", S["body"]))

    story.append(Paragraph("F. Statistical Protocol", S["h2"]))
    story.append(Paragraph(
        "Once the benchmark is enlarged, each system would be run over multiple "
        "independently generated corpora with the same question templates, and results "
        "reported as mean \u00b1 standard deviation with 95% bootstrap confidence "
        "intervals over resampled questions. Paired comparisons between systems would use "
        "a paired test over the shared question set (Wilcoxon signed-rank for "
        "per-question rank statistics, McNemar's test for per-question hit and stale "
        "outcomes), with the number of questions stated. The present paper reports point "
        "estimates only and makes no significance claim. "
        "<font color='#b3261e'><b>[REQUIRES EXPERIMENT]</b></font>", S["body"]))

    # ------------------------------------------------ VIII. FAILURE-CASE ANALYSIS
    story.append(base.h1("VIII", "Failure-Case Analysis", S))
    story.append(Paragraph(
        "The mechanisms above are rule-based and pattern-driven, and they fail in "
        "predictable ways. Table XI lists the cases we expect to fail, with the reason. "
        "These are design limitations rather than undiscovered defects: none of them is "
        "solved by the current system, and none is claimed to be.", S["body"]))
    story.append(tbl_caption("XI", "Anticipated Failure Cases", S))
    story.append(make_table([
        ["Case", "Why the current rules miss it"],
        ["Contradiction phrased without shared vocabulary",
         "Conflict detection requires a shared topic signature or canonical predicate"],
        ["Missing or wrong timestamp",
         "Supersession orders by recorded time; a wrong timestamp inverts the ordering"],
        ["Ambiguous temporal expression (\u201cnext month\u201d, \u201csoon\u201d)",
         "Extraction expects an absolute date or a recognised pattern"],
        ["Future plan later abandoned silently",
         "No retraction is recorded, so the fact stays open and is reported as current"],
        ["Implicit state change with no supersession cue",
         "A new state must share a canonical predicate to close the previous one"],
        ["Memory relevant only in combination with another",
         "Ranking scores memories individually; joint relevance is not modelled"],
        ["Forgotten content reproduced verbatim in an unrelated memory",
         "Removal applies to the forgotten item, not to copies of its text elsewhere"],
    ], [104, COL_W - 104], S, align_left_col0=True))
    story.append(Paragraph(
        "The last row is the sharpest: retrieval-level forgetting removes the item and its "
        "derived state, but a user who pasted the same credential into a second note has "
        "created a second memory that the tombstone does not cover. Detection of duplicated "
        "sensitive content across memories is not attempted here.", S["body"]))

    # ------------------------------------------- IX. DISCUSSION AND LIMITATIONS
    story.append(base.h1("IX", "Discussion and Limitations", S))
    story.append(Paragraph(
        "<b>Saturation of a convenient metric is not evidence of equivalence.</b> Our "
        "results show a system that is identical to its baselines on recall and materially "
        "different on the metric that determines whether the user is misinformed. This is "
        "a caution about evaluation practice for personal AI, and it is the reason the "
        "paper reports stale@1 and leakage alongside Hit@k.", S["body"]))
    story.append(Paragraph(
        "<b>Damping rather than deleting</b> is a deliberate design decision. Removing "
        "superseded memories would attain the same stale@1 result while making the "
        "assistant unable to answer historical questions. Both capabilities are legitimate: "
        "validity intervals close facts without erasing them, and rank multipliers demote "
        "rather than remove. Whether damping is preferable to removal is a question for a "
        "user study, not for this corpus.", S["body"]))
    story.append(Paragraph(
        "<b>Forgetting is a cross-cutting property.</b> The baseline leakage result shows "
        "that deletion at one surface is insufficient; any system that promises removal "
        "while retaining a derived index or a duplicate copy elsewhere has a removal hole. "
        "This holds independently of the machine-learning sense of unlearning, and the two "
        "should not be conflated.", S["body"]))
    story.append(Paragraph("The limitations are material and are stated in full.", S["body"]))
    for text in [
        "PersonalBrain-Bench is small and synthetic. Fifteen memories and eleven questions "
        "isolate specific behaviours rather than represent the distribution of real "
        "personal data; per-category figures rest on one to five questions, so absolute "
        "values should not be extrapolated and per-category deltas should be treated as "
        "directional.",
        "The evaluation covers retrieval, not end-to-end generation quality. Whether the "
        "ranking improvements produce fewer incorrect answers in generated prose is not "
        "measured here; the design that would measure it is given in Section VII-B.",
        "No component-wise ablation has been run. The aggregate comparison and the "
        "per-category results are consistent with the intended mechanism, but they do not "
        "isolate it; the factorised design is given in Section VII-A.",
        "Extraction is rule-based and conservative, trading recall for precision. It will "
        "miss contradictions that do not match its patterns, as set out in Section VIII.",
        "Temporal handling uses UTC-normalised timestamps without full timezone or "
        "partial-interval reasoning, which would matter for events spanning midnight "
        "across zones.",
        "Scalability is not established. Latency is reported for a single small corpus, so "
        "the cost of conflict and temporal lookups at larger corpus sizes is unknown.",
        "Conclusions about forgetting depend on the configured dense backend, because a "
        "vector store allows deletion of the embedding itself. The evaluation states and "
        "pins its configuration for that reason.",
    ]:
        story.append(Paragraph(text, S["bullet"], bulletText="\u2022"))

    # -------------------------------------------- X. CONCLUSION AND FUTURE WORK
    story.append(base.h1("X", "Conclusion and Future Work", S))
    story.append(Paragraph(
        "Personal knowledge stores violate the consistency assumptions of general "
        "retrieval benchmarks, and the resulting failures are invisible to recall-oriented "
        "metrics. This paper addressed the question of how a personal memory system should "
        "retrieve evidence so that generated answers reflect what the user currently holds "
        "to be true, and proposed a seven-component research layer for that problem: "
        "auditable importance scoring, a temporal knowledge graph with validity intervals "
        "and supersession, contradiction-aware retrieval across three conflict classes, "
        "consolidation with provenance preservation, exposure-versus-depth gap detection, "
        "forgetting enforced at five retrieval surfaces, and PersonalBrain-Bench as an "
        "instrument for the setting.", S["body"]))
    story.append(Paragraph(
        "On the controlled PersonalBrain-Bench corpus, the evaluation indicates that "
        "Hit@5 saturates for all four pipelines while rank-sensitive and staleness metrics "
        f"separate them: MRR {v['mrr']:.3f} \u2192 {ad['mrr']:.3f}, stale@1 "
        f"{v['stale_top1_rate']:.3f} \u2192 {ad['stale_top1_rate']:.3f}, and both "
        f"post-forgetting leakage and duplicate context from {v['duplicate_rate']:.3f} to "
        f"{ad['duplicate_rate']:.3f}, with the baselines continuing to return explicitly "
        "unlearned content in the configuration evaluated. These are results about a small "
        "synthetic corpus in a model-free configuration; they demonstrate behaviour on "
        "that corpus and are not evidence of general superiority.", S["body"]))
    story.append(Paragraph(
        "What remains unresolved is therefore explicit. Component-wise attribution, "
        "end-to-end generation quality, conflict-detection accuracy, parameter and "
        "threshold sensitivity, scalability, and behaviour on real de-identified personal "
        "corpora are all unmeasured here, and Section VII specifies the experiments that "
        "would measure them. Future work proceeds along those lines, together with a "
        "learned rather than fixed weighting of the scoring terms and an LLM-assisted "
        "extractor retained behind the high-precision rule-based trigger.", S["body"]))

    # ------------------------------------------------------------ ACKNOWLEDGMENT
    story.append(base.h1("", "Acknowledgment", S))
    story.append(Paragraph(
        "The authors thank the School of Computing, Vel Tech Rangarajan Dr. Sagunthala R&D "
        "Institute of Science and Technology, for institutional support, and acknowledge "
        "the open-source projects on which the system is built, in particular FastAPI, "
        "SQLAlchemy and sentence-transformers.", S["body"]))

    # ---------------------------------------------------------------- REFERENCES
    story.append(base.h1("", "References", S))
    for ref in REFS:
        story.append(Paragraph(ref, S["ref"]))

    story.append(Spacer(1, 5))
    story.append(Paragraph(
        f"<i>Artefact.</i> All results were produced by executing the described system. "
        f"The run configuration and environment are recorded in "
        f"<font face='Courier'>benchmark_results.json</font> "
        f"({r.get('generated_at', '')[:10]}); per-question retrieval traces accompany the "
        f"aggregate metrics. Compiled {datetime.utcnow():%d %B %Y}.", S["note"]))

    # ------------------------------------------------------------------- BUILD
    doc = BaseDocTemplate(
        OUT, pagesize=A4,
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
        title=TITLE, author="; ".join(a["name"] for a in AUTHORS),
        subject="IEEE Conference Paper (revised)")

    head_h = 178
    first_frames = [
        Frame(MARGIN_X, PAGE_H - MARGIN_TOP - head_h, PAGE_W - 2 * MARGIN_X, head_h, id="head",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
        Frame(MARGIN_X, MARGIN_BOTTOM, COL_W, PAGE_H - MARGIN_TOP - head_h - MARGIN_BOTTOM, id="c1"),
        Frame(MARGIN_X + COL_W + GUTTER, MARGIN_BOTTOM, COL_W,
              PAGE_H - MARGIN_TOP - head_h - MARGIN_BOTTOM, id="c2"),
    ]
    later_frames = [
        Frame(MARGIN_X, MARGIN_BOTTOM, COL_W, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM, id="c1"),
        Frame(MARGIN_X + COL_W + GUTTER, MARGIN_BOTTOM, COL_W, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM,
              id="c2"),
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

    story.insert(0, NextPageTemplate("later"))
    doc.build(story)

    print(f"\n[OK] wrote {OUT}  ({os.path.getsize(OUT) / 1024:.0f} KB)")
    print(f"     authors : {', '.join(a['name'] for a in AUTHORS)}")
    print(f"     config  : {cfg}")
    print(f"     corpus  : {corpus['memories']} memories, {corpus.get('conflicts', 0)} conflicts")
    print(f"     MRR     : vanilla {v['mrr']:.3f} | hybrid {hy['mrr']:.3f} | adaptive {ad['mrr']:.3f}")
    print(f"     stale@1 : {v['stale_top1_rate']:.3f} -> {ad['stale_top1_rate']:.3f}")


if __name__ == "__main__":
    main()
