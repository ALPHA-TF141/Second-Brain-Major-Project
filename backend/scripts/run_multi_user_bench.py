#!/usr/bin/env python3
"""
CLI Runner for Multi-User PersonalBrain-Bench (v2)
Exports results to benchmark_multi_user_results.json
"""
import json
import os
import sys
from pathlib import Path

# Anchor to backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.database.init_db import init_database
from app.database.session import SessionLocal
from app.research.multi_user_bench import multi_user_benchmark


def main():
    print("=" * 70)
    print(" PersonalBrain-Bench v2: Multi-User Neural Benchmark Evaluation")
    print("=" * 70)

    init_database()
    db = SessionLocal()
    try:
        print("\n[1/3] Initializing and running multi-persona evaluation suite...")
        results = multi_user_benchmark.run_benchmark(db, k=5)

        print("\n[2/3] Multi-User Aggregate Results (5 Personas, 30 Queries):")
        print("-" * 70)
        print(f"{'Pipeline':<18} | {'Hit@5':<8} | {'MRR':<8} | {'Stale@1':<10} | {'Leak':<8} | {'Latency':<10}")
        print("-" * 70)
        for mode, m in results["summary"].items():
            print(
                f"{mode:<18} | {m['hit_at_5']:<8.4f} | {m['mrr']:<8.4f} | "
                f"{m['stale_top1_rate']:<10.4f} | {m['leak_rate']:<8.4f} | {m['mean_latency_ms']:<7.2f} ms"
            )
        print("-" * 70)

        print("\n[3/3] Statistical Significance vs Adaptive (Wilcoxon Signed-Rank Test):")
        for base, sig in results["significance"].items():
            sig_str = "YES (p < 0.01)" if sig["significant_at_0_01"] else "NO"
            print(f"  • {base:<12}: Stale p={sig['stale_p_value']:.6f}, MRR p={sig['mrr_p_value']:.6f} -> Statistically Significant: {sig_str}")

        # Save artifact
        out_path = BACKEND_DIR / "benchmark_multi_user_results.json"
        with open(out_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nArtifact saved to: {out_path}")
        print("Evaluation completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
