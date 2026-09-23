"""
Test isolation for credential stores.
===========================================================================
WHY THIS EXISTS

Both integration test suites used to run against the REAL credential
directory, `backend/data/integrations/`. That directory holds:

    .token_key            the Fernet key that encrypts everything else
    google_accounts.enc   connected Google / Gmail / Calendar accounts
    imap_accounts.enc     connected mailboxes (app passwords)
    calendar_feeds.enc    subscribed iCal / ICS feeds

`test_google_integration.py` deleted the whole directory and pointed the global
token store back at it; `test_mail_calendar.py` deleted the two `.enc` files by
name. Both are steps of `verify-jarvis.ps1` (gates 7 and 8), so every
verification run wiped the user's connected accounts -- and because the key file
went with them, even a surviving `.enc` would have been undecryptable. The
symptom the user reported is exactly that: "I have to connect my accounts all
the time."

THE CONTRACT

    with isolated_credentials("google") as harness:
        ...run the test, writing only inside `harness`...

Inside the block, every credential store points at a private directory under
`backend/data/_test_harness_<label>/`. On exit the harness directory is removed,
the singletons are pointed back at the real directory, and the real directory is
re-checked file by file. If anything there changed, that is a test failure, not a
warning -- the whole point is that a future edit cannot silently reintroduce the
bug.
"""
from __future__ import annotations

import hashlib
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, Optional, Tuple

# The real credential directory, resolved from this file's location so it does
# NOT depend on the process working directory. That independence is the second
# half of the bug: the stores default to the relative path "./data/integrations",
# so a process started from anywhere but backend/ would silently use a different
# directory and appear to have lost every account.
BACKEND_DIR = Path(__file__).resolve().parent
REAL_CREDENTIAL_DIR = BACKEND_DIR / "data" / "integrations"
HARNESS_ROOT = BACKEND_DIR / "data"

PROTECTED_FILES = (".token_key", "google_accounts.enc", "imap_accounts.enc",
                   "calendar_feeds.enc")


def _snapshot(directory: Path) -> Dict[str, str]:
    """Hash every protected file so tampering is detectable, not just visible."""
    out: Dict[str, str] = {}
    if not directory.is_dir():
        return out
    for name in sorted(PROTECTED_FILES):
        path = directory / name
        if path.is_file():
            out[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def _all_files(directory: Path) -> Dict[str, int]:
    """Every file in the directory, name -> size. Catches files we did not name."""
    out: Dict[str, int] = {}
    if not directory.is_dir():
        return out
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(directory))] = path.stat().st_size
    return out


def describe_real_credentials() -> str:
    """One-line summary for the test's own output, e.g. '3 file(s) present'."""
    snapshot = _snapshot(REAL_CREDENTIAL_DIR)
    if not snapshot:
        return "none present (nothing to protect)"
    return f"{len(snapshot)} file(s) present: " + ", ".join(sorted(snapshot))


def _repoint_stores(directory: Path) -> None:
    """
    Point every credential store at `directory`, in place.

    The stores are module-level singletons that routes captured at import time,
    so re-initialising the SAME objects is what actually redirects the running
    application. Replacing the objects would leave `app.routes.mail` holding the
    old ones.
    """
    from app.config import settings
    from app.integrations.token_store import google_token_store

    settings.google_token_dir = str(directory)
    google_token_store.__init__(directory=str(directory))

    from app.routes import mail as mail_routes

    mail_routes.mail_accounts.__init__("imap_accounts.enc", directory=str(directory),
                                       collection="accounts")
    mail_routes.calendar_feeds.__init__("calendar_feeds.enc", directory=str(directory),
                                        collection="feeds")


_ACTIVE: Optional[dict] = None


