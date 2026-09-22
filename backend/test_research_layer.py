"""
Research layer regression test - all seven paper contributions.
===========================================================================
Every check here corresponds to a specific claim in the paper. If a claim cannot
be tested, it should not be in the paper.

  1. Adaptive Memory Scoring      components compute, disc_riminative, persisted
  2. Temporal KG                  extraction, supersession, retraction, current-focus
  3. Contradiction detection      value_change + negation, resolution policy
  4. Consolidation                clusters near-duplicates, preserves provenance
  5. Knowledge gaps               exposure-without-depth surfaces, depth suppresses
  6. Forgetting                   leak rate zero across every retrieval surface
  7. Benchmark                    four modes comparable, adaptive best on stale@1

Usage (backend folder, venv active):
    python test_research_layer.py
"""
import os
import sys
import warnings

# These must be set before any model library is imported. The research layer
# loads a sentence-transformer when one is installed, and its progress bars plus
# the "unauthenticated requests to the HF Hub" notice are not test output - they
# bury the PASS/FAIL lines this gate exists to print.
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
# datetime.utcnow() deprecation notices from the standard library are noise here;
# the app's own migration to timezone-aware datetimes is tracked separately.
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", module=r"(starlette|fastapi)\.testclient")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app.research  # noqa: F401  - registers every ORM mapper

PASS, FAIL = "[PASS]", "[FAIL]"
failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  --> {PASS} {label}")
    else:
        failures.append(label)
        print(f"  --> {FAIL}  {label}   {detail}")


