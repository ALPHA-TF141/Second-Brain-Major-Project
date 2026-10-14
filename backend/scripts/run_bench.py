#!/usr/bin/env python3
"""
CLI Runner for PersonalBrain-Bench (single user, four pipelines).
=============================================================
Reproduces the metric table of the IEEE paper (hit@5, MRR, stale@1,
staleness over all retrieved items, duplicate rate, forgotten-leak rate)
for the four compared systems: vanilla, hybrid, graph, adaptive.

Every run starts from a FRESH derived-research state (BenchmarkRunner
resets temporal facts, conflicts, consolidations, gaps and tombstones
before ingesting the synthetic corpus), so two consecutive executions
produce identical metrics; only wall-clock latency varies.

Usage (from anywhere):
    python backend/scripts/run_bench.py

Environment:
    BENCH_DENSE_BACKEND   dense backend to request: "tfidf" (default,
                          network-free and deterministic) or "neural"
    BENCH_K               retrieval depth (default 5)

Artifact:
    backend/benchmark_results.json   full per-question, per-type results
"""
import json
import os
import sys
from pathlib import Path

# Anchor to the backend directory so the sqlite URL (./data/second_brain.db)
# and the artifact path resolve identically no matter where this is called
# from.
BACKEND_DIR = Path(__file__).resolve().parent.parent
os.chdir(BACKEND_DIR)
sys.path.insert(0, str(BACKEND_DIR))

from app.database.init_db import init_database  # noqa: E402
from app.database.session import SessionLocal   # noqa: E402
from app.research.bench import benchmark_runner  # noqa: E402


def main() -> None:
    dense = os.environ.get("BENCH_DENSE_BACKEND", "tfidf")
    k = int(os.environ.get("BENCH_K", "5"))

    print("=" * 78)
    print(" PersonalBrain-Bench: single-user evaluation, four pipelines")
    print("=" * 78)

    init_database()
    db = SessionLocal()
    try:
        results = benchmark_runner.run_all(db, k=k, dense_backend=dense)
    finally:
        db.close()

    corpus = results["corpus"]
    config = results["configuration"]
    print(f"\nCorpus: {corpus['memories']} memories, "
          f"{corpus['conflicts']} detected conflicts, k={results['k']}")
    print(f"Configuration: dense_backend={config['dense_backend']} "
          f"(requested {config['dense_backend_requested']}), "
          f"scoring_weights={config['scoring_weights_version']}, "
          f"corpus_scope={config['corpus_scope']}")

    print("\n" + "-" * 78)
    print(f"{'Pipeline':<10} | {'Hit@5':>6} | {'MRR':>6} | {'stale@1':>7} | "
          f"{'stale':>6} | {'dup':>6} | {'leak':>6} | {'latency':>9}")
    print("-" * 78)
    for mode in ("vanilla", "hybrid", "graph", "adaptive"):
        m = results["results"][mode]
        print(f"{mode:<10} | {m['hit_at_k']:>6.3f} | {m['mrr']:>6.3f} | "
              f"{m['stale_top1_rate']:>7.3f} | {m['staleness_rate']:>6.3f} | "
              f"{m['duplicate_rate']:>6.3f} | {m['forgotten_leak_rate']:>6.3f} | "
              f"{m['latency_ms']:>6.1f} ms")
    print("-" * 78)

    print("\nAdaptive vs baselines:")
    for name, delta in results["comparison"].items():
        print(f"  {name:<20} dMRR={delta['mrr_delta']:>+6.3f}  "
              f"dstale={delta['staleness_reduction']:>+6.3f}  "
              f"ddup={delta['duplicate_reduction']:>+6.3f}  "
              f"context={delta['context_reduction_pct']:>+6.1f}%")

    out_path = BACKEND_DIR / "benchmark_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nArtifact saved to: {out_path}")
    print("Evaluation completed successfully.")


if __name__ == "__main__":
    main()
