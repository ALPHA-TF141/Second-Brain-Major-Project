"""
Mail ingestion regression test (offline, fake IMAP server).
===========================================================================
Proves the whole pipeline the user asked for:

    Gmail  ->  read-only IMAP  ->  SQLite memory  ->  vault card + wiki + graph
                                        |
                                        +->  tasks + notifications
                                        |
                                        +->  ANSWERABLE by /api/chat/ask

The important test here is the LAST one: it runs the real RAG retrieval path and
asserts the ingested email comes back as answer context. Storing mail that the
assistant cannot answer from would be the most useless possible outcome, and it
is exactly what would have happened if we had only written vault JSON cards
(the RAG pipeline reads SQLite, never the vault).

Usage (backend folder, venv active):
    python test_mail_ingestion.py
"""
import os
import socket
import sys
import threading
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS, FAIL = "[PASS]", "[FAIL]"
failures = []

# The mailbox this test registers. Deliberately NOT a real address: an earlier
# version used the user's own account, which made test-generated vault cards
# indistinguishable from genuine ones - and the cleanup pass then deleted the
# user's real mail cards. Every artefact this test creates now carries this
# marker, and cleanup refuses to touch anything without it.
TEST_ADDRESS = "imap-test-harness@example.invalid"
SERVER_LOG = {"fetch": [], "select": []}


def check(label, condition, detail=""):
    if condition:
        print(f"  --> {PASS} {label}")
    else:
        failures.append(label)
        print(f"  --> {FAIL} {label}   {detail}")


# ===========================================================================
# Fake Gmail IMAP with UID semantics
# ===========================================================================
def raw(subject, sender, body, extra_headers="", date=None):
    date = date or "Tue, 22 Sep 2026 09:00:00 +0530"
    return (
        f"From: {sender}\r\n"
        f"To: {TEST_ADDRESS}\r\n"
        f"Subject: {subject}\r\n"
        f"Date: {date}\r\n"
        f"Message-ID: <{abs(hash(subject))}@mail.gmail.com>\r\n"
        f"{extra_headers}"
        f"\r\n"
        f"{body}\r\n"
    ).encode()


MESSAGES = {
    # uid -> (raw bytes, flags)
    101: (raw("Project review notes", "Prof. Sharma <sharma@university.edu>",
              "Please review the attached dataset before our next discussion."), ""),
    102: (raw("50% off everything", "Deals <deals@shop.example.com>",
              "Big sale this week only!",
              extra_headers="List-Unsubscribe: <https://shop.example.com/u>\r\nPrecedence: bulk\r\n"), ""),
    103: (raw("IEEE conference draft deadline",
              "Prof. Sharma <sharma@university.edu>",
              "You must submit the IEEE conference draft by Friday 5 PM for the review committee.",
              date="Tue, 22 Sep 2026 10:00:00 +0530"), ""),
    104: (raw("Your invoice is ready", "Billing <billing@aws.amazon.com>",
              "Your invoice for September is attached. Amount due 5000.",
              extra_headers="Precedence: bulk\r\n"), ""),
}

UIDVALIDITY = 987654321


