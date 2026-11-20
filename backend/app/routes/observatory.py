"""Research-first observability. New benchmark runs never touch live derived state."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.models.research import ResearchRun
from app.research.observatory import (ARTIFACTS, BACKEND, METRICS, PAPER_TARGETS,
                                      audit_result, live_snapshot)

router = APIRouter(prefix='/api/observatory', tags=['research-observatory'])
_run_lock = threading.Lock()


@router.get('/live')
def live(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
         db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return live_snapshot(db, offset, limit)


@router.get('/reference')
def reference(user: User = Depends(get_current_user)):
    return {'paper': 'Ieee_paper_Final8.pdf, Table II, core synthetic corpus',
            'targets': PAPER_TARGETS, 'metric_definitions': METRICS,
            'conditions': {'memories': 15, 'queries': 11, 'answerable_queries': 9, 'k': 5,
                           'retrieval': 'TF-IDF, not neural embeddings',
                           'nli': 'ONNX DistilBERT INT8, both orders >= .55',
                           'parsing': 'spaCy en_core_web_sm 3.8.0'},
            'caveats': ['Targets are transcribed reference values, not measurements.',
                        'Synthetic authored diagnostics do not establish real-world generalisation.',
                        'Zero stale@1 does not imply zero stale results at lower ranks.',
                        'Retrieval-level exclusion is not permanent erasure.',
                        'Original baselines and adaptive have different forgetting policies.',
                        'Other paper tables can be inspected in committed artifacts; they are not rerun by the core button.'],
            'artifacts': ARTIFACTS}


@router.get('/artifacts/{name}')
def artifact(name: str, user: User = Depends(get_current_user)):
    if name not in ARTIFACTS:
        raise HTTPException(404, 'Unknown artifact')
    path = BACKEND / ARTIFACTS[name]
    if not path.is_file():
        raise HTTPException(404, 'Artifact not present')
    try:
        raw = json.loads(path.read_text())
    except (ValueError, OSError):
        raise HTTPException(422, 'Artifact could not be read')
    return {'source': 'committed_artifact_not_executed_now', 'file': path.name,
            'warning': 'Historical repository artifact; not a fresh measurement or an independently verified paper target.',
            'data': audit_result(raw) if name == 'core' else raw}


@router.get('/runs')
def runs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(ResearchRun).filter(ResearchRun.kind == 'observatory').order_by(ResearchRun.id.desc()).limit(30).all()
    return [{'id': r.id, 'created_at': r.created_at, 'duration_ms': r.duration_ms,
             'questions': r.questions} for r in rows]


@router.get('/runs/{run_id}')
def get_run(run_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(ResearchRun).filter(ResearchRun.id == run_id, ResearchRun.kind == 'observatory').first()
    if not row:
        raise HTTPException(404, 'Run not found')
    return {'id': row.id, 'created_at': row.created_at, 'data': json.loads(row.metrics_json)}


@router.post('/runs')
def run(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not _run_lock.acquire(blocking=False):
        raise HTTPException(409, 'A benchmark is already running in this server process')
    started = time.perf_counter()
    try:
        with tempfile.TemporaryDirectory(prefix='secondbrain-observatory-') as tmp:
            output = Path(tmp) / 'result.json'
            env = os.environ.copy()
            env.update({'DATABASE_URL': 'sqlite:///' + (Path(tmp) / 'benchmark.db').as_posix(),
                        'PYTHONPATH': str(BACKEND), 'MAIL_SYNC_ENABLED': 'false',
                        'WAKE_WORD_ENABLED': 'false', 'VOICE_ANNOUNCE_ENABLED': 'false',
                        'HF_HUB_OFFLINE': '1'})
            try:
                revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=BACKEND,
                                          capture_output=True, text=True, timeout=5)
                env['OBS_CODE_REVISION'] = revision.stdout.strip() or 'unknown'
                dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=BACKEND,
                                       capture_output=True, text=True, timeout=5)
                env['OBS_CODE_DIRTY'] = 'true' if dirty.stdout.strip() else 'false'
                child = subprocess.run([sys.executable, '-m', 'app.research.observatory_worker', str(output)],
                                       cwd=tmp, env=env, capture_output=True, text=True, timeout=300)
            except subprocess.TimeoutExpired:
                raise HTTPException(504, 'Benchmark timed out; live data was not used or reset')
            if child.returncode or not output.exists():
                # Child uses synthetic data only. Bound diagnostics for a useful actionable UI failure.
                raise HTTPException(503, {'message': 'Isolated benchmark failed; check research dependencies.',
                                          'diagnostic': child.stderr[-2000:]})
            result = json.loads(output.read_text())
        result['completed_at'] = datetime.utcnow().isoformat() + 'Z'
        row = ResearchRun(kind='observatory', system='core-tfidf', questions=11,
                          metrics_json=json.dumps(result), duration_ms=int((time.perf_counter()-started)*1000))
        db.add(row)
        db.commit()
        db.refresh(row)
        return {'id': row.id, 'created_at': row.created_at, 'data': result}
    finally:
        _run_lock.release()


class ProbePayload(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    mode: Literal['vanilla', 'hybrid', 'graph', 'adaptive', 'adaptive_graph'] = 'adaptive'
    k: int = Field(5, ge=1, le=20)


@router.post('/probe')
def probe(payload: ProbePayload, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.models.memory import Memory
    from app.models.research import ForgottenMemory
    from app.research.pipeline import AdaptiveMemoryRetrieval
    if not payload.query.strip():
        raise HTTPException(422, 'Query cannot be blank')
    forgotten = {r.memory_id for r in db.query(ForgottenMemory).all()}
    active_ids = {r.id for r in db.query(Memory.id).all()} - forgotten
    retriever = AdaptiveMemoryRetrieval()  # per-request trace, not the shared singleton
    results = retriever.retrieve(db, payload.query, limit=payload.k, mode=payload.mode,
                                 allowed_ids=active_ids, dense_backend='tfidf')
    return {'query': payload.query, 'mode': payload.mode, 'results': results,
            'trace': retriever.last_trace, 'sampled_at': datetime.utcnow().isoformat() + 'Z',
            'accuracy_metrics': None,
            'policy': 'All live probe modes exclude tombstones; differs from original benchmark baseline policies.',
            'note': 'Ranking uses existing stored research annotations; inspect live recalculated vs persisted importance separately. No gold labels or generated answer.'}
