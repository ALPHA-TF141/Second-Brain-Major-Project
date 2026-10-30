#!/usr/bin/env python3
"""
Statistical reporting for the paper: bootstrap CIs + leave-one-out ablation.
============================================================================
Replaces the Wilson/Wilcoxon discussion the reviewers objected to, for two
reasons that are stated in the paper's own limitations section:

  1. Query-level tests treat six queries from the same persona as independent
     observations. They are not. The cluster bootstrap resamples PERSONAS, so
     the dependence is in the resampling unit rather than in a caveat.
  2. "No significant difference" from 11 queries is not evidence of no effect.
     A confidence interval shows how wide the uncertainty actually is.

Outputs (backend/stats_results.json):
  bootstrap   ΔMRR / Δstale@1 with 95% percentile CIs, per baseline
  loo         leave-one-out ablation: full system minus each mechanism
  cumulative  the original cumulative ablation, kept for comparison

Usage:
    python backend/scripts/run_stats.py
    BENCH_DENSE_BACKEND=bm25 python backend/scripts/run_stats.py
"""
import json
import os
import sys
from pathlib import Path

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parent.parent
os.chdir(BACKEND_DIR)
sys.path.insert(0, str(BACKEND_DIR))

from app.database.init_db import init_database      # noqa: E402
from app.database.session import SessionLocal       # noqa: E402
from app.research.bench import benchmark_runner     # noqa: E402
from app.research.multi_user_bench import multi_user_benchmark  # noqa: E402

# Leave-one-out: every mechanism on, then each one removed in turn.
# `graph` is handled by switching mode rather than by an ablation flag, because
# the graph expansion runs BEFORE the research layer.
MECHANISMS = ("temporal", "contradiction", "consolidation", "forgetting", "importance")


def bootstrap_delta(a, b, n=10000, seed=0, clusters=None):
    """
    Paired bootstrap of mean(a) - mean(b).

    `clusters` resamples groups instead of individual queries (cluster
    bootstrap). Pass the persona id per query when queries share a persona;
    pass None when every query is independent (single-corpus runs).
    """
    rng = np.random.default_rng(seed)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.size == 0 or b.size == 0:
        return 0.0, 0.0, 0.0

    observed = float(a.mean() - b.mean())
    deltas = np.empty(n, dtype=float)

    if clusters is None:
        for i in range(n):
            idx = rng.integers(0, a.size, a.size)
            deltas[i] = a[idx].mean() - b[idx].mean()
    else:
        clusters = np.asarray(clusters)
        unique = np.unique(clusters)
        for i in range(n):
            picked = rng.choice(unique, unique.size, replace=True)
            idx = np.concatenate([np.flatnonzero(clusters == c) for c in picked])
            deltas[i] = a[idx].mean() - b[idx].mean()

    low, high = np.percentile(deltas, [2.5, 97.5])
    return observed, float(low), float(high)


def _per_query(outcome):
    return [q["reciprocal_rank"] for q in outcome["per_question"] if q.get("answerable")]


def _per_query_stale(outcome):
    return [1.0 if q.get("top1_is_stale") else 0.0 for q in outcome["per_question"]]


def single_corpus(db, dense_backend):
    """Core corpus: 11 questions, no clustering - plain paired bootstrap."""
    ingest = benchmark_runner.load_corpus(db, reset=True)
    key_to_id = ingest["key_to_id"]

    rows = {}
    for mode in ("vanilla", "hybrid", "graph", "adaptive", "adaptive_graph"):
        rows[mode] = benchmark_runner.evaluate(
            db, mode=mode, k=5, key_to_id=key_to_id, dense_backend=dense_backend)

    comparisons = {}
    for baseline in ("vanilla", "hybrid", "graph"):
        observed, low, high = bootstrap_delta(
            _per_query(rows["adaptive"]), _per_query(rows[baseline]))
        s_obs, s_low, s_high = bootstrap_delta(
            _per_query_stale(rows["adaptive"]), _per_query_stale(rows[baseline]))
        comparisons[f"adaptive_vs_{baseline}"] = {
            "delta_mrr": round(observed, 4), "ci95": [round(low, 4), round(high, 4)],
            "delta_stale_at_1": round(s_obs, 4), "stale_ci95": [round(s_low, 4), round(s_high, 4)],
        }

    # Adaptation-vs-graph on top of adaptation
    observed, low, high = bootstrap_delta(
        _per_query(rows["adaptive_graph"]), _per_query(rows["adaptive"]))
    comparisons["adaptive_graph_vs_adaptive"] = {
        "delta_mrr": round(observed, 4), "ci95": [round(low, 4), round(high, 4)],
    }

    return {
        "questions": rows["adaptive"]["questions"],
        "answerable": rows["adaptive"]["answerable_questions"],
        "metrics": {mode: {"mrr": rows[mode]["mrr"], "hit_at_5": rows[mode]["hit_at_k"],
                           "stale_at_1": rows[mode]["stale_top1_rate"],
                           "duplicate_rate": rows[mode]["duplicate_rate"],
                           "leak_rate": rows[mode]["forgotten_leak_rate"]}
                    for mode in rows},
        "bootstrap": comparisons,
        "graph": ingest.get("graph", {}),
    }


