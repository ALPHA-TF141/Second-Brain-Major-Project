"""
Regenerate benchmark_results.json (the file every quantitative claim is read from).
===========================================================================
Run it from the repository root:

    python backend/run_benchmark.py

Why a script instead of a one-liner: the result file has to carry the run
CONFIGURATION and the ENVIRONMENT:

  configuration  which dense backend was used (a neural embedder when one is
                 installed, model-free TF-IDF otherwise - the two do not give
                 identical leak/staleness figures) and the scoring weights
                 version. Without it, the table cannot be reproduced.
  environment    the machine, so the latency column is attributable. Latency is
                 wall-clock and is not comparable between machines; the quality
                 metrics are deterministic and corpus-scoped.

The evaluation is corpus-scoped end to end (retrieval, scoring, conflict
detection, temporal supersession, gap statistics), so the numbers depend only on
the corpus and not on whatever else is in the database.
"""
import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# The database URL is relative, so the working directory decides which database
# is opened - run from anywhere and you would silently evaluate an empty one.
# Same reason the verification scripts Push-Location into backend/.
os.chdir(HERE)

import app.research  # noqa: F401,E402  - registers every ORM mapper
from app.database.session import SessionLocal  # noqa: E402
from app.research.bench import benchmark_runner  # noqa: E402

OUT = os.path.join(HERE, os.pardir, "benchmark_results.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate benchmark_results.json")
    parser.add_argument("--backend", choices=("tfidf", "neural"), default="tfidf",
                        help="dense retriever used by the evaluation. 'tfidf' (default) is "
                             "offline, needs no model download and is what the published "
                             "numbers were produced with; 'neural' uses sentence-transformers "
                             "when it is installed and gives different figures.")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = benchmark_runner.run_all(db, k=args.k, dense_backend=args.backend)
    finally:
        db.close()

    results = {
        mode: {k: v for k, v in outcome.items() if k != "per_question"}
        for mode, outcome in result["results"].items()
    }
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system": "SecondBrain - Adaptive Memory Retrieval",
        "configuration": result["configuration"],
        "environment": {
            "note": ("Retrieval, scoring and conflict detection are corpus-scoped, so the "
                     "quality metrics are reproducible on any database. Latency is wall-clock "
                     "on the machine that produced this file and is NOT comparable across "
                     "machines."),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
        },
        "corpus": result["corpus"],
        "k": result["k"],
        "results": results,
        "comparison": result["comparison"],
        "per_question_adaptive": result["results"]["adaptive"]["per_question"],
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print(f"[OK] wrote {os.path.normpath(OUT)}")
    print(f"     configuration: {payload['configuration']}")
    for mode in ("vanilla", "hybrid", "graph", "adaptive"):
        m = results[mode]
        print(f"     {mode:9s} hit@5={m['hit_at_k']:.3f} mrr={m['mrr']:.3f} "
              f"stale@1={m['stale_top1_rate']:.3f} leak={m['forgotten_leak_rate']:.3f} "
              f"duplicate={m['duplicate_rate']:.3f} ({m['latency_ms']} ms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
