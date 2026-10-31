#!/usr/bin/env python3
"""
Distractor-scaling experiment.
==============================
The core corpus has 15 memories and 11 questions, so Hit@5 is 1.000 for every
system and the comparison saturates: a retriever that returns the gold memory at
rank 1 and one that returns it at rank 5 look identical. That is why earlier
versions of this work could not show a graph contribution.

This script holds the QUESTIONS fixed and grows the DISTRACTOR pool instead.
Decoys are topically similar (papers, deadlines, datasets, models, stacks) but
never contain a gold or forbidden key, so they can only cost a system rank -
they can never grant a correct answer. As the pool grows, the metrics stop
saturating and the retrievers separate.

Output: backend/scaling_results.json, plus a printed table.

Usage:
    python backend/scripts/run_scaling.py
    BENCH_DECOYS="0,25,50,100" python backend/scripts/run_scaling.py
"""
import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
os.chdir(BACKEND_DIR)
sys.path.insert(0, str(BACKEND_DIR))

from app.database.init_db import init_database        # noqa: E402
from app.database.session import SessionLocal         # noqa: E402
from app.research.bench import benchmark_runner       # noqa: E402

MODES = ("vanilla", "hybrid", "graph", "adaptive", "adaptive_graph")


def main() -> None:
    dense = os.environ.get("BENCH_DENSE_BACKEND", "tfidf")
    pool = [int(x) for x in os.environ.get("BENCH_DECOYS", "0,25,50,100").split(",") if x.strip()]

    print("=" * 88)
    print(f" Distractor scaling - questions fixed, distractor pool varied (dense={dense})")
    print("=" * 88)

    init_database()
    db = SessionLocal()
    rows = []
    try:
        for decoys in pool:
            ingest = benchmark_runner.load_corpus(db, reset=True, decoys=decoys)
            key_to_id = ingest["key_to_id"]
            for mode in MODES:
                outcome = benchmark_runner.evaluate(
                    db, mode=mode, k=5, key_to_id=key_to_id, dense_backend=dense)
                rows.append({
                    "decoys": decoys,
                    "memories": ingest["memories"],
                    "mode": mode,
                    "hit_at_5": outcome["hit_at_k"],
                    "mrr": outcome["mrr"],
                    "evidence_recall": outcome.get("evidence_recall", 0.0),
                    "stale_at_1": outcome["stale_top1_rate"],
                    "duplicate_rate": outcome["duplicate_rate"],
                    "leak_rate": outcome["forgotten_leak_rate"],
                    "graph_nodes": ingest.get("graph", {}).get("nodes", 0),
                    "graph_edges": ingest.get("graph", {}).get("edges", 0),
                })
            print(f"  corpus of {ingest['memories']:>3} memories done "
                  f"(graph {ingest.get('graph', {}).get('nodes', 0)} nodes / "
                  f"{ingest.get('graph', {}).get('edges', 0)} edges)")
    finally:
        db.close()

    # print one block per corpus size
    for decoys in pool:
        block = [r for r in rows if r["decoys"] == decoys]
        if not block:
            continue
        print(f"\nCorpus {block[0]['memories']} memories ({decoys} decoys), k=5")
        print(f"{'mode':<16} {'Hit@5':>7} {'MRR':>7} {'EvidRec':>8} {'stale@1':>8} {'dup':>6} {'leak':>6}")
        for r in block:
            print(f"{r['mode']:<16} {r['hit_at_5']:>7.3f} {r['mrr']:>7.3f} "
                  f"{r['evidence_recall']:>8.3f} {r['stale_at_1']:>8.3f} "
                  f"{r['duplicate_rate']:>6.3f} {r['leak_rate']:>6.3f}")

    out = {"dense_backend": dense, "k": 5, "pool": pool, "rows": rows}
    out_path = BACKEND_DIR / "scaling_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nArtifact saved to: {out_path}")


if __name__ == "__main__":
    main()
