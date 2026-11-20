"""Research observatory arithmetic, isolation, and API contracts."""
import json
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.init_db import Base
from app.database.session import get_db
from app.auth.dependencies import get_current_user
from app.models.memory import Memory
from app.models.research import ForgottenMemory, MemoryConflict, ResearchRun, TemporalFact
from app.research.observatory import fraction, metric_ledger, live_snapshot, PAPER_TARGETS
from app.routes.observatory import router


@pytest.fixture
def db():
    engine = create_engine('sqlite://', poolclass=StaticPool, connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        yield session
    engine.dispose()


def memory(db, text='Observatory test', **kwargs):
    m = Memory(session_id=1, title=text, content=text, content_hash=str(datetime.now().timestamp()),
               created_at=datetime.utcnow()-timedelta(days=45), **kwargs)
    db.add(m); db.commit()
    return m


def test_fraction_zero_is_undefined():
    assert fraction(0, 0)['value'] is None
    assert fraction(0, 5)['value'] == 0


def test_metric_denominators_and_rr():
    rows = [
        dict(answerable=True, rank=2, hit=True, top1_is_stale=True,
             retrieved=['old', 'new'], forgotten_leak=1, stale_results=1,
             evidence_recall=1, context_chars=100, duplicate_pairs=1),
        dict(answerable=False, rank=0, hit=False, top1_is_stale=False,
             retrieved=[], forgotten_leak=0, stale_results=0,
             evidence_recall=None, context_chars=0, duplicate_pairs=0),
    ]
    l = metric_ledger({'per_question': rows})
    assert l['mrr']['value'] == .5 and l['mrr']['denominator'] == 1
    assert l['stale_top1_rate']['value'] == .5 and l['stale_top1_rate']['denominator'] == 2
    assert l['forgotten_leak_rate']['value'] == .5
    assert l['duplicate_rate']['value'] == .5
    assert l['avg_context_chars']['value'] == 50


def test_old_artifact_does_not_invent_pairs():
    l = metric_ledger({'duplicate_rate': .123, 'per_question': []})
    assert l['duplicate_rate']['value'] is None
    assert 'No raw' in l['duplicate_rate']['note']


def test_mismatch_detected():
    row = dict(answerable=True, rank=1, hit=True, top1_is_stale=False, retrieved=['a'])
    assert metric_ledger({'per_question': [row], 'mrr': .5})['mrr']['matches_reported'] is False


def test_empty_live_no_accuracy(db):
    s = live_snapshot(db)
    assert s['accuracy_metrics'] is None
    assert s['mean_importance']['value'] is None
    assert not s['scores']


def test_score_expansion_readonly(db):
    m = memory(db)
    before = db.query(ResearchRun).count()
    s = live_snapshot(db)
    r = s['scores'][0]
    assert r['memory_id'] == m.id
    assert len(r['terms']) == 8
    assert r['total'] == pytest.approx(max(0, min(1.5, sum(t['contribution'] for t in r['terms']))), abs=1e-6)
    temporal = next(t for t in r['terms'] if t['name'] == 'temporal')
    assert temporal['input'] == pytest.approx(.5, abs=.0001)
    assert db.query(ResearchRun).count() == before
    assert r['persisted_total'] is None  # GET does not write a score row.


def test_forgotten_excluded_live_scores(db):
    m = memory(db)
    db.add(ForgottenMemory(memory_id=m.id)); db.commit()
    s = live_snapshot(db)
    assert s['counts']['forgotten'] == 1 and s['counts']['active_memories'] == 0
    assert not s['scores']


def test_revision_detects_edit_without_count_change(db):
    m = memory(db)
    first = live_snapshot(db)
    m.content = 'Changed original evidence'; db.commit()
    second = live_snapshot(db)
    assert first['counts'] == second['counts']
    assert first['revision'] != second['revision']


def test_conflict_arithmetic(db):
    m = memory(db)
    db.add(MemoryConflict(older_memory_id=m.id, severity=.8, resolved=False)); db.commit()
    s = live_snapshot(db)
    assert s['conflicts'][0]['damping_factor'] == pytest.approx(.44)
    c = next(t for t in s['scores'][0]['terms'] if t['name'] == 'contradiction')
    assert c['input'] == .5 and c['weight'] == -.25


def test_temporal_interval_visible(db):
    m = memory(db)
    db.add(TemporalFact(subject='user', predicate='focus', object='Java', source_memory_id=m.id))
    db.commit()
    f = live_snapshot(db)['temporal'][0]
    assert f['source_active'] and f['valid_to'] is None


def test_pagination_keeps_full_corpus_context(db):
    memory(db, 'Alpha memory'); memory(db, 'Beta memory')
    all_rows = live_snapshot(db)['scores']
    page = live_snapshot(db, offset=1, limit=1)
    assert page['score_count'] == 2 and len(page['scores']) == 1
    assert page['scores'][0]['total'] == pytest.approx(all_rows[1]['total'], abs=1e-5)


@pytest.fixture
def client(db):
    app = FastAPI(); app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: object()
    with TestClient(app) as c:
        yield c


def test_routes(client):
    assert client.get('/api/observatory/live').status_code == 200
    assert client.get('/api/observatory/live?limit=201').status_code == 422
    assert client.get('/api/observatory/live?offset=-1').status_code == 422
    assert client.get('/api/observatory/reference').json()['targets'] == PAPER_TARGETS
    assert client.get('/api/observatory/artifacts/unknown').status_code == 404
    assert client.get('/api/observatory/runs/99999').status_code == 404


def test_artifact_is_labelled(client):
    r = client.get('/api/observatory/artifacts/core')
    assert r.status_code == 200
    assert r.json()['source'] == 'committed_artifact_not_executed_now'
    assert r.json()['data']['calculations']['adaptive']['mrr']['value'] == 1


def test_requires_authentication():
    app = FastAPI(); app.include_router(router)
    with TestClient(app) as c:
        assert c.get('/api/observatory/reference').status_code == 401


def test_saved_run_only_exposes_observatory(client, db):
    row = ResearchRun(kind='benchmark', metrics_json='{}'); db.add(row); db.commit()
    assert client.get(f'/api/observatory/runs/{row.id}').status_code == 404


def test_isolated_run_preserves_live_data(client, db):
    m = memory(db, 'Personal database sentinel')
    db.add(TemporalFact(subject='user', predicate='sentinel', object='must survive', source_memory_id=m.id))
    db.commit()
    before = live_snapshot(db)
    response = client.post('/api/observatory/runs')
    assert response.status_code == 200, response.text
    data = response.json()['data']
    assert len(data['results']) == 5
    assert data['provenance']['isolation'].startswith('fresh temporary')
    assert 'nli_loaded' in data['provenance']
    assert data['results']['adaptive']['per_question'][0]['ranking']
    assert 'pipeline_trace' in data['results']['adaptive']['per_question'][0]
    for ledgers in data['calculations'].values():
        for c in ledgers.values():
            assert c['matches_reported'] in (True, None)
    after = live_snapshot(db)
    assert after['counts'] == before['counts']
    assert after['revision'] == before['revision']
    assert client.get('/api/observatory/runs').json()[0]['id'] == response.json()['id']
    assert client.get(f"/api/observatory/runs/{response.json()['id']}").status_code == 200

@pytest.mark.parametrize('mode', ['vanilla', 'hybrid', 'graph', 'adaptive', 'adaptive_graph'])
def test_live_probe_excludes_tombstones_in_all_modes(client, db, mode):
    from app.models.memory import SearchIndex
    a = memory(db, 'Probe common research active')
    b = memory(db, 'Probe common research forgotten')
    db.add(ForgottenMemory(memory_id=b.id))
    db.add_all([SearchIndex(memory_id=a.id, session_id=1, searchable_text=a.content),
                SearchIndex(memory_id=b.id, session_id=1, searchable_text=b.content)])
    db.commit()
    r = client.post('/api/observatory/probe', json={'query': 'common research', 'mode': mode})
    assert r.status_code == 200, r.text
    assert r.json()['accuracy_metrics'] is None
    assert r.json()['results']
    assert all(m['memory_id'] != b.id for m in r.json()['results'])
    assert r.json()['results'][0]['score'] > 0


def test_probe_validation(client):
    assert client.post('/api/observatory/probe', json={'query': '   '}).status_code == 422
    assert client.post('/api/observatory/probe', json={'query': 'x', 'mode': 'invalid'}).status_code == 422