def main():
    print("=" * 74)
    print("  JARVIS OS - RESEARCH LAYER TEST (7 contributions)")
    print("=" * 74)

    from app.database.session import SessionLocal
    from app.research.bench import benchmark_runner

    db = SessionLocal()
    try:
        # load the controlled corpus for every subsequent check
        print("\n[0] Load PersonalBrain-Bench corpus")
        ingest = benchmark_runner.load_corpus(db, reset=True)
        key_to_id = ingest["key_to_id"]
        check("corpus ingested", ingest["memories"] >= 15, str(ingest["memories"]))
        check("conflicts detected during ingest", ingest["conflicts"] >= 1, str(ingest["conflicts"]))
        check("a memory was actually forgotten for the forgetting test",
              ingest.get("forgotten") == 1, str(ingest.get("forgotten")))

        # ================================================== 1. ADAPTIVE SCORING
        print("\n[1] Contribution 1 - Adaptive Memory Scoring")
        from app.models.memory import Memory
        from app.models.research import MemoryScore
        from app.research.scoring import DEFAULT_WEIGHTS, adaptive_memory_scorer

        score_result = adaptive_memory_scorer.score_corpus(db)
        check("every memory scored", score_result["scored"] >= 15, str(score_result["scored"]))
        check("weights are versioned", score_result["weights_version"] == "v1")
        check("positive weights sum to ~1.0",
              abs(sum(v for k, v in DEFAULT_WEIGHTS.items()
                      if k not in ("redundancy", "contradiction")) - 1.0) < 1e-6,
              str(sum(v for k, v in DEFAULT_WEIGHTS.items()
                      if k not in ("redundancy", "contradiction"))))

        rows = db.query(MemoryScore).all()
        check("score rows persisted", len(rows) >= 15, str(len(rows)))
        check("all components stored (auditable, not a black box)",
              all(all(hasattr(r, c) for c in
                      ("relevance", "frequency", "temporal", "connectivity",
                       "user_confirmation", "future_utility", "redundancy", "contradiction"))
                  for r in rows))

        totals = [r.total for r in rows]
        check("scores are discriminative (not all identical)",
              max(totals) - min(totals) > 0.05, f"range {min(totals):.3f}..{max(totals):.3f}")

        # recency term must actually decay.
        # Joined rather than looked up per row: a score row whose memory is gone
        # must not crash the test, and the join simply excludes it.
        pairs = (
            db.query(MemoryScore, Memory)
            .join(Memory, Memory.id == MemoryScore.memory_id)
            .all()
        )
        newest = max(pairs, key=lambda p: p[1].created_at or __import__("datetime").datetime.min)[0]
        oldest = min(pairs, key=lambda p: p[1].created_at or __import__("datetime").datetime.max)[0]
        check("recency term decays with age", newest.temporal > oldest.temporal,
              f"newest={newest.temporal:.3f} oldest={oldest.temporal:.3f}")
        check("no orphaned score rows remain",
              len(pairs) == len(rows), f"scores={len(rows)} joined={len(pairs)}")

        # ================================================ 2. TEMPORAL GRAPH
        print("\n[2] Contribution 2 - Temporal Personal Knowledge Graph")
        from app.models.research import TemporalFact
        from app.research.temporal import temporal_knowledge_graph as tkg

        facts = tkg.extract_facts("I am learning Python for data analysis.")
        check("fact extracted from natural text", len(facts) == 1, str(facts))
        check("pattern matched the study state", facts and facts[0]["predicate"] == "learning")

        negated = tkg.extract_facts("I am not learning Ruby anymore.")
        check("negation recognised (retraction, not assertion)",
              negated and negated[0]["negated"] is True, str(negated))

        # the key temporal behaviour: learning -> focus must supersede
        current_focus = tkg.current_focus(db)
        check("exactly one current focus survives supersession",
              len(current_focus) == 1, f"focus objects: {current_focus}")
        check("the current focus is Java (not the older Python)",
              current_focus and "java" in current_focus[0].lower(), str(current_focus))

        superseded = db.query(TemporalFact).filter(TemporalFact.superseded_by.isnot(None)).all()
        check("the superseded fact is CLOSED, not deleted (history preserved)",
              len(superseded) >= 1, str(len(superseded)))
        check("superseded fact keeps a link to its replacement",
              all(f.superseded_by for f in superseded))

        history = tkg.history(db)
        check("history returns both facts in time order",
              len(history) >= 2 and history == sorted(history, key=lambda h: h["valid_from"] or ""),
              f"{len(history)} facts")

        # ================================================ 3. CONTRADICTIONS
        print("\n[3] Contribution 3 - Contradiction-Aware Retrieval")
        from app.models.research import MemoryConflict
        from app.research.contradictions import contradiction_resolver

        detect = contradiction_resolver.resolve(db)
        check("detection runs over the corpus", detect["memories_examined"] >= 15, str(detect))
        check("conflicts found", detect["conflicts"] >= 1, str(detect["conflicts"]))

        conflicts = db.query(MemoryConflict).all()
        types = {c.conflict_type for c in conflicts}
        check("conflict types classified", len(types) >= 1, str(types))
        check("every conflict carries a resolution policy",
              all(c.resolution for c in conflicts))

        deadline_new_id = key_to_id.get("deadline_new")
        deadline_old_id = key_to_id.get("deadline_old")
        if deadline_old_id:
            penalty, reason = contradiction_resolver.conflict_penalty(db, deadline_old_id)
            check("the OUTDATED memory is penalised for retrieval",
                  penalty < 1.0, f"multiplier={penalty}")
            check("the penalty gives a reason", bool(reason) or penalty == 1.0, reason)
        if deadline_new_id:
            newer_penalty, _ = contradiction_resolver.conflict_penalty(db, deadline_new_id)
            check("the CURRENT memory is NOT penalised", newer_penalty == 1.0, f"{newer_penalty}")

        summary = contradiction_resolver.summary(db)
        check("summary reports totals and types",
              summary["total"] >= 1 and "by_type" in summary)

        # ================================================ 4. CONSOLIDATION
        print("\n[4] Contribution 4 - Memory Consolidation")
        from app.models.research import MemoryConsolidation
        from app.research.consolidation import memory_consolidator

        sim = memory_consolidator.similarity(
            "FastAPI routing uses decorators to map HTTP methods and paths to Python functions",
            "FastAPI routing maps HTTP methods and paths to Python functions using decorators")
        check("reworded duplicate scores above the configured threshold",
              sim >= memory_consolidator.threshold,
              f"{sim:.4f} vs threshold {memory_consolidator.threshold}")

        unrelated = memory_consolidator.similarity(
            "FastAPI routing uses decorators", "The IEEE paper deadline is 25 September")
        check("unrelated text scores low similarity", unrelated < 0.30, f"{unrelated:.4f}")

        dry = memory_consolidator.consolidate(db, dry_run=True)
        check("dry run finds the duplicate cluster without merging",
              dry["clusters_found"] >= 1, str(dry["clusters_found"]))
        check("dry run reports a context saving",
              dry["context_reduction_pct"] >= 0, f"{dry['context_reduction_pct']}%")

        real = memory_consolidator.consolidate(db)
        check("consolidation persists", real["clusters_found"] >= 1)
        rows_c = db.query(MemoryConsolidation).all()
        check("consolidation rows written", len(rows_c) >= 1, str(len(rows_c)))
        check("PROVENANCE PRESERVED - merged ids are recorded",
              all(r.merged_memory_ids for r in rows_c),
              "the paper claims provenance is preserved")
        check("merged count matches the id list",
              all(r.merged_count == len([x for x in r.merged_memory_ids.split(',') if x]) for r in rows_c))

        # ================================================ 5. KNOWLEDGE GAPS
        print("\n[5] Contribution 5 - Knowledge-Gap Detection")
        from app.research.gaps import knowledge_gap_detector

        # Scoped to the benchmark corpus, and not persisted.
        #
        # Gap scores are corpus-relative (mentions, spread, connectivity are all
        # statistics over the memories being examined), so a 15-memory corpus has
        # to be measured against itself. Unscoped, this ran over every memory the
        # machine holds and the concept the check looks for was crowded out of the
        # ranking by unrelated notes - a failure that said nothing about the code.
        # persist=False so a scoped run cannot overwrite the gaps of the real vault.
        corpus_ids = set(key_to_id.values())
        gap_result = knowledge_gap_detector.detect(db, scope_ids=corpus_ids, persist=False)
        check("gap detection runs", gap_result["memories_examined"] >= 15, str(gap_result["memories_examined"]))
        check("at least one gap surfaced", gap_result["gaps"] >= 1, str(gap_result["gaps"]))

        concepts = [g["concept"] for g in gap_result["items"]]
        check("the repeatedly-mentioned-but-unexplained concept is flagged",
              any("multithreading" in c for c in concepts), str(concepts[:5]))

        if gap_result["items"]:
            top = gap_result["items"][0]
            check("each gap carries a human-readable rationale", bool(top["rationale"]), str(top))
            check("gap score is bounded 0..1", 0.0 <= top["gap_score"] <= 1.0, str(top["gap_score"]))

        # depth must SUPPRESS a gap
        good_stats = knowledge_gap_detector._concept_stats([
            type("M", (), {"title": "RAG retrieval", "content":
                 "RAG is a technique that retrieves context. RAG means retrieval augmented generation. "
                 "RAG works by embedding the query. RAG refers to grounding the model. " * 3,
                 "created_at": __import__("datetime").datetime.utcnow()})()
        ])
        entry = good_stats.get("rag", {})
        check("explained concepts accumulate explanation evidence",
              entry.get("explained", 0) >= 1, str(entry.get("explained")))

        # ================================================ 6. FORGETTING
        print("\n[6] Contribution 6 - Forgetting / Unlearning")
        from app.models.research import ForgottenMemory
        from app.research.forgetting import forgetting_service

        forgotten_ids = forgetting_service.forgotten_ids(db)
        check("the forgotten memory is tombstoned", len(forgotten_ids) == 1, str(forgotten_ids))

        secret_id = key_to_id.get("old_password")
        if secret_id:
            check("its search index row is gone",
                  db.execute(__import__("sqlalchemy").text(
                      "SELECT COUNT(*) FROM search_index WHERE memory_id = :m"),
                      {"m": secret_id}).scalar() == 0)

            # the decisive test: retrieval must not return it in ANY mode
            from app.research.pipeline import adaptive_retrieval

            leaks = {}
            for mode in ("vanilla", "hybrid", "graph", "adaptive"):
                res = adaptive_retrieval.retrieve(db, "temporary lab portal credential", limit=10, mode=mode)
                leaks[mode] = sum(1 for r in res if r["memory_id"] == secret_id)

            check("adaptive does NOT return the forgotten memory",
                  leaks["adaptive"] == 0, str(leaks))

            # WHY THIS IS NOT "the baselines leak it": whether a baseline still
            # reaches the text depends on which dense backend is installed. With a
            # vector store the embedding itself is deleted, so no mode can return
            # it; with the model-free TF-IDF backend the raw memory row is still
            # there and the baselines DO return it. Asserting that
            # backend-dependent outcome failed on a machine that had
            # sentence-transformers installed while the forgetting was working
            # perfectly. What the paper claims is the MECHANISM, so the mechanism
            # is what gets asserted:
            #   (a) the row is tombstoned, not destroyed,
            #   (b) an unfiltered retriever still reaches that row,
            #   (c) the research layer drops it when it is handed over.
            from app.models.memory import Memory

            secret_row = db.query(Memory).filter(Memory.id == secret_id).first()
            check("the unlearned row is tombstoned, not destroyed (audit trail kept)",
                  secret_row is not None and secret_id in forgetting_service.forgotten_ids(db))

            raw_ids = [mid for mid, _score in adaptive_retrieval._candidate_tfidf(
                db, "temporary lab portal credential", 10 ** 6)]
            check("an unfiltered raw-row retriever still reaches it - that is the hole",
                  secret_id in raw_ids, f"reachable={secret_id in raw_ids}")

            if secret_row is not None:
                layer_trace = {"stages": {}}
                kept = adaptive_retrieval._apply_research_layer(db, [secret_row], layer_trace)
                check("the research layer drops it even when handed over as a candidate",
                      all(m.id != secret_id for m in kept), str(layer_trace["stages"]))

        # restore works
        if secret_id:
            restored = forgetting_service.restore(db, secret_id)
            check("restore re-indexes the memory", restored.get("restored") is True, str(restored))
            after = adaptive_retrieval.retrieve(db, "temporary lab portal credential", limit=10, mode="hybrid")
            check("restored memory is retrievable again",
                  any(r["memory_id"] == secret_id for r in after),
                  "restore must be more than deleting a tombstone row")
            # put it back for the benchmark
            forgetting_service.forget(db, secret_id, reason="benchmark")

        bulk = forgetting_service.forget_matching(db, "zzz_no_such_content_zzz")
        check("bulk forget reports zero matches cleanly", bulk["forgotten"] == 0, str(bulk))

        # ================================================ 7. BENCHMARK
        print("\n[7] Contribution 7 - PersonalBrain-Bench across four modes")
        result = benchmark_runner.run_all(db, k=5)
        modes = result["results"]
        check("all four modes evaluated", set(modes) == {"vanilla", "hybrid", "graph", "adaptive"},
              str(sorted(modes)))
        check("corpus size matches", result["corpus"]["memories"] >= 15, str(result["corpus"]))
        check("results persisted as research runs", len(db.execute(
            __import__("sqlalchemy").text("SELECT COUNT(*) FROM research_runs")).fetchall()) > 0)

        a, h, v = modes["adaptive"], modes["hybrid"], modes["vanilla"]
        check("adaptive MRR >= every baseline", a["mrr"] >= max(h["mrr"], v["mrr"]),
              f"adaptive={a['mrr']} hybrid={h['mrr']} vanilla={v['mrr']}")
        check("adaptive has the LOWEST stale@1 rate",
              a["stale_top1_rate"] <= min(h["stale_top1_rate"], v["stale_top1_rate"]),
              f"adaptive={a['stale_top1_rate']} hybrid={h['stale_top1_rate']} vanilla={v['stale_top1_rate']}")
        check("adaptive eliminates forgotten-content leakage",
              a["forgotten_leak_rate"] == 0.0, f"{a['forgotten_leak_rate']}")
        check("adaptive eliminates duplicate context",
              a["duplicate_rate"] == 0.0, f"{a['duplicate_rate']}")
        check("the temporal advantage shows up per-type",
              a["per_type"]["temporal"]["mrr"] >= h["per_type"]["temporal"]["mrr"],
              f"adaptive={a['per_type']['temporal']['mrr']} hybrid={h['per_type']['temporal']['mrr']}")
        check("the contradiction advantage shows up per-type",
              a["per_type"]["contradiction"]["mrr"] >= v["per_type"]["contradiction"]["mrr"],
              f"adaptive={a['per_type']['contradiction']['mrr']} vanilla={v['per_type']['contradiction']['mrr']}")
        check("comparison table produced", "adaptive_vs_hybrid" in result["comparison"],
              str(list(result["comparison"].keys())))

        # The dense backend (neural embedder vs model-free TF-IDF) is selected at
        # runtime and the two do not give identical figures. A table without this
        # line cannot be reproduced on another machine, so the run states it.
        configuration = result.get("configuration", {})
        check("the run records the configuration it was measured with",
              bool(configuration.get("dense_backend")), str(configuration))
        print(f"      (dense backend: {configuration.get('dense_backend')}, "
              f"scoring weights {configuration.get('scoring_weights_version')}, "
              f"k={result.get('k')}, corpus-scoped={configuration.get('corpus_scope')})")

        # ================================================ API SURFACE
        print("\n[8] API surface")
        from fastapi.testclient import TestClient

        from app.main import app

        api = TestClient(app)
        token = api.post("/api/auth/login", json={
            "username": "Immanuel", "password": "secondbrain", "device_name": "test"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        for path, method in [
            ("/api/research/overview", "get"),
            ("/api/research/scores", "get"),
            ("/api/research/temporal", "get"),
            ("/api/research/conflicts", "get"),
            ("/api/research/gaps", "get"),
            ("/api/research/forgotten", "get"),
            ("/api/research/runs", "get"),
        ]:
            r = getattr(api, method)(path, headers=headers)
            check(f"GET {path} -> 200", r.status_code == 200, r.text[:120])

        r = api.post("/api/research/score", headers=headers)
        check("POST /score -> 200", r.status_code == 200, r.text[:120])

        r = api.post("/api/research/temporal/ingest", headers=headers,
                     json={"text": "I am mainly focusing on Java for backend development."})
        check("temporal ingest -> 200", r.status_code == 200, r.text[:150])

        r = api.post("/api/research/answer", headers=headers,
                     json={"question": "What am I currently focusing on?", "mode": "adaptive"})
        check("answer endpoint -> 200", r.status_code == 200, r.text[:150])
        check("answer returns a pipeline trace", "trace" in r.json(), r.text[:150])

        r = api.post("/api/research/forget", headers=headers, json={"query": ""})
        check("forget with no target -> 400", r.status_code == 400, f"got {r.status_code}")

        r = api.post("/api/research/forget", headers=headers, json={"memory_id": 999999})
        check("forget unknown memory -> 404", r.status_code == 404, f"got {r.status_code}")

        r = api.get("/api/research/overview")
        check("research routes require the app JWT", r.status_code == 401, f"got {r.status_code}")

        r = api.post("/api/research/benchmark", headers=headers, json={"k": 5})
        check("benchmark endpoint -> 200", r.status_code == 200, r.text[:150])
        body = r.json()
        check("benchmark returns a paper-ready summary", "summary" in body and "adaptive" in body["summary"])

    finally:
        db.close()

    print("\n" + "=" * 74)
    if failures:
        print(f"  {len(failures)} CHECK(S) FAILED:")
        for f in failures:
            print(f"    - {f}")
        print("=" * 74)
        return 1
    print("  ALL RESEARCH LAYER CHECKS PASSED")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