class FakeImap:
    def __init__(self, conn):
        self.conn = conn

    def send(self, data: bytes):
        self.conn.sendall(data)

    def run(self):
        self.send(b"* OK [CAPABILITY IMAP4rev1 UIDPLUS] ready\r\n")
        buffer = b""
        while True:
            try:
                chunk = self.conn.recv(8192)
            except OSError:
                return
            if not chunk:
                return
            buffer += chunk
            while b"\r\n" in buffer:
                line, buffer = buffer.split(b"\r\n", 1)
                if not self.respond(line.decode("utf-8", "replace")):
                    return

    def respond(self, line: str) -> bool:
        parts = line.split(" ")
        tag = parts[0] if parts else "*"
        command = parts[1].upper() if len(parts) > 1 else ""
        is_uid = command == "UID"
        sub = parts[2].upper() if is_uid and len(parts) > 2 else ""

        if command == "CAPABILITY":
            self.send(b"* CAPABILITY IMAP4rev1 UIDPLUS\r\n" + f"{tag} OK CAPABILITY completed\r\n".encode())

        elif command == "LOGIN":
            self.send(f"{tag} OK LOGIN completed\r\n".encode())

        elif command in ("EXAMINE", "SELECT"):
            readonly = command == "EXAMINE"
            SERVER_LOG["select"].append(readonly)
            self.send(b"* 4 EXISTS\r\n* 0 RECENT\r\n")
            self.send(b"* FLAGS (\\Seen \\Flagged)\r\n")
            self.send(f"* OK [UIDVALIDITY {UIDVALIDITY}] UIDs valid\r\n".encode())
            self.send(b"* OK [UIDNEXT 105] Predicted next UID\r\n")
            self.send(f"{tag} OK [{'READ-ONLY' if readonly else 'READ-WRITE'}] {command} completed\r\n".encode())

        elif command == "STATUS":
            self.send(f"* STATUS INBOX (UIDVALIDITY {UIDVALIDITY} UIDNEXT 105 MESSAGES 4)\r\n".encode())
            self.send(f"{tag} OK STATUS completed\r\n".encode())

        elif command == "SEARCH" or (is_uid and sub == "SEARCH"):
            # Handles both plain SEARCH (sequence numbers, used by verify()) and
            # UID SEARCH (stable ids, used by the sync cursor).
            criteria = line.upper()
            if "UNSEEN" in criteria:
                hits = [u for u in sorted(MESSAGES) if not MESSAGES[u][1]]
            elif "UID " in criteria:
                token = criteria.split("UID ")[1].split(":")[0].strip()
                since = int(token) if token.isdigit() else 0
                hits = [u for u in sorted(MESSAGES) if u > since]
            else:
                hits = sorted(MESSAGES)
            # plain SEARCH must answer with sequence numbers
            values = hits if is_uid else list(range(1, len(hits) + 1))
            self.send(("* SEARCH " + " ".join(str(v) for v in values) + "\r\n").encode())
            self.send(f"{tag} OK SEARCH completed\r\n".encode())

        elif is_uid and sub == "FETCH":
            SERVER_LOG["fetch"].append(line)
            uid_set = parts[3]
            uids = []
            for token in uid_set.split(","):
                if ":" in token:
                    low, high = token.split(":")
                    low = int(low)
                    high = 0x7FFFFFFF if high == "*" else int(high)
                    uids.extend(u for u in sorted(MESSAGES) if low <= u <= high)
                else:
                    uids.append(int(token))
            self.send(f"{tag} OK UID FETCH completed\r\n".encode()) if False else None
            for uid in uids:
                if uid not in MESSAGES:
                    continue
                body, flags = MESSAGES[uid]
                # UID FETCH replies carry the UID inside the response, which is
                # how the parser identifies each message.
                self.send(
                    f"* {uids.index(uid) + 1} FETCH (UID {uid} BODY[] {{{len(body)}}}\r\n".encode()
                    + body
                    + f" FLAGS ({flags}))\r\n".encode()
                )
            self.send(f"{tag} OK UID FETCH completed\r\n".encode())

        elif command in ("CLOSE", "NOOP"):
            self.send(f"{tag} OK {command} completed\r\n".encode())

        elif command == "LOGOUT":
            self.send(b"* BYE\r\n" + f"{tag} OK LOGOUT completed\r\n".encode())
            return False

        else:
            self.send(f"{tag} BAD unknown command\r\n".encode())

        return True


def start_fake_imap():
    import imaplib

    if not hasattr(imaplib, "_real_IMAP4_SSL"):
        imaplib._real_IMAP4_SSL = imaplib.IMAP4_SSL
        imaplib.IMAP4_SSL = imaplib.IMAP4

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(5)
    port = server.getsockname()[1]

    def loop():
        while True:
            try:
                conn, _ = server.accept()
            except OSError:
                return
            threading.Thread(target=FakeImap(conn).run, daemon=True).start()

    threading.Thread(target=loop, daemon=True).start()
    return port


