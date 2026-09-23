"""
Generic encrypted credential store.
===========================================================================
`google_oauth` tokens and `imap` app passwords are both long-lived credentials
that grant access to the user's mail. They get the same protection:

  * Fernet (AES-128-CBC + HMAC) encryption at rest
  * stored under backend/data/ (git-ignored, never part of the vault sync)
  * a hard refusal to write anywhere inside memory_vault/

This reuses the SAME key file as the Google store, so there is one secret to
manage, not two.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken

_VAULT_MARKERS = ("memory_vault",)


class StoreUnavailable(RuntimeError):
    pass


class EncryptedStore:
    """A single encrypted JSON file holding a list of records."""

    def __init__(self, filename: str, directory: Optional[str] = None,
                 collection: str = "items"):
        # None -> the resolved absolute default; never working-directory relative
        # (see app.config.credentials_dir for why that mattered).
        if not directory:
            from app.config import credentials_dir

            directory = credentials_dir()
        self.directory = Path(directory)
        self.file = self.directory / filename
        self.key_file = self.directory / ".token_key"
        self.collection = collection
        self._lock = threading.RLock()
        self._fernet: Optional[Fernet] = None

    # ------------------------------------------------------------- safety
    def _assert_safe_path(self) -> None:
        resolved = str(self.directory.resolve()).lower()
        for marker in _VAULT_MARKERS:
            if marker in resolved:
                raise StoreUnavailable(
                    f"Refusing to store credentials inside '{marker}' - that directory is "
                    "synchronised to GitHub. Use a private path."
                )

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
            try:
                os.chmod(self.key_file, 0o600)
            except OSError:
                pass

        self._fernet = Fernet(key)
        return self._fernet

    # ----------------------------------------------------------------- io
    def _read(self) -> Dict[str, Any]:
        if not self.file.exists():
            return {self.collection: []}
        try:
            raw = self._get_fernet().decrypt(self.file.read_bytes())
            return json.loads(raw.decode("utf-8"))
        except InvalidToken:
            raise StoreUnavailable(
                "Stored credentials could not be decrypted (key changed or file corrupted). "
                "Disconnect and reconnect."
            )
        except json.JSONDecodeError:
            return {self.collection: []}

    def _write(self, payload: Dict[str, Any]) -> None:
        self._assert_safe_path()
        self.directory.mkdir(parents=True, exist_ok=True)
        blob = self._get_fernet().encrypt(json.dumps(payload, indent=2).encode("utf-8"))
        tmp = self.file.with_suffix(".tmp")
        tmp.write_bytes(blob)
        tmp.replace(self.file)
        try:
            os.chmod(self.file, 0o600)
        except OSError:
            pass

    # -------------------------------------------------------------- api
    def all(self, include_secrets: bool = False) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._read().get(self.collection, []))
        if include_secrets:
            return items
        return [self.redact(i) for i in items]

    def get(self, item_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for item in self._read().get(self.collection, []):
                if item.get("id") == item_id:
                    return item
        return None

    def put(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update, keyed on `id`."""
        with self._lock:
            data = self._read()
            items = data.setdefault(self.collection, [])
            for index, existing in enumerate(items):
                if existing.get("id") == record.get("id"):
                    record.setdefault("created_at", existing.get("created_at"))
                    items[index] = {**existing, **record}
                    self._write(data)
                    return self.redact(items[index])
            record.setdefault("created_at", datetime.utcnow().isoformat())
            items.append(record)
            self._write(data)
            return self.redact(record)

    def update(self, item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            data = self._read()
            for item in data.get(self.collection, []):
                if item.get("id") == item_id:
                    item.update(updates)
                    self._write(data)
                    return self.redact(item)
        return None

    def remove(self, item_id: str) -> bool:
        with self._lock:
            data = self._read()
            before = len(data.get(self.collection, []))
            data[self.collection] = [i for i in data.get(self.collection, []) if i.get("id") != item_id]
            if len(data[self.collection]) == before:
                return False
            self._write(data)
            return True

    # ----------------------------------------------------------- redact
    SECRET_KEYS = ("app_password", "refresh_token", "access_token", "secret_url")

    def redact(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Strip secrets before anything reaches the frontend."""
        safe = {k: v for k, v in record.items() if k not in self.SECRET_KEYS}
        # For calendar feeds keep only a masked hint of the URL
        url = record.get("secret_url")
        if url:
            safe["url_hint"] = f"{url[:48]}…{url[-12:]}" if len(url) > 70 else "…"
        return safe