def activate(label: str) -> Path:
    """
    Point the credential stores at a private harness directory.

    Used by the two suites that wrap their whole body rather than indenting it;
    pair with verify_and_restore() in a finally block.
    """
    global _ACTIVE
    if _ACTIVE is not None:
        raise RuntimeError("credentials are already isolated in this process")

    harness = HARNESS_ROOT / f"_test_harness_{label}"
    if harness.parent.resolve() != HARNESS_ROOT.resolve():
        raise RuntimeError(f"refusing to use a harness outside {HARNESS_ROOT}: {harness}")

    _ACTIVE = {
        "path": harness,
        "before": _all_files(REAL_CREDENTIAL_DIR),
        "hashes": _snapshot(REAL_CREDENTIAL_DIR),
    }

    if harness.exists():
        shutil.rmtree(harness, ignore_errors=True)
    harness.mkdir(parents=True, exist_ok=True)
    _repoint_stores(harness)
    return harness


def active_dir() -> Path:
    if _ACTIVE is None:
        raise RuntimeError("activate() was not called")
    return _ACTIVE["path"]


def verify_and_restore() -> None:
    """
    Point the stores back at the real directory, delete the harness, and raise if
    the real credential directory changed while the test ran.
    """
    global _ACTIVE
    if _ACTIVE is None:
        return
    state = _ACTIVE
    _ACTIVE = None

    _repoint_stores(REAL_CREDENTIAL_DIR)
    shutil.rmtree(state["path"], ignore_errors=True)

    after = _all_files(REAL_CREDENTIAL_DIR)
    after_hashes = _snapshot(REAL_CREDENTIAL_DIR)
    if state["before"] != after or state["hashes"] != after_hashes:
        missing = sorted(set(state["before"]) - set(after))
        added = sorted(set(after) - set(state["before"]))
        changed = sorted(n for n in state["hashes"]
                         if n in after_hashes and state["hashes"][n] != after_hashes[n])
        raise AssertionError(
            "the real credential directory was modified by this test: "
            f"missing={missing} added={added} changed={changed}")


@contextmanager
def isolated_credentials(label: str) -> Iterator[Path]:
    """
    Run a test against a private credential directory.

    Yields the harness path. Guarantees that the real credential directory is
    byte-identical afterwards, and that the stores are pointed back at it.
    """
    harness = HARNESS_ROOT / f"_test_harness_{label}"

    # Refuse to operate on anything that is not the harness we created. A typo in
    # a deletion target is how the real credentials were lost the first time.
    if harness.parent.resolve() != HARNESS_ROOT.resolve():
        raise RuntimeError(f"refusing to use a harness outside {HARNESS_ROOT}: {harness}")

    before = _all_files(REAL_CREDENTIAL_DIR)
    before_hashes = _snapshot(REAL_CREDENTIAL_DIR)

    if harness.exists():
        shutil.rmtree(harness, ignore_errors=True)
    harness.mkdir(parents=True, exist_ok=True)
    _repoint_stores(harness)

    try:
        yield harness
    finally:
        # Point the application back at the real directory before anything else,
        # so a failure inside the test cannot leave the app reading the harness.
        _repoint_stores(REAL_CREDENTIAL_DIR)
        shutil.rmtree(harness, ignore_errors=True)

        after = _all_files(REAL_CREDENTIAL_DIR)
        after_hashes = _snapshot(REAL_CREDENTIAL_DIR)

        if before != after or before_hashes != after_hashes:
            missing = sorted(set(before) - set(after))
            added = sorted(set(after) - set(before))
            changed = sorted(n for n in before_hashes
                             if n in after_hashes and before_hashes[n] != after_hashes[n])
            raise AssertionError(
                "the real credential directory was modified by this test: "
                f"missing={missing} added={added} changed={changed}"
            )


def real_credentials_intact(before: Dict[str, int]) -> Tuple[bool, str]:
    """Explicit check a test can assert on, for a visible PASS line."""
    after = _all_files(REAL_CREDENTIAL_DIR)
    if before == after:
        return True, f"{len(after)} file(s) unchanged"
    return False, f"before={sorted(before)} after={sorted(after)}"


def snapshot_real_credentials() -> Dict[str, int]:
    return _all_files(REAL_CREDENTIAL_DIR)
