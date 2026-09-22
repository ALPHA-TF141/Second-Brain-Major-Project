"""
Encrypted OAuth token storage.
===========================================================================
Why encryption matters here specifically:

  This app pushes the `memory_vault/` directory to a PUBLIC GitHub repo every
  60 seconds. OAuth refresh tokens are permanent keys to the user's Gmail and
  Calendar. If a token ever ended up in a synced file, it would be published.

  So tokens are:
    1. stored under `backend/data/` (git-ignored),
    2. encrypted at rest with Fernet (AES-128-CBC + HMAC), and
    3. never referenced from anything that gets committed or vaulted.

The key itself lives next to the tokens in `backend/data/integrations/`, which
is also git-ignored. This is not protection against an attacker who already has
your disk - it is protection against accidental publication, which is the real
risk in this architecture.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken

# Names that must never appear in a committed / vault-synced path
_VAULT_MARKERS = ("memory_vault",)


class TokenStoreUnavailable(RuntimeError):
    pass


class GoogleTokenStore:
    """Encrypted JSON store for connected Google accounts."""

    def __init__(self, directory: str = "./data/integrations"):
        self.directory = Path(directory)
        self.accounts_file = self.directory / "google_accounts.enc"
        self.key_file = self.directory / ".token_key"
        self._lock = threading.Lock()
        self._fernet: Optional[Fernet] = None

    # ------------------------------------------------------------------ safety
    def _assert_safe_path(self) -> None:
        resolved = str(self.directory.resolve()).lower()
        for marker in _VAULT_MARKERS:
            if marker in resolved:
                raise TokenStoreUnavailable(
                    f"Refusing to store OAuth tokens inside '{marker}' - that directory "
                    "is synchronised to GitHub. Point google_token_dir at a private path."
                )

    # ------------------------------------------------------------------- key
    def _get_fernet(self) -> Fernet:
        if self._fernet is not None:
            return self._fernet

        self._assert_safe_path()
        self.directory.mkdir(parents=True, exist_ok=True)

        if self.key_file.exists():
            key = self.key_file.read_bytes().strip()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            # Best effort: restrict to the owner on POSIX systems.
            try:
                os.chmod(self.key_file, 0o600)
            except OSError:
                pass

        self._fernet = Fernet(key)
        return self._fernet

    # ------------------------------------------------------------------- io
    def _read_all(self) -> Dict[str, Any]:
        if not self.accounts_file.exists():
            return {"accounts": []}
        try:
            raw = self._fernet_or_raise().decrypt(self.accounts_file.read_bytes())
            return json.loads(raw.decode("utf-8"))
        except InvalidToken:
            # Key rotated or file corrupted - do not guess, surface it.
            raise TokenStoreUnavailable(
                "Stored Google tokens could not be decrypted (key changed or file corrupted). "
                "Delete backend/data/integrations/ and reconnect your accounts."
            )
        except json.JSONDecodeError:
            return {"accounts": []}

    def _fernet_or_raise(self) -> Fernet:
        try:
            return self._get_fernet()
        except Exception as exc:  # pragma: no cover - depends on host
            raise TokenStoreUnavailable(f"Token encryption unavailable: {exc}") from exc

    def _write_all(self, payload: Dict[str, Any]) -> None:
        self._assert_safe_path()
        self.directory.mkdir(parents=True, exist_ok=True)
        blob = self._fernet_or_raise().encrypt(json.dumps(payload, indent=2).encode("utf-8"))

        # Write atomically so a crash mid-write cannot destroy every token.
        tmp = self.accounts_file.with_suffix(".tmp")
        tmp.write_bytes(blob)
        tmp.replace(self.accounts_file)
        try:
            os.chmod(self.accounts_file, 0o600)
        except OSError:
            pass

    # --------------------------------------------------------------- public
    def list_accounts(self) -> List[Dict[str, Any]]:
        """Account metadata WITHOUT secrets - safe to send to the frontend."""
        with self._lock:
            data = self._read_all()
        return [self._public(a) for a in data.get("accounts", [])]

    @staticmethod
    def _public(account: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": account.get("id"),
            "email": account.get("email"),
            "name": account.get("name", ""),
            "picture": account.get("picture", ""),
            "services": account.get("services", []),
            "scopes": account.get("scopes", []),
            "connected_at": account.get("connected_at"),
            "last_used": account.get("last_used"),
            "status": account.get("status", "connected"),
            "error": account.get("error", ""),
        }

    def get_secret(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Full record INCLUDING the refresh token. Backend-internal only."""
        with self._lock:
            data = self._read_all()
        for account in data.get("accounts", []):
            if account.get("id") == account_id:
                return account
        return None

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        email = (email or "").strip().lower()
        with self._lock:
            data = self._read_all()
        for account in data.get("accounts", []):
            if (account.get("email") or "").lower() == email:
                return account
        return None

    def upsert_account(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or refresh an account, keyed on email address."""
        with self._lock:
            data = self._read_all()
            accounts = data.setdefault("accounts", [])
            email = (record.get("email") or "").lower()

            for index, existing in enumerate(accounts):
                if (existing.get("email") or "").lower() == email:
                    # Keep the original connected_at, refresh everything else.
                    record["connected_at"] = existing.get("connected_at") or record.get("connected_at")
                    accounts[index] = {**existing, **record}
                    self._write_all(data)
                    return self._public(accounts[index])

            accounts.append(record)
            self._write_all(data)
            return self._public(record)

    def update_account(self, account_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            data = self._read_all()
            for account in data.get("accounts", []):
                if account.get("id") == account_id:
                    account.update(updates)
                    self._write_all(data)
                    return self._public(account)
        return None

    def remove_account(self, account_id: str) -> bool:
        with self._lock:
            data = self._read_all()
            before = len(data.get("accounts", []))
            data["accounts"] = [a for a in data.get("accounts", []) if a.get("id") != account_id]
            if len(data["accounts"]) == before:
                return False
            self._write_all(data)
            return True

    def touch(self, account_id: str) -> None:
        self.update_account(account_id, {"last_used": datetime.utcnow().isoformat()})


google_token_store = GoogleTokenStore()