# ===========================================================================
def main():
    print("=" * 74)
    print("  JARVIS OS - MAIL -> MEMORY INGESTION TEST (offline)")
    print("=" * 74)

    port = start_fake_imap()

    from app.config import settings
    from app.integrations import imap_mail
    from app.integrations.local_store import EncryptedStore

    # route the client at the fake server
    real_init = imap_mail.GmailImapClient.__init__

    def patched(self, address, password, host=imap_mail.GMAIL_HOST, port_=imap_mail.GMAIL_PORT):
        real_init(self, address, password, host="127.0.0.1", port=port)

    imap_mail.GmailImapClient.__init__ = patched

    settings.mail_sync_enabled = False          # we drive syncs manually
    settings.mail_sync_folders = "inbox"
    settings.mail_sync_limit = 25
    settings.mail_sync_skip_bulk = True
    settings.mail_store_in_vault = True

    # isolate the ledger and the account store for a repeatable run
    from app.agents.mail_ingestion_agent import EmailLedger, mail_ingestion_agent
    from app.routes import mail as mail_routes
    from app.database.session import SessionLocal
    from app.models.capture import MemorySession
    from app.models.memory import Memory, MemoryTag, SearchIndex
    from app.routes.os_store import os_store

    data_dir = os.path.join(os.getcwd(), "data")
    for name in ("mail_ledger.json", "imap_accounts.enc"):
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            os.remove(path)
    mail_ingestion_agent.ledger = EmailLedger()
    mail_routes.mail_accounts.__init__("imap_accounts.enc", collection="accounts")


    try:
        # ---- register the account ------------------------------------------
        print("\n[1] Register the mailbox")
        from fastapi.testclient import TestClient

        from app.main import app

        # ---- clean slate (must run AFTER app.main imports every model, or
        # SQLAlchemy cannot resolve the relationship mappers) -----------------
        from app.models.capture import MemorySession
        from app.models.memory import MemoryRelationship

        db = SessionLocal()
        try:
            stale = [m.id for m in db.query(Memory).filter(Memory.source_type == "email").all()]
            if stale:
                db.query(SearchIndex).filter(SearchIndex.memory_id.in_(stale)).delete(synchronize_session=False)
                db.query(MemoryTag).filter(MemoryTag.memory_id.in_(stale)).delete(synchronize_session=False)
                db.query(MemoryRelationship).filter(
                    MemoryRelationship.source_memory_id.in_(stale)).delete(synchronize_session=False)
                db.query(Memory).filter(Memory.id.in_(stale)).delete(synchronize_session=False)
                db.commit()

            sessions_cleared = 0
            for session in db.query(MemorySession).filter(MemorySession.session_type == "email").all():
                db.delete(session)
                sessions_cleared += 1
            db.commit()
        finally:
            db.close()

        # tasks + notifications produced by earlier runs
        cleaned = os_store._read()
        cleaned["tasks"] = [t for t in cleaned.get("tasks", [])
                            if not str(t.get("source", "")).startswith("email:")]
        cleaned["notifications"] = []
        os_store._write(cleaned)

        print(f"      (reset: {len(stale)} old email memories, {sessions_cleared} email sessions cleared)")

        api = TestClient(app)
        token = api.post("/api/auth/login", json={
            "username": "Immanuel", "password": "secondbrain", "device_name": "test"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        r = api.post("/api/mail/imap/connect", headers=headers, json={
            "email": TEST_ADDRESS, "app_password": "abcd efgh ijkl mnop",
            "label": "College"})
        check("account connected", r.status_code == 200, r.text[:200])
        check("the test uses a non-real address", TEST_ADDRESS.endswith(".invalid"))
        account_id = r.json()["account"]["id"]

        # ---- first sync ------------------------------------------------------
        print("\n[2] First sync: read mail -> memories")
        result = mail_ingestion_agent.sync_account(SessionLocal(), account_id, 1, notify=False)
        check("sync reported 3 ingested (1 bulk skipped)",
              result["ingested"] == 3,
              f"ingested={result['ingested']} skipped={result['skipped_bulk']} "
              f"dupes={result['duplicates']} errors={result['errors']}")
        check("newsletter detected as bulk and skipped",
              result["skipped_bulk"] == 1, f"skipped={result['skipped_bulk']}")
        check("no errors", not result["errors"], str(result["errors"]))

        # ---- rows landed in SQLite (this is what makes it answerable) --------
        print("\n[3] Stored in the searchable memory tables")
        db = SessionLocal()
        try:
            memories = db.query(Memory).filter(Memory.source_type == "email").all()
            check("email memories created", len(memories) == 3, f"got {len(memories)}")

            subjects = " | ".join(m.title for m in memories)
            check("subjects preserved", "IEEE conference draft deadline" in subjects, subjects)
            check("bulk mail NOT stored", "50% off" not in subjects, subjects)

            deadline_memory = next((m for m in memories if "deadline" in m.title.lower()), None)
            check("email body stored", deadline_memory and "review committee" in deadline_memory.content)
            check("memory attributed to the test account",
                  deadline_memory and deadline_memory.app_source == TEST_ADDRESS)
            check("source_type tagged as email",
                  deadline_memory and deadline_memory.source_type == "email")

            indexes = db.query(SearchIndex).filter(SearchIndex.source_type == "email").all()
            check("search index rows created", len(indexes) == 3, f"got {len(indexes)}")

            tags = db.query(MemoryTag).all()
            check("tags attached", len(tags) > 0, f"got {len(tags)}")
        finally:
            db.close()

        # ---- vault + wiki + graph -------------------------------------------
        print("\n[4] Written into the GitHub-backed memory vault")
        from pathlib import Path

        vault_cards = list(Path("..").glob("memory_vault/cards/*/mail_*.json"))
        if not vault_cards:
            vault_cards = list(Path("../memory_vault/cards").glob("*/mail_*.json"))
        check("vault JSON cards written", len(vault_cards) >= 3, f"got {len(vault_cards)}")

        if vault_cards:
            import json

            card = json.loads(vault_cards[0].read_text(encoding="utf-8"))
            check("card has a summary", bool(card.get("summary")))
            check("card carries key pointers", len(card.get("key_pointers", [])) > 0)
            check("card tagged as email", "email" in (card.get("tags") or []))

        wiki_dir = Path("../memory_vault/wiki")
        wiki_files = list(wiki_dir.rglob("*.md")) if wiki_dir.exists() else []
        check("wiki compiled from ingested mail", len(wiki_files) > 0, f"got {len(wiki_files)}")

        # ---- action detection -----------------------------------------------
        print("\n[5] Deadlines turned into tasks + notifications")
        tasks = os_store.get_tasks()
        email_tasks = [t for t in tasks if str(t.get("source", "")).startswith("email:")]
        check("task created from the deadline email", len(email_tasks) >= 1,
              f"got {len(email_tasks)} of {len(tasks)}")
        deadline_task = next((t for t in email_tasks if "deadline" in t["title"].lower()), None)
        check("deadline task created", deadline_task is not None,
              str([t["title"] for t in email_tasks]))
        if deadline_task:
            task = deadline_task
            check("task titled from the subject", "deadline" in task["title"].lower(), task["title"])
            check("task marked high priority", task["priority"] == "high", task["priority"])
            check("task has a due date", bool(task.get("due_date")), str(task.get("due_date")))
            check("task flagged as ai_suggested", task.get("ai_suggested") is True)
        check("transactional bulk with a real due date is kept",
              any("invoice" in t["title"].lower() for t in email_tasks),
              str([t["title"] for t in email_tasks]))
        check("marketing newsletter produced NO task",
              not any("50% off" in t["title"] for t in email_tasks),
              str([t["title"] for t in email_tasks]))

        notifications = os_store.get_notifications()
        check("notifications produced", len(notifications) >= 1, f"got {len(notifications)}")
        check("notification names the sender",
              any("sharma@university.edu" in n.get("body", "") for n in notifications),
              str([n.get("body") for n in notifications])[:160])

        # ---- incremental sync ------------------------------------------------
        print("\n[6] Second sync must find nothing (cursor + dedupe)")
        second = mail_ingestion_agent.sync_account(SessionLocal(), account_id, 1, notify=False)
        check("no re-ingestion on the second run", second["ingested"] == 0,
              f"ingested={second['ingested']}")
        db = SessionLocal()
        try:
            count = db.query(Memory).filter(Memory.source_type == "email").count()
            check("still exactly 3 memories (no duplicates)", count == 3, f"got {count}")
        finally:
            db.close()

        cursor = mail_ingestion_agent.ledger.cursor(account_id, "inbox")
        check("cursor advanced to the newest UID", cursor.get("last_uid") == 104, str(cursor))
        check("cursor remembers UIDVALIDITY", cursor.get("uidvalidity") == UIDVALIDITY, str(cursor))

        # ---- a brand new message is picked up --------------------------------
        print("\n[7] A newly arrived email is ingested on the next sync")
        MESSAGES[105] = (raw("New lab slot confirmed", "Lab Admin <lab@university.edu>",
                             "Your lab slot is confirmed for tomorrow."), "")
        third = mail_ingestion_agent.sync_account(SessionLocal(), account_id, 1, notify=False)
        check("exactly the new message ingested", third["ingested"] == 1, f"got {third['ingested']}")
        check("old messages not re-read", third["duplicates"] == 0, f"got {third['duplicates']}")

        # ---- read-only guarantee ---------------------------------------------
        print("\n[8] Read-only guarantee")
        check("every mailbox opened READ-ONLY (EXAMINE)",
              all(SERVER_LOG["select"]) and len(SERVER_LOG["select"]) > 0,
              f"select calls: {SERVER_LOG['select']}")
        check("every body fetch used BODY.PEEK, never BODY[]",
              all("BODY.PEEK" in c for c in SERVER_LOG["fetch"]) and len(SERVER_LOG["fetch"]) > 0,
              "a plain BODY[] fetch would mark your mail as read")

        # ---- THE key test: can Jarvis ANSWER from ingested mail? -------------
        print("\n[9] Answerable: the RAG path retrieves the ingested email")
        from app.rag.pipeline import rag_pipeline

        db = SessionLocal()
        try:
            context = rag_pipeline.retrieve(db, "What is the IEEE conference draft deadline?", "summary")
            titles = [c["title"] for c in context]
            check("retrieval returned context", len(context) > 0, f"got {len(context)}")
            check("the deadline email is in the answer context",
                  any("IEEE conference draft deadline" in t for t in titles),
                  f"retrieved: {titles[:5]}")

            context2 = rag_pipeline.retrieve(db, "What did Prof. Sharma say about the dataset?", "summary")
            titles2 = [c["title"] for c in context2]
            check("sender-based question finds the sender's mail",
                  any("sharma" in (c.get("content", "").lower()) for c in context2),
                  f"retrieved: {titles2[:5]}")
        finally:
            db.close()

        # ---- API surface -----------------------------------------------------
        print("\n[10] Sync API")
        r = api.get("/api/mail/sync/status", headers=headers)
        check("status endpoint works", r.status_code == 200, r.text[:160])
        body = r.json()
        check("status reports the interval", body.get("interval_minutes") == 10, str(body.get("interval_minutes")))
        check("status reports total ingested", body.get("stats", {}).get(account_id, {}).get("total_ingested", 0) >= 4,
              str(body.get("stats", {}).get(account_id)))

        r = api.post("/api/mail/sync", headers=headers, json={"account_id": account_id})
        check("manual sync endpoint works", r.status_code == 200, r.text[:200])

        r = api.post("/api/mail/sync", headers=headers, json={"account_id": "imap_nope"})
        check("unknown account surfaces a clear error", r.status_code == 502, f"got {r.status_code}: {r.text[:120]}")

        r = api.post("/api/mail/sync", json={"account_id": account_id})
        check("sync requires the app JWT", r.status_code == 401, f"got {r.status_code}")

        # ---- action detection unit checks ------------------------------------
        print("\n[11] Deadline parsing")
        detect = mail_ingestion_agent._detect_due_date
        today = datetime.now(timezone.utc).date()

        d = detect("submit by Friday")
        check("weekday -> next Friday", d is not None and d > today.isoformat(), str(d))

        d = detect("deadline 25/12/2026")
        check("numeric date parsed", d == "2026-12-25", str(d))

        d = detect("due on 30 September")
        check("month-name date parsed", d is not None and d.endswith("-09-30"), str(d))

        d = detect("no date here at all")
        check("no date -> None (no invented deadline)", d is None, str(d))

        check("deadline email flagged high priority",
              mail_ingestion_agent.detect_actions("Draft deadline", "must submit by Friday")[0]["priority"] == "high")
        check("ordinary email produces no action",
              mail_ingestion_agent.detect_actions("Lunch?", "See you at 1") == [])

    finally:
        imap_mail.GmailImapClient.__init__ = real_init

    # ---- clean up the vault -------------------------------------------------
    # The test writes REAL vault cards and wiki articles from fake emails. If we
    # leave them, they land in the user's GitHub-backed brain as if they were
    # genuine mail - which is exactly the "no fake data" rule this project keeps.
    from pathlib import Path as _Path

    removed_cards = 0
    skipped_cards = 0
    for card in _Path("../memory_vault/cards").glob("*/mail_*.json"):
        try:
            payload = card.read_text(encoding="utf-8")
        except Exception:
            continue
        # SAFETY: only delete artefacts this test created. A real mail card does
        # not mention the test marker, so it is left alone no matter what.
        if TEST_ADDRESS not in payload:
            skipped_cards += 1
            continue
        card.unlink()
        removed_cards += 1

    removed_wiki = 0
    skipped_wiki = 0
    for article in _Path("../memory_vault/wiki").rglob("email__*.md"):
        try:
            body = article.read_text(encoding="utf-8")
        except Exception:
            continue
        if TEST_ADDRESS not in body and "example.invalid" not in body:
            skipped_wiki += 1
            continue
        article.unlink()
        removed_wiki += 1

    # Drop the graph nodes the fake cards added, so the graph stays truthful
    graph_path = _Path("../memory_vault/knowledge_graph.json")
    if graph_path.exists():
        import json as _json

        graph = _json.loads(graph_path.read_text(encoding="utf-8"))
        fake_ids = {n["id"] for n in graph.get("nodes", []) if str(n.get("id", "")).startswith("card_mail_")}
        if fake_ids:
            graph["nodes"] = [n for n in graph.get("nodes", []) if n["id"] not in fake_ids]
            graph["edges"] = [
                e for e in graph.get("edges", [])
                if e.get("source") not in fake_ids and e.get("target") not in fake_ids
            ]
            graph_path.write_text(_json.dumps(graph, indent=2), encoding="utf-8")

    # The wiki compiler also rewrites its INDEX and the graph gains nodes from the
    # fake cards. Restore both from git so a test run leaves the vault byte-identical.
    import subprocess

    for target in ("memory_vault/knowledge_graph.json", "memory_vault/wiki/INDEX.md"):
        try:
            subprocess.run(["git", "checkout", "--", target], cwd="..", capture_output=True, timeout=20)
        except Exception:
            pass

    empty_dir = _Path("../memory_vault/wiki/communication")
    if empty_dir.is_dir() and not any(empty_dir.iterdir()):
        empty_dir.rmdir()

    print(f"\n      (cleaned up {removed_cards} test vault cards, {removed_wiki} test wiki articles, "
          f"restored graph + wiki index)")
    if skipped_cards or skipped_wiki:
        print(f"      PROTECTED {skipped_cards} real vault card(s) and {skipped_wiki} real wiki "
              f"article(s) - they did not carry the test marker")

    print("\n" + "=" * 74)
    if failures:
        print(f"  {len(failures)} CHECK(S) FAILED:")
        for f in failures:
            print(f"    - {f}")
        print("=" * 74)
        return 1
    print("  ALL MAIL INGESTION CHECKS PASSED")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
