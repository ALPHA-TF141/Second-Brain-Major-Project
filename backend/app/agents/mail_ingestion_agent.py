"""
Mail Ingestion Agent
===========================================================================
Reads connected mailboxes, turns each new email into a permanent memory, and
writes it into BOTH stores that matter:

  1. SQLite (`memories` + `search_index`)
       This is what /api/chat/ask actually searches. Without this row, Jarvis
       could store an email and still be unable to answer questions about it -
       the RAG pipeline only reads SQLite, never the vault JSON cards.

  2. Memory Vault (`memory_vault/cards/...`)
       via vault_agent.store_card(), which also updates the knowledge graph and
       compiles the email into the self-improving wiki, then syncs to GitHub.

Duplicate protection
    * IMAP   : UIDVALIDITY + last-UID cursor (stable identifiers)
    * Google : message-id ledger + `after:` date filter
    * Both   : a sha1 content hash against the `memories.content_hash` unique
               constraint, so re-running a sync can never double-store.

Read-only guarantee
    Every mailbox is opened with EXAMINE and every body pulled with BODY.PEEK,
    so syncing your mail NEVER marks anything as read.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.integrations.imap_mail import GmailImapClient, ImapError

# Bulk-mail signals that are provider agnostic (unlike Gmail's category labels)
BULK_PRECEDENCE = {"bulk", "list", "junk"}
BULK_AUTO_SUBMITTED = {"auto-generated", "auto-replied"}

DEADLINE_WORDS = (
    "deadline", "due date", "due by", "due on", "last date", "final date",
    "submit by", "submission", "submit before", "expires", "expiry", "expiring",
    "closes on", "closing date", "before the", "no later than", "by end of",
)
ACTION_WORDS = (
    "action required", "action needed", "please review", "please submit", "please confirm",
    "respond by", "reply by", "kindly", "request you to", "must be", "needs to be",
    "payment", "invoice", "amount due", "outstanding", "renew", "renewal",
    "verification", "verify", "otp", "one time password", "sign in attempt",
    "meeting", "interview", "schedule", "workshop", "viva", "seminar", "exam",
)
HIGH_PRIORITY_WORDS = (
    "urgent", "immediately", "asap", "important", "critical", "action required",
    "deadline today", "last date", "final reminder", "account suspended",
)

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "mon": 0, "tue": 1, "tues": 2, "wed": 3, "thu": 4, "thur": 5,
    "thurs": 5, "fri": 6, "sat": 5, "sun": 6,
}

MAX_LEDGER_SEEN = 20000
MAX_CARD_BODY = 6000


# ===========================================================================
class EmailLedger:
    """Sync cursors + already-ingested message ids. Contains no message bodies."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or (Path(__file__).resolve().parents[2] / "data" / "mail_ledger.json")
        self._lock = threading.RLock()

    def _read(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"cursors": {}, "seen": [], "sessions": {}, "stats": {}}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"cursors": {}, "seen": [], "sessions": {}, "stats": {}}

    def _write(self, data: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if len(data.get("seen", [])) > MAX_LEDGER_SEEN:
            data["seen"] = data["seen"][-MAX_LEDGER_SEEN:]
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        tmp.replace(self.path)

    # ---- cursors -----------------------------------------------------------
    def cursor(self, account_id: str, folder: str) -> Dict[str, Any]:
        with self._lock:
            return self._read().get("cursors", {}).get(f"{account_id}:{folder}", {})

    def set_cursor(self, account_id: str, folder: str, uidvalidity: int, last_uid: int) -> None:
        with self._lock:
            data = self._read()
            data.setdefault("cursors", {})[f"{account_id}:{folder}"] = {
                "uidvalidity": uidvalidity,
                "last_uid": last_uid,
                "updated_at": datetime.utcnow().isoformat(),
            }
            self._write(data)

    # ---- dedupe ------------------------------------------------------------
    def seen(self, key: str) -> bool:
        with self._lock:
            return key in set(self._read().get("seen", []))

    def mark_seen(self, key: str) -> None:
        with self._lock:
            data = self._read()
            seen = data.setdefault("seen", [])
            if key not in seen:
                seen.append(key)
            self._write(data)

    # ---- sessions / stats --------------------------------------------------
    def session_for(self, account_id: str) -> Optional[int]:
        with self._lock:
            value = self._read().get("sessions", {}).get(account_id)
            return int(value) if value else None

    def set_session(self, account_id: str, session_id: int) -> None:
        with self._lock:
            data = self._read()
            data.setdefault("sessions", {})[account_id] = session_id
            self._write(data)

    def record_sync(self, account_id: str, summary: Dict[str, Any]) -> None:
        with self._lock:
            data = self._read()
            stats = data.setdefault("stats", {}).setdefault(account_id, {})
            stats.update(summary)
            stats["last_sync"] = datetime.utcnow().isoformat()
            stats["total_ingested"] = int(stats.get("total_ingested", 0)) + int(summary.get("ingested", 0))
            self._write(data)

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            data = self._read()
            return {
                "stats": data.get("stats", {}),
                "cursors": data.get("cursors", {}),
                "seen_count": len(data.get("seen", [])),
            }


# ===========================================================================
class MailIngestionAgent:
    def __init__(self):
        self.ledger = EmailLedger()
        self.last_error = ""
        self.is_syncing = False

    # ------------------------------------------------------------- helpers
    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha1(value.encode("utf-8", "ignore")).hexdigest()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _extract_email(self, header_value: str) -> str:
        match = re.search(r"<([^>]+)>", header_value or "")
        if match:
            return match.group(1).strip().lower()
        return (header_value or "").strip().lower()

    @staticmethod
    def _clean_body(body: str, limit: int = MAX_CARD_BODY) -> str:
        text = (body or "").replace("\r\n", "\n")
        # drop quoted replies so the stored memory is the actual message
        lines = []
        for line in text.split("\n"):
            if re.match(r"^\s*>", line):
                continue
            if re.match(r"^\s*(On .+wrote:|-----Original Message-----)", line):
                break
            lines.append(line)
        cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
        return cleaned[:limit] if len(cleaned) > limit else cleaned

    # ------------------------------------------------- action / date detect
    def _detect_due_date(self, text: str) -> Optional[str]:
        """Best-effort date extraction. Returns an ISO date or None."""
        lowered = text.lower()
        now = self._now()

        # explicit ISO / numeric dates
        match = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text)
        if match:
            try:
                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3))).date().isoformat()
            except ValueError:
                pass

        match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", text)
        if match:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if year < 100:
                year += 2000
            if 1 <= day <= 31 and 1 <= month <= 12:
                try:
                    return datetime(year, month, day).date().isoformat()
                except ValueError:
                    pass

        # "25 September" / "September 25"
        match = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]{3,9})\b", lowered)
        if match and match.group(2)[:3] in MONTHS:
            day = int(match.group(1))
            month = MONTHS[match.group(2)[:3]]
            year = now.year
            try:
                candidate = datetime(year, month, day)
                if candidate.date() < now.date():
                    candidate = datetime(year + 1, month, day)
                return candidate.date().isoformat()
            except ValueError:
                pass

        match = re.search(r"\b([a-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?\b", lowered)
        if match and match.group(1)[:3] in MONTHS:
            day = int(match.group(2))
            month = MONTHS[match.group(1)[:3]]
            year = now.year
            try:
                candidate = datetime(year, month, day)
                if candidate.date() < now.date():
                    candidate = datetime(year + 1, month, day)
                return candidate.date().isoformat()
            except ValueError:
                pass

        # weekday names -> next occurrence
        for name, index in WEEKDAYS.items():
            if re.search(rf"\b{name}\b", lowered):
                delta = (index - now.weekday()) % 7
                if delta == 0:
                    delta = 7  # "by Friday" means the coming one
                return (now + timedelta(days=delta)).date().isoformat()

        if re.search(r"\b(today)\b", lowered):
            return now.date().isoformat()
        if re.search(r"\b(tomorrow)\b", lowered):
            return (now + timedelta(days=1)).date().isoformat()

        return None

    def detect_actions(self, subject: str, body: str) -> List[Dict[str, Any]]:
        """Rule-based action/deadline extraction from an email."""
        haystack = f"{subject}\n{body}".lower()
        actions: List[Dict[str, Any]] = []

        deadline_hit = next((w for w in DEADLINE_WORDS if w in haystack), None)
        action_hit = next((w for w in ACTION_WORDS if w in haystack), None)

        if not deadline_hit and not action_hit:
            return []

        due = self._detect_due_date(f"{subject}\n{body}")
        urgent = any(w in haystack for w in HIGH_PRIORITY_WORDS)

        # Build a readable task title from the subject, trimmed of list prefixes
        title = re.sub(r"^(re|fwd|fw)\s*:\s*", "", subject or "", flags=re.I).strip()
        title = re.sub(r"^\[[^\]]{1,24}\]\s*", "", title).strip() or "(no subject)"

        kind = "deadline" if deadline_hit else "action"
        priority = "high" if urgent else ("high" if deadline_hit else "medium")

        actions.append({
            "kind": kind,
            "title": f"{'Deadline' if kind == 'deadline' else 'Action'}: {title}"[:160],
            "due_date": due,
            "priority": priority,
            "trigger": deadline_hit or action_hit,
        })
        return actions

    def importance(self, message: Dict[str, Any], actions: List[Dict[str, Any]], own_addresses: set) -> str:
        """low | normal | high - drives whether the user gets interrupted."""
        sender = self._extract_email(message.get("from", ""))
        subject = (message.get("subject") or "").lower()

        if actions and actions[0]["priority"] == "high":
            return "high"
        if any(w in subject for w in ("urgent", "action required", "immediately", "asap")):
            return "high"
        if sender in own_addresses:
            return "normal"
        if message.get("unread") and message.get("flagged"):
            return "high"
        if actions:
            return "normal"
        if message.get("unread"):
            return "normal"
        return "low"

    def bulk_kind(self, message: Dict[str, Any]) -> str:
        """
        Classify bulk mail in two tiers, because "bulk" is not one thing:

          hard  - marketing/newsletters (List-Unsubscribe, auto-submitted).
                  Never enters the vault; it would pollute the wiki and graph.
          soft  - transactional bulk (Precedence: bulk) such as invoices and
                  billing notices. These are RECORD-KEEPING mail with real
                  amounts and due dates, so they are kept if they contain an
                  action, and dropped otherwise.

        Returns "hard", "soft" or "" (normal mail).
        """
        if message.get("list_unsubscribe"):
            return "hard"
        if any(marker in (message.get("auto_submitted") or "") for marker in BULK_AUTO_SUBMITTED):
            return "hard"
        if (message.get("precedence") or "") in BULK_PRECEDENCE:
            return "soft"
        return ""

    def is_bulk(self, message: Dict[str, Any]) -> bool:
        return self.bulk_kind(message) == "hard"

    # --------------------------------------------------------- persistence
    def _get_or_create_session(self, db: Session, user_id: int, account_id: str, address: str):
        from app.models.capture import MemorySession

        existing_id = self.ledger.session_for(account_id)
        if existing_id:
            session = db.query(MemorySession).filter(MemorySession.id == existing_id).first()
            if session:
                return session

        session = MemorySession(
            user_id=user_id,
            session_type="email",
            dominant_activity=f"Inbox: {address}",
            is_active=True,
            started_at=datetime.utcnow(),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        self.ledger.set_session(account_id, session.id)
        return session

    def _store_memory(self, db: Session, session_id: int, message: Dict[str, Any],
                      account_address: str, actions: List[Dict[str, Any]]) -> Optional[int]:
        """
        Write the SQLite memory + search index. Returns the memory id, or None if
        this exact content was already stored (the hash constraint protects us).
        """
        from app.memory.archive import MemoryArchive
        from app.models.memory import Memory, SearchIndex

        subject = message.get("subject") or "(no subject)"
        sender = message.get("from") or "unknown"
        body = self._clean_body(message.get("body", ""))

        action_lines = ""
        if actions:
            action_lines = "\n\nAction items:\n" + "\n".join(
                f"- {a['title']}" + (f" (due {a['due_date']})" if a["due_date"] else "")
                for a in actions
            )

        content = (
            f"Email received by {account_address}\n"
            f"From: {sender}\n"
            f"To: {message.get('to', '')}\n"
            f"Date: {message.get('date', '')}\n"
            f"Subject: {subject}\n\n"
            f"{body}{action_lines}"
        ).strip()

        content_hash = self._hash(content)
        if db.query(Memory).filter(Memory.content_hash == content_hash).first():
            return None

        archive = MemoryArchive()
        category = archive.tagger.category(content, "email", "gmail")
        tags = archive.tagger.tag(content, subject[:60], "email", "gmail")

        memory = Memory(
            session_id=session_id,
            title=subject[:220],
            content=content,
            content_hash=content_hash,
            source_type="email",
            app_source=account_address,
            topic_label=(subject[:80] or "Email"),
            category=category,
            created_at=message.get("date_parsed") or datetime.utcnow(),
        )
        db.add(memory)
        db.flush()

        for tag in tags:
            from app.models.memory import MemoryTag

            db.add(MemoryTag(memory_id=memory.id, tag=tag, source="email"))

        db.add(
            SearchIndex(
                memory_id=memory.id,
                session_id=session_id,
                searchable_text=f"{subject} {content} {account_address} {sender} {' '.join(tags)}",
                tags_text=", ".join(tags),
                app_source=account_address,
                source_type="email",
                topic_label=subject[:80],
                created_at=memory.created_at,
            )
        )
        db.commit()
        return memory.id

    def _store_vault_card(self, message: Dict[str, Any], account_address: str,
                          actions: List[Dict[str, Any]], importance: str, sync: bool = False):
        """JSON card -> knowledge graph + wiki + GitHub (via vault_agent)."""
        from app.agents.card_schema import JSONMemoryCard
        from app.agents.vault_agent import vault_agent

        subject = message.get("subject") or "(no subject)"
        sender = message.get("from") or "unknown"
        body = self._clean_body(message.get("body", ""), 1500)
        sender_email = self._extract_email(sender)

        pointers = []
        if actions:
            for action in actions:
                pointers.append(
                    f"{action['kind'].title()}: {action['title']}"
                    + (f" - due {action['due_date']}" if action["due_date"] else "")
                )
        pointers.append(f"From: {sender}")
        if message.get("date"):
            pointers.append(f"Received: {message['date']}")

        card = JSONMemoryCard(
            id=f"mail_{message.get('uid') or self._hash(subject)[:10]}_{self._hash(account_address + subject)[:6]}",
            timestamp=(message.get("date_parsed") or datetime.utcnow()).isoformat(),
            domain="Communication",
            priority="high" if importance == "high" else ("medium" if importance == "normal" else "low"),
            quality_score=0.9 if actions else 0.7,
            app_source="gmail",
            window_title=subject,
            topic=f"Email: {subject}",
            summary=f"Email from {sender} to {account_address} about: {subject}",
            key_pointers=pointers[:8],
            entities=[sender_email, account_address] + [a["trigger"] for a in actions],
            tags=["email", "inbox", sender_email.split("@")[-1], (actions[0]["kind"] if actions else "message")],
            source_url_or_ref=f"mailto:{sender_email}" if sender_email else None,
            raw_ocr_excerpt=body,
            hero_image=None,
        )

        # sync=False for bulk runs: vault_agent otherwise kicks off a GitHub push
        # per card. The existing 60-second vault loop picks them up instead.
        try:
            vault_agent.store_card(card, sync=sync)
        except TypeError:
            vault_agent.store_card(card)  # older signature
        return card.id

    # --------------------------------------------------------------- sync
    def sync_account(self, db: Session, account_id: str, user_id: int,
                     folders: Optional[List[str]] = None, limit: Optional[int] = None,
                     notify: bool = True, store_vault: bool = True) -> Dict[str, Any]:
        from app.integrations.local_store import EncryptedStore
        from app.integrations.token_store import google_token_store

        folders = folders or [f.strip() for f in settings.mail_sync_folders.split(",") if f.strip()]
        limit = limit or settings.mail_sync_limit
        summary: Dict[str, Any] = {
            "account_id": account_id, "ingested": 0, "skipped_bulk": 0,
            "duplicates": 0, "errors": [], "actions": 0, "messages": [],
        }

        if account_id.startswith("imap_"):
            store = EncryptedStore("imap_accounts.enc", collection="accounts")
            record = store.get(account_id)
            if not record:
                summary["errors"].append("Account not found")
                return summary
            address = record.get("email", "")
            client = GmailImapClient(address, record.get("app_password", ""))
            ingestor = self._sync_imap
        else:
            record = google_token_store.get_secret(account_id)
            if not record:
                summary["errors"].append("Account not found")
                return summary
            address = record.get("email", "")
            client = None
            ingestor = self._sync_google

        session = self._get_or_create_session(db, user_id, account_id, address)

        for folder in folders:
            try:
                result = ingestor(db, client, account_id, folder, limit, session, address,
                                  store_vault=store_vault)
                for key in ("ingested", "skipped_bulk", "duplicates", "actions"):
                    summary[key] += result.get(key, 0)
                summary["messages"].extend(result.get("messages", []))
                summary["errors"].extend(result.get("errors", []))
            except Exception as exc:
                summary["errors"].append(f"{folder}: {type(exc).__name__}: {exc}")

        self.ledger.record_sync(account_id, {
            "ingested": summary["ingested"],
            "skipped_bulk": summary["skipped_bulk"],
            "duplicates": summary["duplicates"],
            "actions": summary["actions"],
            "email": address,
        })

        if notify and summary["ingested"]:
            try:
                import asyncio

                from app.routes.os_store import os_store
                from app.websocket.manager import manager

                os_store.add_activity(
                    "email",
                    f"Ingested {summary['ingested']} email(s) from {address}",
                    "success",
                    f"{summary['actions']} action item(s) detected, {summary['skipped_bulk']} bulk skipped",
                )

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(manager.broadcast({
                        "type": "mail_sync",
                        "account": address,
                        "ingested": summary["ingested"],
                        "actions": summary["actions"],
                        "timestamp": datetime.utcnow().isoformat(),
                    }))
            except Exception:
                pass

        return summary

    def _sync_imap(self, db: Session, client: GmailImapClient, account_id: str, folder: str,
                   limit: int, session, address: str, store_vault: bool = True) -> Dict[str, Any]:
        out = {"ingested": 0, "skipped_bulk": 0, "duplicates": 0, "actions": 0,
               "messages": [], "errors": []}

        state = client.folder_state(folder)
        uidvalidity = state.get("uidvalidity")
        if uidvalidity is None:
            out["errors"].append("Server did not report UIDVALIDITY")
            return out

        cursor = self.ledger.cursor(account_id, folder)
        since = 0
        if cursor.get("uidvalidity") == uidvalidity:
            since = int(cursor.get("last_uid", 0))
        # a changed UIDVALIDITY means the mailbox was rebuilt -> resync from scratch

        uids = client.list_uids_since(folder, since_uid=since, limit=limit)
        if not uids:
            self.ledger.set_cursor(account_id, folder, uidvalidity, since)
            return out

        messages = client.fetch_by_uids(folder, uids)
        highest = since

        for message in messages:
            uid = int(message["uid"])
            highest = max(highest, uid)

            dedupe_key = f"{account_id}:imap:{uidvalidity}:{uid}"
            if self.ledger.seen(dedupe_key):
                out["duplicates"] += 1
                continue

            result = self._ingest_one(db, message, account_id, address, session,
                                      store_vault=store_vault)
            if result["stored"]:
                out["ingested"] += 1
                out["actions"] += result["actions"]
                out["messages"].append({
                    "subject": message.get("subject"),
                    "from": message.get("from"),
                    "importance": result["importance"],
                    "actions": result["actions"],
                })
            elif result["bulk"]:
                out["skipped_bulk"] += 1
            else:
                out["duplicates"] += 1

            self.ledger.mark_seen(dedupe_key)

        self.ledger.set_cursor(account_id, folder, uidvalidity, highest)
        return out

    def _sync_google(self, db: Session, client, account_id: str, folder: str, limit: int,
                     session, address: str, store_vault: bool = True) -> Dict[str, Any]:
        """Google path is synchronous-friendly: reuse the existing async client."""
        import asyncio

        from app.integrations import google_oauth

        out = {"ingested": 0, "skipped_bulk": 0, "duplicates": 0, "actions": 0,
               "messages": [], "errors": []}

        cursor = self.ledger.cursor(account_id, folder)
        since_epoch = int(cursor.get("last_epoch", 0))
        if not since_epoch:
            since_epoch = int((self._now() - timedelta(days=settings.mail_sync_backfill_days)).timestamp())

        query = f"in:inbox after:{since_epoch}"
        if folder == "unread":
            query = f"is:unread after:{since_epoch}"

        async def fetch():
            return await google_oauth.gmail_list_messages(account_id, query, limit)

        try:
            messages = asyncio.run(fetch())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                messages = loop.run_until_complete(fetch())
            finally:
                loop.close()

        for message in messages:
            message_id = message.get("id")
            dedupe_key = f"{account_id}:google:{message_id}"
            if self.ledger.seen(dedupe_key):
                out["duplicates"] += 1
                continue

            # list view has no body; fetch the full message before storing
            async def fetch_one():
                return await google_oauth.gmail_get_message(account_id, message_id)

            try:
                try:
                    full = asyncio.run(fetch_one())
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    try:
                        full = loop.run_until_complete(fetch_one())
                    finally:
                        loop.close()
            except Exception as exc:
                out["errors"].append(f"{message_id}: {exc}")
                continue

            full["date_parsed"] = None
            full["uid"] = message_id
            full["list_unsubscribe"] = False
            full["precedence"] = ""
            full["auto_submitted"] = ""

            result = self._ingest_one(db, full, account_id, address, session,
                                      store_vault=store_vault)
            if result["stored"]:
                out["ingested"] += 1
                out["actions"] += result["actions"]
                out["messages"].append({
                    "subject": full.get("subject"),
                    "from": full.get("from"),
                    "importance": result["importance"],
                    "actions": result["actions"],
                })
            elif result["bulk"]:
                out["skipped_bulk"] += 1
            else:
                out["duplicates"] += 1

            self.ledger.mark_seen(dedupe_key)

        self.ledger.set_cursor(account_id, folder, 0, 0)
        data = self.ledger._read()
        data.setdefault("cursors", {})[f"{account_id}:{folder}"] = {
            "uidvalidity": 0,
            "last_uid": 0,
            "last_epoch": int(self._now().timestamp()),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.ledger._write(data)
        return out

    # ------------------------------------------------------- one message
    def _ingest_one(self, db: Session, message: Dict[str, Any], account_id: str,
                    address: str, session, store_vault: bool = True) -> Dict[str, Any]:
        own = {address.lower()}
        bulk = self.bulk_kind(message)
        subject = message.get("subject") or ""
        body = self._clean_body(message.get("body", ""))
        actions = self.detect_actions(subject, body)
        importance = self.importance(message, actions, own)

        skip = settings.mail_sync_skip_bulk and bulk == "hard"
        # Transactional bulk (a bill, an invoice) is dropped from the vault only
        # when it carries no action - otherwise the deadline would be lost.
        if settings.mail_sync_skip_bulk and bulk == "soft" and not actions:
            skip = True

        if skip:
            return {"stored": False, "bulk": True, "actions": len(actions),
                    "importance": importance, "memory_id": None}

        memory_id = self._store_memory(db, session.id, message, address, actions)
        if memory_id is None:
            return {"stored": False, "bulk": False, "actions": 0,
                    "importance": importance, "memory_id": None}

        if store_vault:
            try:
                self._store_vault_card(message, address, actions, importance, sync=False)
            except Exception as exc:
                print(f"[MailIngest] Vault card failed for '{subject[:50]}': {exc}")

        if actions:
            self._create_tasks(actions, message, address)
            self._notify_actions(actions, message, address)

        if importance == "high":
            self._notify_important(message, address, actions)

        return {"stored": True, "bulk": False, "actions": len(actions),
                "importance": importance, "memory_id": memory_id}

    def _create_tasks(self, actions: List[Dict[str, Any]], message: Dict[str, Any], address: str):
        try:
            from app.routes.os_store import os_store

            for action in actions:
                os_store.add_task({
                    "title": action["title"],
                    "project": "Email Follow-ups",
                    "priority": action["priority"],
                    "due_date": action["due_date"] or "",
                    "status": "pending",
                    "ai_suggested": True,
                    "source": f"email:{address}",
                })
        except Exception as exc:
            print(f"[MailIngest] Task creation failed: {exc}")

    def _notify_actions(self, actions: List[Dict[str, Any]], message: Dict[str, Any], address: str):
        try:
            from app.routes.os_store import os_store

            for action in actions:
                due = f" - due {action['due_date']}" if action["due_date"] else ""
                os_store.add_notification({
                    "title": action["title"],
                    "body": f"From {self._extract_email(message.get('from', ''))} ({address}){due}",
                    "kind": "email_action",
                    "priority": action["priority"],
                    "source": "mail",
                })
        except Exception as exc:
            print(f"[MailIngest] Notification failed: {exc}")

    def _notify_important(self, message: Dict[str, Any], address: str, actions: List[Dict[str, Any]]):
        try:
            from app.routes.os_store import os_store

            os_store.add_notification({
                "title": f"Important email: {message.get('subject', '(no subject)')[:90]}",
                "body": f"From {self._extract_email(message.get('from', ''))} to {address}",
                "kind": "email_important",
                "priority": "high",
                "source": "mail",
            })
        except Exception as exc:
            print(f"[MailIngest] Notification failed: {exc}")

    # ------------------------------------------------------------ sync all
    def sync_all(self, db: Session, user_id: int, notify: bool = True) -> Dict[str, Any]:
        from app.integrations.local_store import EncryptedStore
        from app.integrations.token_store import google_token_store

        if self.is_syncing:
            return {"skipped": True, "reason": "A sync is already running"}

        self.is_syncing = True
        results = []
        try:
            accounts = []
            try:
                accounts.extend(a["id"] for a in EncryptedStore("imap_accounts.enc", collection="accounts").all())
            except Exception:
                pass
            try:
                accounts.extend(
                    a["id"] for a in google_token_store.list_accounts()
                    if "gmail" in (a.get("services") or ["gmail"])
                )
            except Exception:
                pass

            for account_id in accounts:
                try:
                    results.append(self.sync_account(db, account_id, user_id, notify=notify))
                except Exception as exc:
                    results.append({"account_id": account_id,
                                    "errors": [f"{type(exc).__name__}: {exc}"],
                                    "ingested": 0})
            return {
                "accounts": len(accounts),
                "ingested": sum(r.get("ingested", 0) for r in results),
                "actions": sum(r.get("actions", 0) for r in results),
                "skipped_bulk": sum(r.get("skipped_bulk", 0) for r in results),
                "results": results,
            }
        finally:
            self.is_syncing = False

    def status(self) -> Dict[str, Any]:
        ledger_stats = self.ledger.stats()
        return {
            "enabled": settings.mail_sync_enabled,
            "interval_minutes": settings.mail_sync_interval_minutes,
            "folders": [f.strip() for f in settings.mail_sync_folders.split(",") if f.strip()],
            "limit_per_run": settings.mail_sync_limit,
            "skip_bulk": settings.mail_sync_skip_bulk,
            "store_in_vault": settings.mail_store_in_vault,
            "is_syncing": self.is_syncing,
            "last_error": self.last_error,
            **ledger_stats,
        }


mail_ingestion_agent = MailIngestionAgent()
