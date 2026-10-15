#!/usr/bin/env python3
"""
E3 - Conflict-detection accuracy on an author-annotated pair set.

The detector's precision and recall were previously unknown; only its
downstream effect on retrieval had been measured. This harness inserts
annotated memory PAIRS into a throwaway database, runs the shipped
detector (rule signals + ONNX NLI when installed) and scores it:

  gold classes : temporal / value_change (supersession), negation,
                 numeric value change
  negatives    : near-duplicates, topically similar but consistent,
                 same-topic different-subject, unrelated text

Artifact: backend/conflict_accuracy_results.json
"""
import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
WORKDIR = Path("/tmp/e3_conflict_run")
import shutil
shutil.rmtree(WORKDIR, ignore_errors=True)
WORKDIR.mkdir(parents=True, exist_ok=True)
os.chdir(WORKDIR)
sys.path.insert(0, str(BACKEND_DIR))

from app.database.init_db import init_database  # noqa: E402
from app.database.session import SessionLocal   # noqa: E402
from app.models.capture import MemorySession    # noqa: E402
from app.models.memory import Memory            # noqa: E402
from app.models.user import User                # noqa: E402

# (text_a, text_b, gold_class or None)
PAIRS = [
    # ---- positives: temporal / value-change supersession ------------------
    ("I am working on the Second Brain journal paper this semester.",
     "I have switched to the IEEE conference paper as my main focus now.",
     "value_change"),
    ("My thesis deadline is 25 September 2026.",
     "The thesis deadline moved to 10 October 2026 after the extension.",
     "value_change"),
    ("I use Visual Studio Code for all my Python development.",
     "I moved my Python work to PyCharm this month.",
     "value_change"),
    ("The project repository is hosted on GitLab.",
     "The repository now lives on GitHub after the migration.",
     "value_change"),
    # ---- positives: negation ---------------------------------------------
    ("I attend the robotics club meetings every Friday.",
     "I do not attend the robotics club meetings any more.",
     "negation"),
    ("My laptop has 16 GB of RAM.",
     "My laptop does not have 16 GB of RAM, that was the old machine.",
     "negation"),
    ("I am enrolled in the cloud computing elective.",
     "I am not enrolled in the cloud computing elective anymore.",
     "negation"),
    # ---- positives: numeric value change ----------------------------------
    ("The model training run costs about 40 GPU-hours per epoch.",
     "After optimisation each epoch costs 12 GPU-hours.",
     "value_change"),
    ("My dataset contains 8,000 labelled screenshots.",
     "The cleaned dataset has 5,400 labelled screenshots.",
     "value_change"),
    ("The bench corpus holds 12 synthetic memories.",
     "The bench corpus was extended to 15 synthetic memories.",
     "value_change"),
    # ---- negatives: near-duplicates (consolidation's job, not conflict) ---
    ("Retrieved the same article about temporal knowledge graphs today.",
     "Saved the article on temporal knowledge graphs again from another tab.",
     None),
    ("Meeting notes: discussed the memory scoring weights with the team.",
     "Notes from the same meeting about memory scoring weights discussion.",
     None),
    # ---- negatives: same topic, consistent --------------------------------
    ("I write my experiments in Python with PyTorch.",
     "My Python experiment scripts log every seed and hyperparameter.",
     None),
    ("The IEEE paper uses a two-column format.",
     "The IEEE paper abstract must be submitted by 25 September 2026.",
     None),
    ("I capture screenshots every five seconds during study sessions.",
     "The screenshot capture interval can be raised for privacy.",
     None),
    # ---- negatives: same words, different subject -------------------------
    ("My advisor reviewed the conference paper draft.",
     "My friend reviewed the conference paper of her roommate.",
     None),
    ("The deadline for the journal track is in November.",
     "My roommate's journal deadline is also in November.",
     None),
    # ---- negatives: unrelated ---------------------------------------------
    ("The canteen serves filter coffee after 3 pm.",
     "Gradient descent minimises the loss surface.",
     None),
    ("Chennai weather is humid in October.",
     "SQL indexes speed up equality lookups.",
     None),
    # ---- negatives: negation words but consistent --------------------------
    ("I never capture screenshots outside study sessions.",
     "Screenshot capture runs only inside study sessions.",
     None),
    ("The API does not allow writes with a read-only token.",
     "Read-only tokens cannot modify anything through the API.",
     None),
]


def main() -> None:
    init_database()
    db = SessionLocal()
    try:
        owner = db.query(User).order_by(User.id.asc()).first()
        from app.research.contradictions import contradiction_resolver
        from app.research.temporal import temporal_knowledge_graph

        gold = []          # (id_a, id_b, gold_class)
        scope = []
        for i, (ta, tb, cls) in enumerate(PAIRS):
            session = MemorySession(user_id=owner.id, session_type=f"e3_{i}",
                                    is_active=False)
            db.add(session)
            db.commit()
            db.refresh(session)
            ids = []
            for text in (ta, tb):
                import hashlib
                mem = Memory(
                    session_id=session.id,
                    title=text[:60],
                    content=text,
                    content_hash=hashlib.sha256(text.encode()).hexdigest(),
                    source_type="e3",
                    app_source=f"e3:{i}",
                )
                db.add(mem)
                db.commit()
                db.refresh(mem)
                facts = temporal_knowledge_graph.extract_facts(text)
                if facts:
                    temporal_knowledge_graph.record_facts(
                        db, facts, source_memory_id=mem.id)
                ids.append(mem.id)
                scope.append(mem.id)
            gold.append((ids[0], ids[1], cls))
        db.commit()

        contradiction_resolver.resolve(db, scope_ids=scope)

        predicted = {}
        from app.models.research import MemoryConflict
        for row in db.query(MemoryConflict).all():
            key = frozenset((row.older_memory_id, row.newer_memory_id))
            predicted.setdefault(key, []).append(row.conflict_type)

        tp = fp = fn = 0
        per_class = {}
        detail = []
        for id_a, id_b, cls in gold:
            key = frozenset((id_a, id_b))
            got = predicted.get(key)
            if cls is not None:
                per_class.setdefault(cls, {"gold": 0, "detected": 0})
                per_class[cls]["gold"] += 1
            if got and cls is not None:
                tp += 1
                per_class[cls]["detected"] += 1
            elif got and cls is None:
                fp += 1
            elif not got and cls is not None:
                fn += 1
            detail.append({"gold": cls, "predicted": got})

        precision = tp / max(1, tp + fp)
        recall = tp / max(1, tp + fn)
        f1 = 2 * precision * recall / max(1e-9, precision + recall)
        out = {
            "pairs": len(PAIRS),
            "positives": sum(1 for *_ , c in [(g[0], g[1], g[2]) for g in gold] if c),
            "negatives": sum(1 for g in gold if g[2] is None),
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "per_class": per_class,
            "detail": detail,
        }
        (BACKEND_DIR / "conflict_accuracy_results.json").write_text(
            json.dumps(out, indent=2))
        print(json.dumps({k: v for k, v in out.items() if k != "detail"}, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
