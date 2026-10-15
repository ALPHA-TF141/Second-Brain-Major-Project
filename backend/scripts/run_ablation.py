#!/usr/bin/env python3
"""
E1 - Component-wise ablation of the research layer (paper Section VI).

Cumulative design: each row adds exactly one mechanism to the previous row,
starting from hybrid retrieval with the whole research layer disabled.
Isolates which mechanism produces the MRR / stale@1 / duplicate / leak
effects reported in Table I.

Usage:  python backend/scripts/run_ablation.py
Artifact: backend/ablation_results.json
"""
import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
os.chdir(BACKEND_DIR)
sys.path.insert(0, str(BACKEND_DIR))

from app.database.init_db import init_database  # noqa: E402
from app.database.session import SessionLocal   # noqa: E402
from app.research.bench import benchmark_runner  # noqa: E402

CONFIGS = [
    ("hybrid (layer off)", "hybrid", None),
    ("+temporal", "adaptive", {"temporal": True}),
    ("+contradiction", "adaptive", {"temporal": True, "contradiction": True}),
    ("+consolidation", "adaptive", {"temporal": True, "contradiction": True,
                                    "consolidation": True}),
    ("+forgetting", "adaptive", {"temporal": True, "contradiction": True,
                                 "consolidation": True, "forgetting": True}),
    ("+importance (full)", "adaptive", {"temporal": True, "contradiction": True,
                                        "consolidation": True, "forgetting": True,
                                        "importance": True}),
]


def main() -> None:
    print("=" * 84)
    print(" E1 ablation: cumulative, one mechanism per row")
    print("=" * 84)

    init_database()
    db = SessionLocal()
    try:
        ingest = benchmark_runner.load_corpus(db, reset=True)
        key_to_id = ingest["key_to_id"]
        rows = []
        for label, mode, ablation in CONFIGS:
            outcome = benchmark_runner.evaluate(
                db, mode=mode, k=5, key_to_id=key_to_id,
                dense_backend="tfidf", ablation=ablation,
            )
            rows.append({
                "config": label,
                "mode": mode,
                "ablation": ablation,
                "hit_at_5": outcome["hit_at_k"],
                "mrr": outcome["mrr"],
                "stale_top1_rate": outcome["stale_top1_rate"],
                "staleness_rate": outcome["staleness_rate"],
                "duplicate_rate": outcome["duplicate_rate"],
                "forgotten_leak_rate": outcome["forgotten_leak_rate"],
                "latency_ms": outcome["latency_ms"],
            })
            print(f"{label:<22} hit@5={outcome['hit_at_k']:.3f} mrr={outcome['mrr']:.3f} "
                  f"stale@1={outcome['stale_top1_rate']:.3f} dup={outcome['duplicate_rate']:.3f} "
                  f"leak={outcome['forgotten_leak_rate']:.3f}")
    finally:
        db.close()

    out = {
        "corpus": {"memories": ingest["memories"], "conflicts": ingest["conflicts"]},
        "k": 5,
        "dense_backend": "tfidf",
        "rows": rows,
    }
    out_path = BACKEND_DIR / "ablation_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nArtifact saved to: {out_path}")


if __name__ == "__main__":
    main()
