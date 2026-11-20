"""Private child process entrypoint; invoked only with an isolated DATABASE_URL."""
import importlib.metadata
import hashlib
import json
import os
import platform
import sys
from pathlib import Path


def main():
    from app.database.init_db import Base, engine, SessionLocal
    from app.models.user import User
    from app.research.bench import benchmark_runner
    from app.research.observatory import audit_result
    from app.research.graph_builder import extractor_mode
    from app.research.neural_nli import neural_nli

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        # Do not seed real application identities or connector metadata.
        db.add(User(username='observatory-synthetic', password_hash='not-a-login'))
        db.commit()
        result = benchmark_runner.run_all(db, k=5, dense_backend='tfidf')
    packages = {}
    for name in ['numpy', 'sqlalchemy', 'spacy', 'onnxruntime', 'tokenizers', 'huggingface-hub']:
        try: packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: packages[name] = None
    source = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for path in sorted(source.rglob('*.py')):
        digest.update(path.relative_to(source).as_posix().encode())
        digest.update(path.read_bytes())
    result['provenance'] = {
        'python': platform.python_version(), 'packages': packages,
        'graph_extractor': extractor_mode(),
        'code_revision': os.environ.get('OBS_CODE_REVISION', 'unknown'),
        'source_sha256': digest.hexdigest(),
        'working_tree_dirty': os.environ.get('OBS_CODE_DIRTY') == 'true',
        'model_downloads': 'disabled in child (HF_HUB_OFFLINE=1); cached optional models only',
        'nli_loaded': bool(neural_nli._available),
        'nli_error': getattr(neural_nli, '_init_error', None),
        'nli_repo': neural_nli.repo_id,
        'warning': 'Model revision is not pinned by the existing loader. Environment may differ from paper.',
        'isolation': 'fresh temporary SQLite database and child process',
        'dense_backend': 'tfidf', 'k': 5,
        'evaluation_clock': benchmark_runner.bench.now.isoformat(),
        'policy': 'Original benchmark policies: adaptive excludes tombstones; baselines do not. Not an equal-deletion-policy ranking test.',
    }
    Path(sys.argv[1]).write_text(json.dumps(audit_result(result), default=str))


if __name__ == '__main__':
    main()
