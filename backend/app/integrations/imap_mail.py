"""
Gmail over IMAP - no OAuth, no Google Cloud project, no verification.
===========================================================================
Why this exists:
    Reading your OWN inbox through the Gmail API requires the `gmail.readonly`
    scope, which Google classifies as RESTRICTED. Publishing an app that uses a
    restricted scope requires a CASA security assessment (~$540-$1,800/yr,
    annual re-certification, 4-8 weeks). That is absurd for a personal
    assistant reading three personal mailboxes.

    IMAP with an App Password needs none of that: no consent screen, no
    verification, no 7-day token expiry, no yearly fee. It just works.

Trade-offs, stated honestly:
    * It is still reading your mail - an app password is a real credential, so
      it is encrypted at rest exactly like an OAuth token.
    * Google Workspace (college/work) accounts stopped accepting app passwords
      on 1 May 2025. Those must use OAuth.
    * IMAP gives no "snippet" for free, so a small part of each body is fetched
      to build one.

READ-ONLY SAFETY (important):
    Every mailbox is opened with `readonly=True`, and every body fetch uses
    BODY.PEEK instead of BODY. Both matter: without them, merely *listing* your
    inbox would silently mark all your unread mail as read. That would be a
    genuinely annoying bug.
"""
from __future__ import annotations

import email
import email.header
import email.utils
import imaplib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

GMAIL_HOST = "imap.gmail.com"
GMAIL_PORT = 993

# UI folder name -> Gmail IMAP mailbox
FOLDER_MAP = {
    "inbox": "INBOX",
    "unread": "INBOX",
    "important": "[Gmail]/Important",
    "starred": "[Gmail]/Starred",
    "sent": "[Gmail]/Sent Mail",
    "drafts": "[Gmail]/Drafts",
    "all": "[Gmail]/All Mail",
}

# IMAP search criteria per folder
FOLDER_SEARCH = {
    "unread": "UNSEEN",
}

MAX_FOLDERS = 40


class ImapError(RuntimeError):
    pass


def _decode(value: Optional[str]) -> str:
    """IMAP headers arrive as encoded-words, e.g. =?UTF-8?B?...?="""
    if not value:
        return ""
    try:
        parts = email.header.decode_header(value)
    except Exception:
        return str(value)

    out = []
    for text, charset in parts:
        if isinstance(text, bytes):
            try:
                out.append(text.decode(charset or "utf-8", "replace"))
            except (LookupError, TypeError):
                out.append(text.decode("utf-8", "replace"))
        else:
            out.append(text)
    return "".join(out).strip()


def _imap_quote(name: str) -> str:
    """Mailbox names with spaces/brackets must be quoted."""
    if any(ch in name for ch in ' [](){}%"\\'):
        escaped = name.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return name


def _clean_snippet(raw: str, limit: int = 180) -> str:
    """IMAP partial-body fetches include MIME scaffolding - strip it."""
    if not raw:
        return ""
    text = re.sub(r"-{2,}[A-Za-z0-9_=.\-]+", " ", raw)          # MIME boundaries
    text = re.sub(r"^[A-Za-z\-]+:\s.*$", " ", text, flags=re.M)  # stray headers
    text = re.sub(r"=\r?\n", "", text)                           # quoted-printable soft breaks
    text = re.sub(r"<[^>]+>", " ", text)                         # html tags
    text = re.sub(r"&[a-z]+;", " ", text)                        # html entities
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:limit]


