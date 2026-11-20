"""Transparent read-only live calculations and independently recomputable v1 metrics.

Never run BenchmarkRunner.load_corpus against the application database: its reset
clears derived state. Observatory benchmarks execute in a separate process/database.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

PAPER_TARGETS = {
    'vanilla': {'hit_at_k': 1., 'mrr': .833, 'stale_top1_rate': .364, 'forgotten_leak_rate': .022, 'duplicate_rate': .022},
    'hybrid': {'hit_at_k': 1., 'mrr': .944, 'stale_top1_rate': .182, 'forgotten_leak_rate': .022, 'duplicate_rate': .022},
    'graph': {'hit_at_k': 1., 'mrr': .944, 'stale_top1_rate': .182, 'forgotten_leak_rate': .022, 'duplicate_rate': .022},
    'adaptive': {'hit_at_k': 1., 'mrr': 1., 'stale_top1_rate': 0., 'forgotten_leak_rate': 0., 'duplicate_rate': 0.},
    'adaptive_graph': {'hit_at_k': 1., 'mrr': 1., 'stale_top1_rate': 0., 'forgotten_leak_rate': 0., 'duplicate_rate': 0.},
}
METRICS = {
    'hit_at_k': 'answerable queries with any gold hit / answerable queries',
    'mrr': 'sum(1 / first gold rank; 0 for a miss) / answerable queries',
    'stale_top1_rate': 'queries whose first result is forbidden / all queries',
    'forgotten_leak_rate': 'forgotten returned items / all returned items',
    'duplicate_rate': 'within-query pairs with term-frequency cosine >= 0.90 / all returned items (v1; not pair fraction)',
    'evidence_recall': 'mean(unique gold keys returned / required gold keys) over answerable queries',
    'staleness_rate': 'forbidden returned items / all returned items',
    'avg_context_chars': 'sum of returned content characters / all queries',
}
SCORE_FORMULAS = {
    'relevance': 'min(1, 6 × sum(interest frequency of each memory token) / sum(interest frequencies))',
    'frequency': 'distinct terms with 1 < document frequency < corpus size / distinct memory terms',
    'temporal': '2 ** (-max(0, age_days) / 45)',
    'connectivity': 'min(1, sum(graph term occurrences) / (4 × distinct memory terms))',
    'user_confirmation': '1 if explicitly tagged; otherwise 0.6 for a confirmation phrase; otherwise 0',
    'future_utility': 'min(1, 0.5 actionable + 0.3 project + 0.3 durable + 0.2 ISO date); heuristic, not learned',
    'redundancy': 'terms with document frequency >= max(3, corpus size × 0.5) / distinct terms',
    'contradiction': 'min(1, unresolved conflict count / 2)',
}
ARTIFACTS = {
    'core': 'benchmark_results.json', 'personas': 'benchmark_multi_user_results.json',
    'ablation': 'ablation_results.json', 'statistics': 'stats_results.json',
    'scaling': 'scaling_results.json', 'conflict_dev': 'conflict_accuracy_results.json',
    'conflict_holdout': 'conflict_accuracy_holdout.json',
}
BACKEND = Path(__file__).resolve().parents[2]


def fraction(numerator, denominator, terms=None):
    return {'numerator': numerator, 'denominator': denominator,
            'value': numerator / denominator if denominator else None,
            'terms': terms or [], 'undefined': denominator == 0}


def metric_ledger(metrics):
    """Recompute from per-question counts, not the displayed rounded aggregates."""
    questions = metrics.get('per_question', [])
    answerable = [q for q in questions if q.get('answerable')]
    rr = [1 / q['rank'] if q.get('rank', 0) > 0 else 0. for q in answerable]
    returned = sum(len(q.get('retrieved', [])) for q in questions)
    ledger = {
        'hit_at_k': fraction(sum(bool(q['hit']) for q in answerable), len(answerable)),
        'mrr': fraction(sum(rr), len(answerable), rr),
        'stale_top1_rate': fraction(sum(bool(q['top1_is_stale']) for q in questions), len(questions)),
        'forgotten_leak_rate': fraction(sum(q.get('forgotten_leak', 0) for q in questions), returned),
        'staleness_rate': fraction(sum(q.get('stale_results', 0) for q in questions), returned),
        'evidence_recall': fraction(sum(q.get('evidence_recall') or 0 for q in answerable), len(answerable)),
        'avg_context_chars': fraction(sum(q.get('context_chars', 0) for q in questions), len(questions)),
    }
    # Older committed artifacts do not record per-query duplicate counts.
    if all('duplicate_pairs' in q for q in questions) and questions:
        ledger['duplicate_rate'] = fraction(sum(q['duplicate_pairs'] for q in questions), returned)
    else:
        ledger['duplicate_rate'] = {'value': None, 'undefined': True,
            'note': 'No raw duplicate-pair counts in this older artifact. Rerun to audit this metric.'}
    for key, calculation in ledger.items():
        calculation['formula'] = METRICS[key]
        calculation['reported'] = metrics.get(key)
        value = calculation['value']
        tolerance = .051 if key == 'avg_context_chars' else .000051
        calculation['matches_reported'] = None if value is None else abs(value - (metrics.get(key) or 0)) <= tolerance
    return ledger


def audit_result(result):
    return {**result, 'calculations': {mode: metric_ledger(m) for mode, m in result.get('results', {}).items()}}


def live_snapshot(db, offset=0, limit=50):
    from app.models.memory import Memory
    from app.models.graph import GraphNode, GraphEdge
    from app.models.research import (ForgottenMemory, TemporalFact, MemoryConflict,
                                     MemoryConsolidation, KnowledgeGap, MemoryScore)
    from app.research.scoring import adaptive_memory_scorer as scorer

    now = datetime.utcnow()
    memories = db.query(Memory).order_by(Memory.id).all()
    forgotten = {r.memory_id for r in db.query(ForgottenMemory).all()}
    active = [m for m in memories if m.id not in forgotten]
    ids = {m.id for m in active}
    context = scorer.build_context(db, active, scope_ids=ids)
    context['now'] = now
    persisted = {s.memory_id: s for s in db.query(MemoryScore).all()}
    score_rows = []
    all_scores = []
    for memory in active:
        c = scorer.score_memory(memory, context)
        terms = []
        for name, weight in scorer.weights.items():
            signed = -weight if name in ('redundancy', 'contradiction') else weight
            terms.append({'name': name, 'input': c[name], 'weight': signed,
                          'contribution': signed * c[name], 'formula': SCORE_FORMULAS[name]})
        raw = sum(t['contribution'] for t in terms)
        all_scores.append(c['total'])
        saved = persisted.get(memory.id)
        score_rows.append({'memory_id': memory.id, 'title': memory.title,
                          'created_at': memory.created_at, 'updated_at': memory.updated_at,
                          'age_days': max(0., (now - (memory.created_at or now)).total_seconds() / 86400),
                          'terms': terms, 'raw_sum': raw, 'clip': 'min(1.5, max(0, S))', 'total': c['total'],
                          'persisted_total': saved.total if saved else None,
                          'persisted_at': saved.computed_at if saved else None,
                          'persisted_delta': c['total'] - saved.total if saved else None,
                          'raw_inputs': {
                              'tokens_with_repetition': scorer._terms(f'{memory.title or ""} {memory.content or ""}'),
                              'term_document_frequencies': {t: context['term_counts'][t] for t in set(scorer._terms(f'{memory.title or ""} {memory.content or ""}'))},
                              'interest_frequencies': dict(context['interests']),
                              'graph_term_counts': dict(context['degree_by_term']),
                              'unresolved_conflict_count': context['conflicts_by_memory'].get(memory.id, 0),
                              'category': memory.category,
                              'corpus_size': len(active),
                          }})
    score_rows.sort(key=lambda r: (-r['total'], r['memory_id']))
    facts = db.query(TemporalFact).order_by(TemporalFact.id).all()
    conflicts = db.query(MemoryConflict).order_by(MemoryConflict.id).all()
    groups = db.query(MemoryConsolidation).order_by(MemoryConsolidation.id).all()
    gaps = db.query(KnowledgeGap).order_by(KnowledgeGap.gap_score.desc()).all()
    nodes = db.query(GraphNode).order_by(GraphNode.id).all()
    edges = db.query(GraphEdge).order_by(GraphEdge.id).all()
    counts = {'memories_total': len(memories), 'active_memories': len(active),
              'forgotten': len(forgotten), 'scored_persisted': len(persisted),
              'temporal_facts': len(facts), 'open_facts': sum(f.valid_to is None for f in facts),
              'superseded_facts': sum(f.superseded_by is not None for f in facts),
              'conflicts': len(conflicts), 'unresolved_conflicts': sum(not c.resolved for c in conflicts),
              'consolidations': len(groups), 'gaps_persisted': len(gaps),
              'graph_nodes': len(nodes), 'graph_edges': len(edges)}
    # Hash actual source/derived records, not just counts; updates without insertions are detected.
    tracked = [memories, facts, conflicts, groups, gaps, nodes, edges, list(persisted.values()),
               db.query(ForgottenMemory).order_by(ForgottenMemory.id).all()]
    serial = [[{prop.key: getattr(row, prop.key) for prop in row.__mapper__.column_attrs}
               for row in rows] for rows in tracked]
    revision = hashlib.sha256(json.dumps(serial, default=str, sort_keys=True).encode()).hexdigest()[:16]
    graph_degree = fraction(2 * len(edges), len(nodes))
    return {'sampled_at': now.isoformat() + 'Z', 'revision': revision, 'counts': counts,
            'scope': 'Legacy single-user database; active-memory scoring excludes tombstones. Derived counts are stored rows, not claims of correctness.',
            'accuracy_metrics': None, 'accuracy_note': 'MRR / Hit@k / accuracy require gold labels. Live notes have no gold labels.',
            'score_equation': 'S = .30R + .08F + .22T + .15G + .15U + .10P - .18D - .25C',
            'weights': scorer.weights, 'half_life_days': scorer.half_life_days,
            'scores': score_rows[offset:offset + limit], 'offset': offset, 'limit': limit, 'score_count': len(score_rows),
            'mean_importance': fraction(sum(all_scores), len(all_scores)),
            'graph_mean_degree': {**graph_degree, 'formula': '2 × stored edges / stored nodes; includes all edge types'},
            'temporal': [{'id': f.id, 'subject': f.subject, 'predicate': f.predicate, 'object': f.object,
                          'valid_from': f.valid_from, 'valid_to': f.valid_to, 'superseded_by': f.superseded_by,
                          'source_memory_id': f.source_memory_id, 'source_active': f.source_memory_id in ids} for f in facts],
            'conflicts': [{'id': c.id, 'older': c.older_memory_id, 'newer': c.newer_memory_id,
                           'severity': c.severity, 'damping_factor': 1 - .7 * (c.severity or 0),
                           'substitution': f'1 - 0.7 × {c.severity or 0}', 'resolved': c.resolved,
                           'method': c.detected_by, 'type': c.conflict_type, 'resolution': c.resolution} for c in conflicts],
            'consolidations': [{'id': g.id, 'canonical_memory_id': g.canonical_memory_id,
                                'members': g.merged_memory_ids, 'merged_count': g.merged_count,
                                'threshold': g.similarity_threshold, 'tokens_before': g.tokens_before,
                                'tokens_after': g.tokens_after,
                                'reduction': fraction((g.tokens_before or 0) - (g.tokens_after or 0), g.tokens_before or 0)} for g in groups],
            'gaps': [{'concept': g.concept, 'mentions': g.mentions, 'exposure': min(1, (g.mentions or 0) / 12),
                      'depth': g.depth_score, 'connectivity': g.connectivity, 'stored_gap': g.gap_score,
                      'recomputed_from_stored_inputs': min(1, (g.mentions or 0) / 12) * (1 - (g.depth_score or 0)) * (1 - .5 * (g.connectivity or 0)),
                      'formula': 'min(1, mentions/12) × (1-depth) × (1-0.5×connectivity)',
                      'detected_at': g.detected_at, 'warning': 'Heuristic; stored rounded inputs, not validated understanding.'} for g in gaps],
            'freshness_note': 'Scores recomputed read-only now. Facts, graph, conflicts, consolidation and gaps reflect their latest completed pipeline operations; this view does not run or fabricate extraction.'}