def leave_one_out(db, dense_backend):
    """Full system minus one mechanism, plus graph on/off."""
    ingest = benchmark_runner.load_corpus(db, reset=True)
    key_to_id = ingest["key_to_id"]

    full = benchmark_runner.evaluate(db, mode="adaptive_graph", k=5,
                                     key_to_id=key_to_id, dense_backend=dense_backend)
    table = [{
        "configuration": "full (adaptive + graph)",
        "mrr": full["mrr"], "stale_at_1": full["stale_top1_rate"],
        "duplicate_rate": full["duplicate_rate"], "leak_rate": full["forgotten_leak_rate"],
    }]

    # minus graph -> plain adaptive (graph expansion is a mode, not a flag)
    for label, mode, ablation in [("− graph", "adaptive", None)]:
        outcome = benchmark_runner.evaluate(db, mode=mode, k=5, key_to_id=key_to_id,
                                            dense_backend=dense_backend, ablation=ablation)
        table.append({"configuration": label, "mrr": outcome["mrr"],
                      "stale_at_1": outcome["stale_top1_rate"],
                      "duplicate_rate": outcome["duplicate_rate"],
                      "leak_rate": outcome["forgotten_leak_rate"]})

    for dropped in MECHANISMS:
        ablation = {name: (name != dropped) for name in MECHANISMS}
        outcome = benchmark_runner.evaluate(db, mode="adaptive_graph", k=5,
                                            key_to_id=key_to_id,
                                            dense_backend=dense_backend, ablation=ablation)
        table.append({"configuration": f"− {dropped}", "mrr": outcome["mrr"],
                      "stale_at_1": outcome["stale_top1_rate"],
                      "duplicate_rate": outcome["duplicate_rate"],
                      "leak_rate": outcome["forgotten_leak_rate"]})

    return table


def personas(dense_backend):
    """
    Five-persona run, with the cluster bootstrap the paper's limitations section
    asks for: resample PERSONAS, not queries.

    Six queries share each persona, so treating 30 queries as 30 independent
    observations understates the interval. The cluster bootstrap keeps each
    persona's queries together, which is what a mixed-effects model would do
    without the modelling assumptions.
    """
    init_database()
    db = SessionLocal()
    try:
        outcome = multi_user_benchmark.run_benchmark(db)
    finally:
        db.close()

    rows = outcome.get("per_query") or []
    if not rows:
        return {"note": "no per-query rows returned by the persona runner"}

    arrays = {}
    for mode in outcome["summary"]:
        mrr, stale, clusters = [], [], []
        for row in rows:
            if row["mode"] != mode:
                continue
            if row.get("answerable"):
                mrr.append(row.get("mrr", 0.0))
            stale.append(row.get("stale_top1", 0.0))
            clusters.append(row["persona"])
        arrays[mode] = {"mrr": mrr, "stale": stale, "clusters": clusters}

    comparisons = {}
    for baseline in ("vanilla", "hybrid", "graph"):
        if baseline not in arrays:
            continue
        n = min(len(arrays["adaptive"]["mrr"]), len(arrays[baseline]["mrr"]))
        if not n:
            continue
        observed, low, high = bootstrap_delta(
            arrays["adaptive"]["mrr"][:n], arrays[baseline]["mrr"][:n],
            clusters=arrays["adaptive"]["clusters"][:n])
        s_obs, s_low, s_high = bootstrap_delta(
            arrays["adaptive"]["stale"][:n], arrays[baseline]["stale"][:n],
            clusters=arrays["adaptive"]["clusters"][:n])
        comparisons[f"adaptive_vs_{baseline}"] = {
            "delta_mrr": round(observed, 4), "ci95": [round(low, 4), round(high, 4)],
            "delta_stale_at_1": round(s_obs, 4),
            "stale_ci95": [round(s_low, 4), round(s_high, 4)],
        }

    return {"summary": outcome["summary"], "cluster_bootstrap": comparisons}


def main() -> None:
    dense_backend = os.environ.get("BENCH_DENSE_BACKEND", "tfidf")
    print("=" * 78)
    print(f" Statistics: bootstrap CIs and leave-one-out ablation (dense={dense_backend})")
    print("=" * 78)

    init_database()
    db = SessionLocal()
    try:
        core = single_corpus(db, dense_backend)
        loo = leave_one_out(db, dense_backend)
    finally:
        db.close()

    try:
        persona_stats = personas(dense_backend)
    except Exception as exc:  # the persona runner is slower and more fragile
        persona_stats = {"error": f"{type(exc).__name__}: {exc}"}

    print("\nCore corpus - metrics")
    print(f"{'mode':<16} {'MRR':>6} {'hit@5':>6} {'stale@1':>8} {'dup':>6} {'leak':>6}")
    for mode, metrics in core["metrics"].items():
        print(f"{mode:<16} {metrics['mrr']:>6.3f} {metrics['hit_at_5']:>6.3f} "
              f"{metrics['stale_at_1']:>8.3f} {metrics['duplicate_rate']:>6.3f} {metrics['leak_rate']:>6.3f}")

    print("\nBootstrap (95% percentile CI, 10k resamples)")
    for name, row in core["bootstrap"].items():
        print(f"  {name:<30} dMRR={row['delta_mrr']:>+6.3f} "
              f"CI[{row['ci95'][0]:>+6.3f}, {row['ci95'][1]:>+6.3f}]"
              + (f"  dstale={row['delta_stale_at_1']:>+6.3f}" if "delta_stale_at_1" in row else ""))

    print("\nLeave-one-out ablation")
    print(f"{'configuration':<26} {'MRR':>6} {'stale@1':>8} {'dup':>6} {'leak':>6}")
    for row in loo:
        print(f"{row['configuration']:<26} {row['mrr']:>6.3f} {row['stale_at_1']:>8.3f} "
              f"{row['duplicate_rate']:>6.3f} {row['leak_rate']:>6.3f}")

    payload = {"dense_backend": dense_backend, "core": core, "leave_one_out": loo,
               "personas": persona_stats}
    out_path = BACKEND_DIR / "stats_results.json"
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"\nArtifact saved to: {out_path}")


if __name__ == "__main__":
    main()