class GmailImapClient:
    """One short-lived IMAP session per call - simpler and safer than pooling."""

    def __init__(self, address: str, app_password: str, host: str = GMAIL_HOST, port: int = GMAIL_PORT):
        self.address = (address or "").strip()
        self.app_password = (app_password or "").replace(" ", "").strip()
        self.host = host
        self.port = port

    # ------------------------------------------------------------ session
    def _connect(self) -> imaplib.IMAP4_SSL:
        if not self.address or not self.app_password:
            raise ImapError("Email address and app password are both required.")
        try:
            conn = imaplib.IMAP4_SSL(self.host, self.port, timeout=30)
        except Exception as exc:
            raise ImapError(
                f"Could not reach {self.host}:{self.port} ({type(exc).__name__}). "
                "Check your internet connection or any firewall/VPN."
            ) from exc

        try:
            conn.login(self.address, self.app_password)
        except imaplib.IMAP4.error as exc:
            conn.logout()
            detail = str(exc)
            if "Application-specific password required" in detail or "Invalid credentials" in detail:
                raise ImapError(
                    "Gmail rejected that app password. Make sure you generated it at "
                    "myaccount.google.com/apppasswords AFTER enabling 2-Step Verification, and "
                    "that you did not accidentally use your normal Google password."
                ) from exc
            if "authentication failed" in detail.lower():
                raise ImapError(
                    "Authentication failed. Either the app password is wrong, or this is a "
                    "Workspace (college/work) account - those cannot use app passwords since "
                    "May 2025 and must use Google OAuth instead."
                ) from exc
            raise ImapError(f"IMAP login failed: {detail}") from exc

        return conn

    # ------------------------------------------------------------- folders
    def list_folders(self) -> List[Dict[str, str]]:
        conn = self._connect()
        try:
            status, data = conn.list()
            if status != "OK":
                return []
            folders = []
            for entry in data[:MAX_FOLDERS]:
                line = entry.decode("utf-8", "replace") if isinstance(entry, bytes) else str(entry)
                match = re.search(r'"?([^"]*)"?$', line)
                if not match:
                    continue
                raw_name = match.group(1).strip()
                pretty = raw_name.replace("[Gmail]/", "").replace("INBOX", "Inbox")
                folders.append({"raw": raw_name, "label": pretty})
            return folders
        finally:
            self._safe_logout(conn)

    # ------------------------------------------------------------ messages
    def list_messages(self, folder: str = "inbox", limit: int = 30, query: str = "") -> List[Dict[str, Any]]:
        mailbox = FOLDER_MAP.get(folder, folder)
        criteria = FOLDER_SEARCH.get(folder, "ALL")
        if query:
            criteria = self._build_search(query)

        conn = self._connect()
        try:
            # readonly=True: listing must never alter your mailbox state.
            status, _ = conn.select(_imap_quote(mailbox), readonly=True)
            if status != "OK":
                raise ImapError(f"Mailbox '{mailbox}' is not available for this account.")

            status, data = conn.search(None, criteria)
            if status != "OK":
                return []

            uids = (data[0] or b"").split()
            if not uids:
                return []
            uids = uids[-limit:][::-1]  # newest first

            messages = []
            # Fetch in chunks so a big inbox does not blow up one IMAP command.
            for start in range(0, len(uids), 15):
                chunk = uids[start:start + 15]
                status, fetched = conn.fetch(
                    b",".join(chunk),
                    "(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)] "
                    "BODY.PEEK[TEXT]<0.400> FLAGS)",
                )
                if status != "OK":
                    continue
                messages.extend(self._parse_fetch_batch(fetched))
            return messages
        finally:
            self._safe_logout(conn)

    def get_message(self, uid: str, folder: str = "inbox") -> Dict[str, Any]:
        mailbox = FOLDER_MAP.get(folder, folder)
        conn = self._connect()
        try:
            status, _ = conn.select(_imap_quote(mailbox), readonly=True)
            if status != "OK":
                raise ImapError(f"Mailbox '{mailbox}' is not available.")

            # BODY.PEEK again - opening a message must not mark it as read.
            status, data = conn.fetch(uid.encode(), "(BODY.PEEK[] FLAGS)")
            if status != "OK" or not data:
                raise ImapError("That message could not be loaded - it may have been moved or deleted.")

            raw = self._extract_raw(data)
            if raw is None:
                raise ImapError("Message body was empty.")

            parsed = email.message_from_bytes(raw)
            return {
                "id": uid,
                "subject": _decode(parsed.get("Subject")) or "(no subject)",
                "from": _decode(parsed.get("From")),
                "to": _decode(parsed.get("To")),
                "date": _decode(parsed.get("Date")),
                "snippet": _clean_snippet(self._body_text(parsed), 240),
                "body": self._body_text(parsed),
                "unread": self._is_unread(self._extract_flags(data)),
                "labels": [],
            }
        finally:
            self._safe_logout(conn)

    # ------------------------------------------------------------- helpers
    @staticmethod
    def _build_search(query: str) -> str:
        """Translate Gmail-ish search into IMAP SEARCH criteria."""
        q = query.strip()
        lowered = q.lower()

        for prefix, field in (("from:", "FROM"), ("to:", "TO"), ("subject:", "SUBJECT")):
            if lowered.startswith(prefix):
                return f'{field} "{q[len(prefix):].strip()}"'

        if lowered in ("is:unread", "unread"):
            return "UNSEEN"
        if lowered in ("is:read", "read"):
            return "SEEN"
        if lowered.startswith("is:starred") or lowered == "starred":
            return "FLAGGED"

        # Fall back to a body/subject text search - quote it to be safe.
        safe = q.replace('"', " ").replace("\\", " ")
        return f'TEXT "{safe}"'

    def _parse_fetch_batch(self, fetched: list) -> List[Dict[str, Any]]:
        """
        Rebuild message dicts from an IMAP FETCH reply.

        One logical FETCH is a mix of tuples and bare bytes, e.g. for a single
        message:
            (b'2 (BODY[HEADER.FIELDS ...] {123}', <headers>)
            (b' BODY[TEXT]<0> {26}',              <body>)
            b' FLAGS ()'
        Only the FIRST tuple begins with the message number; the rest are
        continuations of it. Treating each tuple as its own message (an easy
        mistake) produces phantom entries with empty ids.
        """
        messages: List[Dict[str, Any]] = []
        current: Optional[Dict[str, Any]] = None

        for item in fetched:
            if isinstance(item, tuple):
                spec = item[0].decode("utf-8", "replace") if isinstance(item[0], bytes) else str(item[0])
                literal = next((p for p in item[1:] if isinstance(p, bytes)), b"")

                new_message = re.match(r"\s*(\d+)\s+\(", spec)
                if new_message:
                    uid = new_message.group(1)
                    current = {
                        "id": uid,
                        "thread_id": uid,
                        "subject": "(no subject)",
                        "from": "",
                        "to": "",
                        "date": "",
                        "snippet": "",
                        "labels": [],
                        "unread": True,
                        "important": False,
                    }
                    messages.append(current)

                if current is None:
                    continue

                upper = spec.upper()
                if "HEADER" in upper:
                    current["_raw_headers"] = literal
                elif "TEXT" in upper:
                    current["snippet"] = _clean_snippet(literal.decode("utf-8", "replace"))

            elif isinstance(item, bytes) and current is not None:
                flags = item.decode("utf-8", "replace")
                if "FLAGS" in flags:
                    current["unread"] = self._is_unread(flags)
                    current["important"] = "\\Flagged" in flags

        for message in messages:
            raw = message.pop("_raw_headers", b"")
            if not raw:
                continue
            parsed = email.message_from_bytes(raw)
            message["subject"] = _decode(parsed.get("Subject")) or "(no subject)"
            message["from"] = _decode(parsed.get("From"))
            message["to"] = _decode(parsed.get("To"))
            message["date"] = _decode(parsed.get("Date"))

        return messages

    @staticmethod
    def _extract_raw(data: list) -> Optional[bytes]:
        for item in data:
            if isinstance(item, tuple):
                for part in item[1:]:
                    if isinstance(part, bytes):
                        return part
            elif isinstance(item, bytes) and b"Subject:" in item:
                return item
        return None

    @staticmethod
    def _extract_flags(data: list) -> str:
        for item in data:
            if isinstance(item, bytes):
                return item.decode("utf-8", "replace")
        return ""

    @staticmethod
    def _is_unread(flags: str) -> bool:
        return "\\Seen" not in flags

    def _body_text(self, message) -> str:
        """Prefer text/plain, fall back to de-tagged text/html."""
        try:
            if message.is_multipart():
                for part in message.walk():
                    if part.get_content_type() == "text/plain" and not part.get_filename():
                        payload = part.get_payload(decode=True)
                        if payload:
                            return payload.decode(part.get_content_charset() or "utf-8", "replace")
                for part in message.walk():
                    if part.get_content_type() == "text/html" and not part.get_filename():
                        payload = part.get_payload(decode=True)
                        if payload:
                            html = payload.decode(part.get_content_charset() or "utf-8", "replace")
                            return re.sub(r"<[^>]+>", " ", html)
                return ""

            payload = message.get_payload(decode=True)
            if not payload:
                return ""
            text = payload.decode(message.get_content_charset() or "utf-8", "replace")
            if message.get_content_type() == "text/html":
                text = re.sub(r"<[^>]+>", " ", text)
            return text
        except Exception:
            return ""

    @staticmethod
    def _safe_logout(conn) -> None:
        try:
            conn.close()
        except Exception:
            pass
        try:
            conn.logout()
        except Exception:
            pass

    # ------------------------------------------------- incremental sync API
    # IMAP *sequence* numbers shift whenever mail is deleted or moved, so they
    # are useless as a saved cursor. UIDs are stable within a folder for as long
    # as UIDVALIDITY is unchanged - that pair is the correct cursor.
    def folder_state(self, folder: str = "inbox") -> Dict[str, Any]:
        """Returns {uidvalidity, uidnext, exists} for a mailbox."""
        mailbox = FOLDER_MAP.get(folder, folder)
        conn = self._connect()
        try:
            status, data = conn.select(_imap_quote(mailbox), readonly=True)
            if status != "OK":
                raise ImapError(f"Mailbox '{mailbox}' is not available for this account.")

            uidvalidity = None
            uidnext = None
            exists = 0
            for item in data:
                text = item.decode("utf-8", "replace") if isinstance(item, bytes) else str(item)
                match = re.search(r"UIDVALIDITY\s+(\d+)", text)
                if match:
                    uidvalidity = int(match.group(1))
                match = re.search(r"UIDNEXT\s+(\d+)", text)
                if match:
                    uidnext = int(match.group(1))
                match = re.search(r"(\d+)\s+EXISTS", text)
                if match:
                    exists = int(match.group(1))

            if uidvalidity is None:
                # Some servers only report it via STATUS
                status, status_data = conn.status(_imap_quote(mailbox), "(UIDVALIDITY UIDNEXT MESSAGES)")
                if status == "OK" and status_data:
                    text = status_data[0].decode("utf-8", "replace") if isinstance(status_data[0], bytes) else str(status_data[0])
                    match = re.search(r"UIDVALIDITY\s+(\d+)", text)
                    if match:
                        uidvalidity = int(match.group(1))
                    match = re.search(r"UIDNEXT\s+(\d+)", text)
                    if match:
                        uidnext = int(match.group(1))
                    match = re.search(r"MESSAGES\s+(\d+)", text)
                    if match:
                        exists = int(match.group(1))

            return {"uidvalidity": uidvalidity, "uidnext": uidnext, "exists": exists, "mailbox": mailbox}
        finally:
            self._safe_logout(conn)

    def list_uids_since(self, folder: str = "inbox", since_uid: int = 0, limit: int = 25) -> List[str]:
        """UIDs newer than `since_uid`, oldest-first so ingestion is chronological."""
        mailbox = FOLDER_MAP.get(folder, folder)
        conn = self._connect()
        try:
            status, _ = conn.select(_imap_quote(mailbox), readonly=True)
            if status != "OK":
                raise ImapError(f"Mailbox '{mailbox}' is not available for this account.")

            # UID SEARCH, not SEARCH: we need stable identifiers.
            status, data = conn.uid("SEARCH", None, f"UID {since_uid + 1}:*")
            if status != "OK":
                return []
            uids = [u.decode() for u in (data[0] or b"").split() if u.decode().isdigit()]
            # "UID n:*" always returns at least the last message even when nothing
            # is new, so filter explicitly.
            uids = [u for u in uids if int(u) > since_uid]
            return uids[:limit]
        finally:
            self._safe_logout(conn)

    def fetch_by_uids(self, folder: str, uids: List[str]) -> List[Dict[str, Any]]:
        """
        Fully parsed messages for the given UIDs, including the headers needed to
        tell real mail from bulk mail (List-Unsubscribe / Precedence).
        """
        if not uids:
            return []
        mailbox = FOLDER_MAP.get(folder, folder)
        conn = self._connect()
        results: List[Dict[str, Any]] = []
        try:
            status, _ = conn.select(_imap_quote(mailbox), readonly=True)
            if status != "OK":
                raise ImapError(f"Mailbox '{mailbox}' is not available for this account.")

            for chunk_start in range(0, len(uids), 10):
                chunk = uids[chunk_start:chunk_start + 10]
                # BODY.PEEK[] - never marks mail as read.
                status, data = conn.uid("FETCH", ",".join(chunk), "(BODY.PEEK[] FLAGS)")
                if status != "OK":
                    continue
                for uid, raw, flags in self._extract_uid_payloads(data):
                    try:
                        parsed = email.message_from_bytes(raw)
                    except Exception:
                        continue
                    results.append({
                        "uid": uid,
                        "subject": _decode(parsed.get("Subject")) or "(no subject)",
                        "from": _decode(parsed.get("From")),
                        "to": _decode(parsed.get("To")),
                        "cc": _decode(parsed.get("Cc")),
                        "date": _decode(parsed.get("Date")),
                        "date_parsed": self._parse_date(parsed.get("Date")),
                        "message_id": (parsed.get("Message-ID") or "").strip(),
                        "body": self._body_text(parsed),
                        "unread": self._is_unread(flags),
                        "flagged": "\\Flagged" in flags,
                        "list_unsubscribe": bool(parsed.get("List-Unsubscribe")),
                        "precedence": (parsed.get("Precedence") or "").lower(),
                        "auto_submitted": (parsed.get("Auto-Submitted") or "").lower(),
                        "folder": folder,
                    })
        finally:
            self._safe_logout(conn)
        return results

    @staticmethod
    def _parse_date(value: Optional[str]):
        if not value:
            return None
        try:
            parsed = email.utils.parsedate_to_datetime(value)
            if parsed and parsed.tzinfo:
                return parsed.astimezone(timezone.utc)
            return parsed
        except Exception:
            return None

    @staticmethod
    def _extract_uid_payloads(data: list):
        r"""
        Yield (uid, raw_bytes, flags) from a `UID FETCH ... (BODY.PEEK[] FLAGS)` reply.

        Wire format for two messages looks like:
            * 1 FETCH (UID 101 BODY[] {123}
            <123 raw bytes>
             FLAGS (\Seen))
            * 2 FETCH (UID 102 BODY[] {45}
            <45 raw bytes>
             FLAGS ())
        So: each tuple carries the spec + literal, and the FLAGS line that follows
        belongs to the message that was just read. Reading the UID out of the spec
        (rather than counting positionally) is what makes this reliable.
        """
        current = None  # {"uid": str, "raw": bytes, "flags": str}

        for item in data:
            if isinstance(item, tuple):
                spec = item[0].decode("utf-8", "replace") if isinstance(item[0], bytes) else str(item[0])
                literal = next((part for part in item[1:] if isinstance(part, bytes)), b"")

                uid_match = re.search(r"UID\s+(\d+)", spec) or re.match(r"\s*(\d+)\s+\(", spec)
                if not uid_match:
                    continue

                if current and current["raw"]:
                    yield current["uid"], current["raw"], current["flags"]

                current = {"uid": uid_match.group(1), "raw": literal, "flags": ""}

                # A trailer line may follow the literal; if it does not, this
                # message is already complete and is yielded on the next round.
            elif isinstance(item, bytes) and current is not None:
                text = item.decode("utf-8", "replace")
                if "FLAGS" in text:
                    current["flags"] = text

        if current and current["raw"]:
            yield current["uid"], current["raw"], current["flags"]

    # ------------------------------------------------------------ validate
    def verify(self) -> Dict[str, Any]:
        """Used by the connect endpoint to prove the credentials work."""
        conn = self._connect()
        try:
            status, _ = conn.select("INBOX", readonly=True)
            if status != "OK":
                raise ImapError("Logged in, but INBOX could not be opened.")
            status, data = conn.search(None, "ALL")
            total = len((data[0] or b"").split()) if status == "OK" else 0
            unread = 0
            status, data = conn.search(None, "UNSEEN")
            if status == "OK":
                unread = len((data[0] or b"").split())
            return {
                "ok": True,
                "address": self.address,
                "total_messages": total,
                "unread": unread,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
        finally:
            self._safe_logout(conn)
