#!/usr/bin/env python3
"""
Export every number in the paper straight from the benchmark artefacts.
=======================================================================
The paper used to be transcribed by hand from terminal output, which is how a
table can drift out of sync with the code that produced it. This script reads
the JSON artefacts and writes LaTeX: one file per table plus a macro file for
numbers that appear in running text.

    backend/benchmark_results.json            -> generated/tab_core.tex, tab_category.tex
    backend/benchmark_multi_user_results.json -> generated/tab_personas.tex
    backend/ablation_results.json             -> generated/tab_ablation.tex
    backend/scaling_results.json              -> generated/tab_scaling.tex
    backend/stats_results.json                -> generated/tab_bootstrap.tex, tab_loo.tex
    backend/conflict_accuracy_results.json    -> generated/nli_numbers.tex

and generated/metrics.tex, which defines macros such as
\\CoreAdaptiveMRR. main.tex \\input{s} those files, so re-running the benchmarks
and this script updates the paper. Nothing is typed twice.

Usage:
    python backend/scripts/export_paper_metrics.py
    python backend/scripts/export_paper_metrics.py --paper-dir ../paper
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PAPER_DIR = BACKEND_DIR.parent / "paper"

MODE_LABELS = {
    "vanilla": "TF-IDF vector",
    "hybrid": "Hybrid",
    "graph": "Graph-aug.",
    "adaptive": "Adaptive",
    "adaptive_graph": "Adaptive+graph",
}
MODE_ORDER = ("vanilla", "hybrid", "graph", "adaptive", "adaptive_graph")


# --------------------------------------------------------------------- helpers
def load(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        print(f"  ! missing artifact: {path.name}")
        return None
    return json.loads(path.read_text())


def f3(value: Any, default: str = "--") -> str:
    """Format a metric to three decimals, or a placeholder if absent."""
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return default


def write(path: Path, body: str) -> None:
    path.write_text(body.strip() + "\n", encoding="utf-8")
    print(f"  wrote {path.relative_to(path.parents[2])}")


def tex_escape(text: str) -> str:
    for old, new in (("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#"), ("$", r"\$")):
        text = text.replace(old, new)
    return text



def wrap_table(rows: str, caption: str, label: str, colspec: str, header: str,
               note: str = "", size: str = "footnotesize", tabcolsep: str = "3pt") -> str:
    """Emit a complete table float.

    Generated artefacts contain whole floats rather than bare row bodies on
    purpose: \\input inside a tabular ends the alignment context and the next
    \\bottomrule fails with "Misplaced \\noalign". Including a complete
    environment at top level has no such restriction.
    """
    note_tex = (f"\n\\par\\vspace{{2pt}}\n\\raggedright\\scriptsize {note}" if note else "")
    return (
        "\\begin{table}[t]\n"
        f"\\caption{{{caption}}}\n"
        f"\\label{{{label}}}\n"
        "\\centering\n"
        f"\\{size}\n"
        f"\\setlength{{\\tabcolsep}}{{{tabcolsep}}}\n"
        f"\\begin{{tabular}}{{{colspec}}}\n"
        "\\toprule\n"
        f"{header} \\\\\n"
        "\\midrule\n"
        f"{rows}\n"
        "\\bottomrule\n"
        "\\end{tabular}"
        f"{note_tex}\n"
        "\\end{table}"
    )


# ---------------------------------------------------------------------- tables
def tab_core(core: Dict[str, Any]) -> str:
    rows = []
    for mode in MODE_ORDER:
        metrics = core["results"].get(mode)
        if not metrics:
            continue
        rows.append(
            f"{MODE_LABELS[mode]} & {f3(metrics['hit_at_k'])} & {f3(metrics['mrr'])} & "
            f"{f3(metrics['stale_top1_rate'])} & {f3(metrics['forgotten_leak_rate'])} & "
            f"{f3(metrics['duplicate_rate'])} \\\\"
        )
    return "\n".join(rows)


def tab_category(core: Dict[str, Any]) -> str:
    adaptive = core["results"].get("adaptive", {})
    per_type = adaptive.get("per_type", {})
    baseline = core["results"].get("hybrid", {}).get("per_type", {})
    rows = []
    for qtype in ("factual", "temporal", "contradiction", "multi_hop", "duplicate"):
        entry = per_type.get(qtype)
        if not entry:
            continue
        n = entry["n"]
        hybrid_mrr = baseline.get(qtype, {}).get("mrr")
        delta = ""
        if hybrid_mrr is not None:
            delta = f"${entry['mrr'] - hybrid_mrr:+.3f}$"
        rows.append(f"{qtype.replace('_', ' ').capitalize()} & {n} & {f3(hybrid_mrr)} & "
                    f"{f3(entry['mrr'])} & {delta} \\\\")
    return "\n".join(rows)


def tab_personas(multi: Dict[str, Any]) -> str:
    rows = []
    summary = multi.get("summary", multi.get("metrics", {}))
    for mode in MODE_ORDER:
        m = summary.get(mode)
        if not m:
            continue
        rows.append(
            f"{MODE_LABELS[mode]} & {f3(m.get('hit_at_5'))} & {f3(m.get('mrr'))} & "
            f"{f3(m.get('stale_top1_rate'))} & {f3(m.get('leak_rate'))} \\\\"
        )
    return "\n".join(rows)


def _items_returned(core: Dict[str, Any]) -> str:
    """Total retrieved items per mode, joined for the Table II footnote."""
    counts = []
    for mode in MODE_ORDER:
        per_q = core.get("results", {}).get(mode, {}).get("per_question") or []
        if per_q:
            counts.append(str(sum(len(row.get("retrieved") or []) for row in per_q)))
    return ", ".join(counts[:-1]) + " and " + counts[-1] if len(counts) > 1 else ", ".join(counts)


def tab_ablation(stats: Dict[str, Any]) -> str:
    rows = []
    for row in stats.get("leave_one_out", []):
        label = tex_escape(row["configuration"])
        rows.append(
            f"{label} & {f3(row['mrr'])} & {f3(row['stale_at_1'])} & "
            f"{f3(row['duplicate_rate'])} & {f3(row['leak_rate'])} \\\\"
        )
    return "\n".join(rows)


def tab_scaling(scaling: Dict[str, Any]) -> str:
    rows = []
    pool = scaling.get("pool", [])
    by_size: Dict[int, Dict[str, Any]] = {}
    for row in scaling.get("rows", []):
        by_size.setdefault(row["decoys"], {})[row["mode"]] = row

    for decoys in pool:
        block = by_size.get(decoys, {})
        if not block:
            continue
        memories = next(iter(block.values()))["memories"]
        for mode in ("hybrid", "graph", "adaptive"):
            row = block.get(mode)
            if not row:
                continue
            label = f"{memories} mem." if mode == "hybrid" else ""
            rows.append(
                f"{label} & {MODE_LABELS[mode]} & {f3(row['hit_at_5'])} & {f3(row['mrr'])} & "
                f"{f3(row['evidence_recall'])} & {f3(row['stale_at_1'])} & "
                f"{f3(row['duplicate_rate'])} & {f3(row['leak_rate'])} \\\\"
            )
    return "\n".join(rows)


def tab_cumulative(ablation: Dict[str, Any]) -> str:
    """One mechanism added per row, in the order the pipeline enables them."""
    rows = []
    for row in ablation.get("rows", []):
        label = tex_escape(row.get("config", ""))
        rows.append(
            f"{label} & {f3(row['mrr'])} & {f3(row['stale_top1_rate'])} & "
            f"{f3(row['duplicate_rate'])} & {f3(row['forgotten_leak_rate'])} \\\\"
        )
    return "\n".join(rows)


def tab_bootstrap(stats: Dict[str, Any]) -> str:
    """Paired bootstrap: MRR and stale@1 deltas with percentile intervals."""
    rows = []
    persona = (stats.get("personas") or {}).get("cluster_bootstrap", {})
    core = (stats.get("core") or {}).get("bootstrap", {})
    short = {
        "adaptive_vs_vanilla": "vs TF-IDF",
        "adaptive_vs_hybrid": "vs hybrid",
        "adaptive_vs_graph": "vs graph",
        "adaptive_graph_vs_adaptive": "graph+ad. vs ad.",
    }
    for scope, data in (("Core", core), ("Personas", persona)):
        for name, row in data.items():
            if "delta_mrr" not in row:
                continue
            label = short.get(name, name.replace("_", " "))
            lo, hi = row.get("ci95", [0.0, 0.0])
            s_lo, s_hi = row.get("stale_ci95", [0.0, 0.0])
            rows.append(
                f"{tex_escape(scope)} & {tex_escape(label)} & ${row['delta_mrr']:+.3f}$ & "
                f"$[{lo:+.3f}, {hi:+.3f}]$ & ${row.get('delta_stale_at_1', 0.0):+.3f}$ & "
                f"$[{s_lo:+.3f}, {s_hi:+.3f}]$ \\\\"
            )
        rows.append("\\midrule")
    if rows and rows[-1] == "\\midrule":
        rows.pop()
    return "\n".join(rows)


def nli_numbers(dev: Dict[str, Any], hold: Dict[str, Any],
                core: Dict[str, Any]) -> str:
    """Macros for the conflict-detection paragraph of Section IV-C."""
    lines = ["% generated from conflict_accuracy{,_holdout}.json"]
    for prefix, block in (("Dev", dev), ("Hold", hold)):
        if not block:
            continue
        row = _prf(block)
        lines.append(f"\\newcommand{{\\Nli{prefix}Pairs}}{{{int(row['pairs'])}}}")
        if row["positives"] is not None:
            lines.append(f"\\newcommand{{\\Nli{prefix}Positives}}{{{int(row['positives'])}}}")
        for name, key in (("Precision", "precision"), ("Recall", "recall"), ("Fone", "f1")):
            if row[key] is not None:
                lines.append(f"\\newcommand{{\\Nli{prefix}{name}}}{{{f3(row[key])}}}")
        for name, key in (("Tp", "tp"), ("Fp", "fp"), ("Fn", "fn")):
            if row[key] is not None:
                lines.append(f"\\newcommand{{\\Nli{prefix}{name}}}{{{int(row[key])}}}")
        # class breakdown
        for cls, vals in (block.get("per_class") or {}).items():
            tag = "".join(part.capitalize() for part in cls.split("_"))
            lines.append(f"\\newcommand{{\\Nli{prefix}{tag}Gold}}{{{int(vals.get('gold', 0))}}}")
            lines.append(f"\\newcommand{{\\Nli{prefix}{tag}Detected}}{{{int(vals.get('detected', 0))}}}")
    # Back-compatible aliases point at the development split.
    for name in ("Precision", "Recall", "Fone", "Tp", "Fp", "Fn"):
        row = _prf(dev)
        key = {"Precision": "precision", "Recall": "recall", "Fone": "f1",
               "Tp": "tp", "Fp": "fp", "Fn": "fn"}[name]
        if row.get(key) is not None:
            value = int(row[key]) if name in ("Tp", "Fp", "Fn") else f3(row[key])
            lines.append(f"\\newcommand{{\\Nli{name}}}{{{value}}}")
    return "\n".join(lines)


# --------------------------------------------------------------------- metrics
def metrics_macros(
    core: Dict[str, Any],
    multi: Dict[str, Any],
    stats: Dict[str, Any],
    scaling: Dict[str, Any],
    conflict: Dict[str, Any],
    ablation: Optional[Dict[str, Any]] = None,
    holdout: Optional[Dict[str, Any]] = None,
) -> str:
    lines = [f"% Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
             "% Source: backend/*.json - do not edit by hand",
             ""]

    corpus = core.get("corpus", {})
    lines += [
        f"\\newcommand{{\\CorpusMemories}}{{{corpus.get('memories', '--')}}}",
        f"\\newcommand{{\\CorpusQuestions}}{{{core.get('results', {}).get('adaptive', {}).get('questions', '--')}}}",
    ]

    answerable = core.get("results", {}).get("adaptive", {}).get("answerable_questions")
    if answerable is not None:
        lines.append(f"\\newcommand{{\\CorpusAnswerable}}{{{answerable}}}")

    questions = core.get("results", {}).get("adaptive", {}).get("questions")
    for mode in MODE_ORDER:
        m = core.get("results", {}).get(mode)
        if not m:
            continue
        suffix = "".join(part.capitalize() for part in mode.split("_"))
        if questions:
            # stale@1 is a rate over all questions; the paper quotes counts
            stale_count = int(round(m["stale_top1_rate"] * questions))
            lines.append(f"\\newcommand{{\\Core{suffix}StaleCount}}{{{stale_count}}}")
        if m.get("evidence_recall") is not None:
            lines.append(f"\\newcommand{{\\Core{suffix}Evid}}{{{f3(m['evidence_recall'])}}}")
        lines += [
            f"\\newcommand{{\\Core{suffix}Hit}}{{{f3(m['hit_at_k'])}}}",
            f"\\newcommand{{\\Core{suffix}Mrr}}{{{f3(m['mrr'])}}}",
            f"\\newcommand{{\\Core{suffix}Stale}}{{{f3(m['stale_top1_rate'])}}}",
            f"\\newcommand{{\\Core{suffix}StaleRate}}{{{f3(m.get('staleness_rate', 0))}}}",
            f"\\newcommand{{\\Core{suffix}Leak}}{{{f3(m['forgotten_leak_rate'])}}}",
            f"\\newcommand{{\\Core{suffix}Dup}}{{{f3(m['duplicate_rate'])}}}",
            f"\\newcommand{{\\Core{suffix}Latency}}{{{m.get('latency_ms', '--')}}}",
        ]

    if multi.get("total_queries") is not None:
        lines.append(f"\\newcommand{{\\PersonaQueries}}{{{int(multi['total_queries'])}}}")
        # per_query holds one row per (question, mode); count questions once.
        per_query = multi.get("per_query") or []
        seen = {(row.get("persona"), row.get("question")) for row in per_query}
        answerable = len({
            (row.get("persona"), row.get("question"))
            for row in per_query if row.get("answerable")
        })
        lines.append(f"\\newcommand{{\\PersonaUniqueQueries}}{{{len(seen)}}}")
        if answerable:
            lines.append(f"\\newcommand{{\\PersonaAnswerable}}{{{answerable}}}")
        if multi.get("personas_evaluated") is not None:
            lines.append(f"\\newcommand{{\\PersonaCount}}{{{int(multi['personas_evaluated'])}}}")

    summary = multi.get("summary", {})
    for mode in MODE_ORDER:
        m = summary.get(mode)
        if not m:
            continue
        suffix = "".join(part.capitalize() for part in mode.split("_"))
        lines += [
            f"\\newcommand{{\\Persona{suffix}Mrr}}{{{f3(m.get('mrr'))}}}",
            f"\\newcommand{{\\Persona{suffix}Stale}}{{{f3(m.get('stale_top1_rate'))}}}",
            f"\\newcommand{{\\Persona{suffix}Leak}}{{{f3(m.get('leak_rate'))}}}",
        ]

    pool = scaling.get("pool", [])
    if pool:
        last = pool[-1]
        block = {row["mode"]: row for row in scaling.get("rows", []) if row["decoys"] == last}
        lines.append(f"\\newcommand{{\\ScaleMaxDecoys}}{{{last}}}")
        if block:
            lines.append(f"\\newcommand{{\\ScaleMemories}}{{{block['hybrid']['memories']}}}")
        if pool:
            first = {row["mode"]: row for row in scaling.get("rows", []) if row["decoys"] == pool[0]}
            if first:
                lines.append(f"\\newcommand{{\\ScaleFirstMemories}}{{{first['hybrid']['memories']}}}")
        for mode in ("hybrid", "adaptive"):
            if mode in block and block[mode].get("evidence_recall") is not None:
                suffix = "".join(part.capitalize() for part in mode.split("_"))
                lines.append(f"\\newcommand{{\\Scale{suffix}Evid}}{{{f3(block[mode]['evidence_recall'])}}}")
        for mode in ("hybrid", "adaptive"):
            if mode in block:
                suffix = "".join(part.capitalize() for part in mode.split("_"))
                lines += [
                    f"\\newcommand{{\\Scale{suffix}Mrr}}{{{f3(block[mode]['mrr'])}}}",
                    f"\\newcommand{{\\Scale{suffix}Dup}}{{{f3(block[mode]['duplicate_rate'])}}}",
                    f"\\newcommand{{\\Scale{suffix}Stale}}{{{f3(block[mode]['stale_at_1'])}}}",
                ]

    abl = ablation.get("rows") or []
    for row in abl:
        config = row.get("config", "")
        tag = "All"
        if config.startswith("+") and config.split()[0] != "+importance":
            tag = "".join(part.capitalize() for part in config.strip("+").split("_"))
        elif "hybrid" in config:
            tag = "Hybrid"
        lines += [
            f"\\newcommand{{\\Abl{tag}Mrr}}{{{f3(row['mrr'])}}}",
            f"\\newcommand{{\\Abl{tag}Stale}}{{{f3(row['stale_top1_rate'])}}}",
            f"\\newcommand{{\\Abl{tag}Dup}}{{{f3(row['duplicate_rate'])}}}",
            f"\\newcommand{{\\Abl{tag}Leak}}{{{f3(row['forgotten_leak_rate'])}}}",
        ]

    core_boot = (stats.get("core") or {}).get("bootstrap", {})
    persona_boot = (stats.get("personas") or {}).get("cluster_bootstrap", {})
    for prefix, data in (("Core", core_boot), ("Persona", persona_boot)):
        row = data.get("adaptive_vs_hybrid")
        if not row:
            continue
        lo, hi = row.get("ci95", [0, 0])
        lines += [
            f"\\newcommand{{\\{prefix}DeltaMrr}}{{{row['delta_mrr']:+.3f}}}",
            f"\\newcommand{{\\{prefix}DeltaMrrLo}}{{{lo:+.3f}}}",
            f"\\newcommand{{\\{prefix}DeltaMrrHi}}{{{hi:+.3f}}}",
        ]
        if "delta_stale_at_1" in row:
            s_lo, s_hi = row.get("stale_ci95", [0, 0])
            lines += [
                f"\\newcommand{{\\{prefix}DeltaStale}}{{{row['delta_stale_at_1']:+.3f}}}",
                f"\\newcommand{{\\{prefix}DeltaStaleLo}}{{{s_lo:+.3f}}}",
                f"\\newcommand{{\\{prefix}DeltaStaleHi}}{{{s_hi:+.3f}}}",
            ]

    tests = load(BACKEND_DIR / "test_results.json")
    if tests:
        lines += [
            f"\\newcommand{{\\TestPassed}}{{{tests.get('passed', '--')}}}",
            f"\\newcommand{{\\TestSkipped}}{{{tests.get('skipped', '--')}}}",
            f"\\newcommand{{\\TestFailed}}{{{tests.get('failed', '--')}}}",
        ]

    # Conflict-detection macros are written to generated/nli_numbers.tex so that
    # this file never defines the same name twice.
    return "\n".join(lines)


# ------------------------------------------------------------------------ main
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-dir", default=str(DEFAULT_PAPER_DIR))
    args = parser.parse_args()

    paper_dir = Path(args.paper_dir).resolve()
    out_dir = paper_dir / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Exporting metrics -> {out_dir}")
    core = load(BACKEND_DIR / "benchmark_results.json")
    multi = load(BACKEND_DIR / "benchmark_multi_user_results.json")
    stats = load(BACKEND_DIR / "stats_results.json")
    scaling = load(BACKEND_DIR / "scaling_results.json")
    ablation = load(BACKEND_DIR / "ablation_results.json")
    conflict = load(BACKEND_DIR / "conflict_accuracy_results.json")
    holdout = load(BACKEND_DIR / "conflict_accuracy_holdout.json")

    if core:
        write(out_dir / "tab_core.tex", wrap_table(
            rows=tab_core(core),
            caption="Reproduced Core-Corpus Retrieval Results",
            label="tab:core",
            colspec="@{}lccccc@{}",
            header=r"\textbf{System} & \textbf{Hit@5} & \textbf{MRR} & \textbf{Stale@1} & \textbf{Leak} & \textbf{Dup.}",
            note="Hit@5 and MRR use \\CorpusAnswerable{} answerable questions; stale@1 uses all "
                 "\\CorpusQuestions{} (\\CoreVanillaStaleCount, \\CoreHybridStaleCount, "
                 "\\CoreGraphStaleCount and \\CoreAdaptiveStaleCount). "
                 f"The systems returned {_items_returned(core)} items, respectively."))
        write(out_dir / "tab_category.tex", wrap_table(
            rows=tab_category(core),
            caption="Reproduced MRR by Question Category",
            label="tab:category",
            colspec="@{}lcccc@{}",
            header=r"\textbf{Category} & \textbf{$n$} & \textbf{Hybrid} & \textbf{Adaptive} & $\boldsymbol{\Delta}$",
            note="$\\Delta$ is adaptive minus hybrid. The two no-gold questions are omitted.",
            tabcolsep="4pt"))
    if multi:
        write(out_dir / "tab_personas.tex", wrap_table(
            rows=tab_personas(multi),
            caption="Isolated Five-Persona Results",
            label="tab:multi",
            colspec="@{}lcccc@{}",
            header=r"\textbf{System} & \textbf{Hit@5} & \textbf{MRR} & \textbf{Stale@1} & \textbf{Leak}",
            note="\\PersonaCount{} isolated synthetic personas: MRR/Hit@5 over \\PersonaAnswerable{} answerable "
                 "queries; stale@1 over \\PersonaQueries{}. Leak is the mean per-query fraction. Graph and hybrid "
                 "coincide because both place every gold item inside the top five.",
            tabcolsep="4pt"))
    if stats:
        write(out_dir / "tab_loo.tex", wrap_table(
            rows=tab_ablation(stats),
            caption="Leave-One-Out Ablation",
            label="tab:loo",
            colspec="@{}lcccc@{}",
            header=r"\textbf{Configuration} & \textbf{MRR} & \textbf{Stale@1} & \textbf{Dup.} & \textbf{Leak}",
            note="Each row removes one mechanism from the full system. Mechanisms whose removal changes no metric "
                 "are reported as neutral rather than as contributing.",
            tabcolsep="4pt"))
        write(out_dir / "tab_bootstrap.tex", wrap_table(
            rows=tab_bootstrap(stats),
            caption="Paired Bootstrap of Adaptive Against Each Baseline",
            label="tab:bootstrap",
            colspec="@{}llcccc@{}",
            header=r"\textbf{Scope} & \textbf{Comparison} & $\boldsymbol{\Delta}$\textbf{MRR} & \textbf{95\% CI} & $\boldsymbol{\Delta}$\textbf{St.@1} & \textbf{95\% CI}",
            size="scriptsize", tabcolsep="2pt",
            note="St.@1 is stale@1. Persona intervals use a cluster bootstrap over personas; core intervals resample questions."))
    if ablation:
        write(out_dir / "tab_cumulative.tex", wrap_table(
            rows=tab_cumulative(ablation),
            caption="Cumulative Ablation: One Mechanism Enabled per Row",
            label="tab:cumulative",
            colspec="@{}lcccc@{}",
            header=r"\textbf{Configuration} & \textbf{MRR} & \textbf{Stale@1} & \textbf{Dup.} & \textbf{Leak}",
            note="Mechanisms are switched on in pipeline order; each row includes every mechanism above it. "
                 "This is a cumulative sequence, not a factorial design.",
            tabcolsep="4pt"))
    elif ablation:
        write(out_dir / "tab_loo.tex", wrap_table(
            rows="\n".join(
                f"{tex_escape(row['config'])} & {f3(row['mrr'])} & {f3(row['stale_top1_rate'])} & "
                f"{f3(row['duplicate_rate'])} & {f3(row['forgotten_leak_rate'])} \\\\"
                for row in ablation.get("rows", [])),
            caption="Leave-One-Out Ablation", label="tab:loo",
            colspec="@{}lcccc@{}",
            header=r"\textbf{Configuration} & \textbf{MRR} & \textbf{Stale@1} & \textbf{Dup.} & \textbf{Leak}"))
    if scaling:
        write(out_dir / "tab_scaling.tex", wrap_table(
            rows=tab_scaling(scaling),
            caption="Distractor Scaling: Questions Fixed, Pool Grown",
            label="tab:scaling",
            colspec="@{}llcccccc@{}",
            header=r"\textbf{Pool} & \textbf{System} & \textbf{Hit@5} & \textbf{MRR} & \textbf{Evid.} & \textbf{Stale@1} & \textbf{Dup.} & \textbf{Leak}",
            tabcolsep="3.5pt",
            note="Evidence recall is the fraction of required gold memories returned for multi-evidence questions. "
                 "Distractors are drawn from the same vocabulary as the corpus but contain no gold key, so they can "
                 "only cost a system rank."))
    if conflict:
        write(out_dir / "nli_numbers.tex", nli_numbers(conflict or {}, holdout or {}, core or {}))

    write(out_dir / "metrics.tex", metrics_macros(
        core or {}, multi or {}, stats or {}, scaling or {}, conflict or {},
        ablation or {}, holdout or {}))

    missing = [name for name, art in (
        ("benchmark_results.json", core),
        ("benchmark_multi_user_results.json", multi),
        ("stats_results.json", stats),
        ("scaling_results.json", scaling),
        ("conflict_accuracy_results.json", conflict),
    ) if art is None]
    if missing:
        print("\n  Incomplete: run the matching script(s) first:")
        for name in missing:
            script = {
                "benchmark_results.json": "scripts/run_bench.py",
                "benchmark_multi_user_results.json": "scripts/run_multi_user_bench.py",
                "stats_results.json": "scripts/run_stats.py",
                "scaling_results.json": "scripts/run_scaling.py",
                "conflict_accuracy_results.json": "scripts/run_conflict_accuracy.py",
            }[name]
            print(f"    python backend/{script}")
    print("\nDone. Recompile paper/main.tex (pdfLaTeX).")


if __name__ == "__main__":
    main()
