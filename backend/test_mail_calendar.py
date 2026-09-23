"""
IMAP mail + iCal calendar regression test (offline).
===========================================================================
Runs a REAL IMAP conversation against a fake in-process IMAP server, and a real
HTTP fetch against a local ICS endpoint. No Google account, no network.

Proves:
  * IMAP login is verified before credentials are saved
  * credentials are ENCRYPTED at rest and never returned to the frontend
  * listing never marks mail as read (uses BODY.PEEK / readonly)
  * headers, bodies, unread flags and folder mapping work
  * provider dispatch: /api/mail/* routes the right way for both providers
  * the iCal parser handles folding, escaping, all-day events, timezones,
    weekly/monthly recurrence, EXDATE exclusions and RECURRENCE-ID overrides
  * a bad/revoked calendar URL gives a clear error, not a crash

Usage (backend folder, venv active):
    python test_mail_calendar.py
"""
import json
import os
import shutil
import socket
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS, FAIL = "[PASS]", "[FAIL]"
failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  --> {PASS} {label}")
    else:
        failures.append(label)
        print(f"  --> {FAIL} {label}   {detail}")


# ===========================================================================
# Fake IMAP server - speaks just enough IMAP4rev1 for imaplib
# ===========================================================================
RAW_MESSAGE_1 = (
    b"From: Prof. Sharma <sharma@university.edu>\r\n"
    b"To: vtu24334@veltech.edu.in\r\n"
    b"Subject: =?UTF-8?B?SUVFRSBkcmFmdCBkZWFkbGluZQ==?=\r\n"      # "IEEE draft deadline"
    b"Date: Tue, 22 Sep 2026 09:00:00 +0530\r\n"
    b"\r\n"
    b"Please submit your IEEE conference draft before Friday 5 PM.\r\n"
)

RAW_MESSAGE_2 = (
    b"From: AWS <no-reply@aws.amazon.com>\r\n"
    b"To: vtu24334@veltech.edu.in\r\n"
    b"Subject: Your AWS invoice\r\n"
    b"Date: Tue, 22 Sep 2026 10:00:00 +0530\r\n"
    b"\r\n"
    b"Your AWS invoice is ready.\r\n"
)

HEADERS_1 = b"From: Prof. Sharma <sharma@university.edu>\r\nTo: vtu24334@veltech.edu.in\r\nSubject: =?UTF-8?B?SUVFRSBkcmFmdCBkZWFkbGluZQ==?=\r\nDate: Tue, 22 Sep 2026 09:00:00 +0530\r\n\r\n"
HEADERS_2 = b"From: AWS <no-reply@aws.amazon.com>\r\nTo: vtu24334@veltech.edu.in\r\nSubject: Your AWS invoice\r\nDate: Tue, 22 Sep 2026 10:00:00 +0530\r\n\r\n"

SEEN_FLAGS_1 = b"\\Seen"          # message 1 already read
UNSEEN_FLAGS_2 = b""              # message 2 unread

# What the server records, so the test can assert on client behaviour
SERVER_LOG = {"fetch_commands": [], "selected_readonly": None}


class FakeImapHandler:
    def __init__(self, conn):
        self.conn = conn
        self.authed = False
        self.mailbox = None

    def send(self, data: bytes):
        self.conn.sendall(data)

    def run(self):
        self.send(b"* OK [CAPABILITY IMAP4rev1] Fake Gmail IMAP ready\r\n")
        buffer = b""
        while True:
            try:
                chunk = self.conn.recv(4096)
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

        if command == "CAPABILITY":
            self.send(b"* CAPABILITY IMAP4rev1\r\n" + f"{tag} OK CAPABILITY completed\r\n".encode())

        elif command == "LOGIN":
            SERVER_LOG["login"] = line
            self.authed = True
            self.send(f"{tag} OK LOGIN completed\r\n".encode())

        elif command == "LIST":
            self.send(b'* LIST (\\HasNoChildren) "/" "INBOX"\r\n')
            self.send(b'* LIST (\\HasNoChildren) "/" "[Gmail]/Sent Mail"\r\n')
            self.send(f"{tag} OK LIST completed\r\n".encode())

        elif command in ("SELECT", "EXAMINE"):
            # imaplib sends EXAMINE for select(readonly=True) and SELECT otherwise.
            # That distinction IS the read-only guarantee, so the test asserts on it.
            mailbox = line.split('"')[1] if '"' in line else parts[2]
            readonly = (command == "EXAMINE")
            SERVER_LOG["selected_readonly"] = readonly
            self.mailbox = mailbox
            self.send(b"* 2 EXISTS\r\n* 0 RECENT\r\n")
            self.send(b"* FLAGS (\\Seen \\Answered \\Flagged \\Deleted \\Draft)\r\n")
            self.send(b"* OK [UIDVALIDITY 1] UIDs valid\r\n")
            self.send(f"{tag} OK [{'READ-ONLY' if readonly else 'READ-WRITE'}] {command} completed\r\n".encode())

        elif command == "SEARCH":
            criteria = line.split(" ", 2)[2] if len(parts) > 2 else "ALL"
            if "UNSEEN" in criteria.upper():
                self.send(b"* SEARCH 2\r\n")
            elif "FLAGGED" in criteria.upper():
                self.send(b"* SEARCH 1\r\n")
            else:
                self.send(b"* SEARCH 1 2\r\n")
            self.send(f"{tag} OK SEARCH completed\r\n".encode())

        elif command == "FETCH":
            SERVER_LOG["fetch_commands"].append(line)
            # A real server replies once per message in the set, so "FETCH 2,1"
            # yields two full responses. Answering only the first is a common
            # way to build a fake server that silently hides bugs.
            for uid in [u.strip() for u in parts[2].split(",") if u.strip()]:
                if uid not in ("1", "2"):
                    self.send(f"{tag} NO no such message\r\n".encode())
                    continue
                headers = HEADERS_1 if uid == "1" else HEADERS_2
                body_snip = (b"Please submit your IEEE conference draft before" if uid == "1"
                             else b"Your AWS invoice is ready.")
                flags = SEEN_FLAGS_1 if uid == "1" else UNSEEN_FLAGS_2

            # IMAP literal framing: after the {n}\r\n header the server writes
            # exactly n raw bytes, and the REST of the response continues on the
            # SAME logical line. Adding an extra CRLF here desynchronises the
            # stream and imaplib aborts with "unexpected response".
                if "BODY.PEEK[]" in line:
                    raw = RAW_MESSAGE_1 if uid == "1" else RAW_MESSAGE_2
                    self.send(
                        f"* {uid} FETCH (BODY[] {{{len(raw)}}}\r\n".encode()
                        + raw
                        + f" FLAGS ({flags.decode()}))\r\n".encode()
                    )
                else:
                    self.send(
                        f"* {uid} FETCH (BODY[HEADER.FIELDS (FROM TO SUBJECT DATE)] {{{len(headers)}}}\r\n".encode()
                        + headers
                        + f" BODY[TEXT]<0> {{{len(body_snip)}}}\r\n".encode()
                        + body_snip
                        + f" FLAGS ({flags.decode()}))\r\n".encode()
                    )
            self.send(f"{tag} OK FETCH completed\r\n".encode())

        elif command in ("CLOSE", "LOGOUT", "NOOP"):
            if command == "LOGOUT":
                self.send(b"* BYE logging out\r\n")
            self.send(f"{tag} OK {command} completed\r\n".encode())
            if command == "LOGOUT":
                return False

        else:
            self.send(f"{tag} BAD unknown command\r\n".encode())

        return True


def start_fake_imap():
    """
    Start the fake server on a plain socket.

    Real Gmail always uses IMAPS on 993 and the client hardcodes IMAP4_SSL - we
    do NOT want to weaken that in production code. So for the test only, we
    alias IMAP4_SSL -> IMAP4, which keeps the entire real imaplib code path
    (login, select, search, fetch, literal parsing) under test.
    """
    import imaplib

    if not hasattr(imaplib, "_real_IMAP4_SSL"):
        imaplib._real_IMAP4_SSL = imaplib.IMAP4_SSL
        imaplib.IMAP4_SSL = imaplib.IMAP4

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(5)
    port = server.getsockname()[1]

    def accept_loop():
        while True:
            try:
                conn, _ = server.accept()
            except OSError:
                return
            threading.Thread(target=FakeImapHandler(conn).run, daemon=True).start()

    threading.Thread(target=accept_loop, daemon=True).start()
    return port


# ===========================================================================
# Fake ICS endpoint
# ===========================================================================
ICS_DOCUMENT = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Google Inc//Google Calendar 70.9054//EN
X-WR-CALNAME:Immanuel
X-WR-TIMEZONE:Asia/Kolkata
BEGIN:VEVENT
UID:single-1@google.com
DTSTART:20260923T043000Z
DTEND:20260923T053000Z
SUMMARY:AI Project Progress Review
LOCATION:Lab 3
DESCRIPTION:Agenda: model results\\, dataset status
ORGANIZER;CN=Sharma:mailto:sharma@university.edu
ATTENDEE;CN=Immanuel:mailto:vtu24334@veltech.edu.in
STATUS:CONFIRMED
END:VEVENT
BEGIN:VEVENT
UID:allday-1@google.com
DTSTART;VALUE=DATE:20260925
DTEND;VALUE=DATE:20260926
SUMMARY:College Holiday
END:VEVENT
BEGIN:VEVENT
UID:folded-1@google.com
DTSTART:20260924T010000Z
DTEND:20260924T020000Z
SUMMARY:A very long title that Google folded ac
 ross two physical lines
END:VEVENT
BEGIN:VEVENT
UID:weekly-1@google.com
DTSTART:20260921T003000Z
DTEND:20260921T010000Z
RRULE:FREQ=WEEKLY;BYDAY=MO,WE;COUNT=6
SUMMARY:Standup (recurring)
END:VEVENT
BEGIN:VEVENT
UID:daily-1@google.com
DTSTART:20260921T120000Z
DTEND:20260921T123000Z
RRULE:FREQ=DAILY;INTERVAL=2;COUNT=5
SUMMARY:Every other day task
EXDATE:20260923T120000Z
END:VEVENT
BEGIN:VEVENT
UID:weekly-1@google.com
RECURRENCE-ID:20260923T003000Z
DTSTART:20260923T053000Z
DTEND:20260923T060000Z
SUMMARY:Standup MOVED to 11:00
END:VEVENT
END:VCALENDAR
"""


class IcsHandler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/good"):
            body = ICS_DOCUMENT.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/calendar; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/html"):
            body = b"<html><body>Not a calendar</body></html>"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


# ===========================================================================
def main():
    """Wrap the scenario so the real credential directory is always verified."""
    from _harness import activate, describe_real_credentials, verify_and_restore

    print(f"\n[0] Real credentials on disk: {describe_real_credentials()}")
    print("    (protected: this suite runs against a private harness directory)")
    activate("mail_calendar")
    try:
        return _scenario()
    finally:
        verify_and_restore()


def _scenario():
    print("=" * 74)
    print("  JARVIS OS - IMAP MAIL + ICAL CALENDAR TEST (offline)")
    print("=" * 74)

    imap_port = start_fake_imap()

    ics_server = ThreadingHTTPServer(("127.0.0.1", 0), IcsHandler)
    ics_port = ics_server.server_address[1]
    threading.Thread(target=ics_server.serve_forever, daemon=True).start()

    from app.integrations.imap_mail import ImapError, GmailImapClient
    from app.integrations.ical_calendar import parse_ics, fetch_feed

    # ---- 1. raw IMAP client against the fake server ----------------------
    print("\n[1] IMAP client end-to-end against a fake IMAP server")
    client = GmailImapClient("vtu24334@veltech.edu.in", "abcd efgh ijkl mnop",
                             host="127.0.0.1", port=imap_port)
    try:
        verified = client.verify()
        check("login + INBOX verified", verified["ok"] is True, str(verified))
        check("total message count read", verified["total_messages"] == 2, str(verified.get("total_messages")))
        check("unread count read from UNSEEN search", verified["unread"] == 1, str(verified.get("unread")))
    except Exception as exc:
        check("IMAP verify works", False, f"{type(exc).__name__}: {exc}")

    check("mailbox opened READ-ONLY", SERVER_LOG.get("selected_readonly") is True,
          f"got {SERVER_LOG.get('selected_readonly')}")

    folders = client.list_folders()
    check("folder list parsed", any(f["label"] == "Inbox" for f in folders), str(folders))
    check("Gmail folders de-prefixed",
          all(not f["label"].startswith("[Gmail]/") for f in folders), str(folders))

    messages = client.list_messages("inbox", limit=10)
    check("two messages listed", len(messages) == 2, f"got {len(messages)}")
    first = next((m for m in messages if m["id"] == "1"), None)
    check("sender parsed", first and "sharma@university.edu" in first["from"])
    check("MIME-encoded subject decoded",
          first and first["subject"] == "IEEE draft deadline", first and first["subject"])
    check("snippet extracted and cleaned",
          first and "IEEE conference draft" in first["snippet"], first and first["snippet"])
    check("read message flagged as not unread", first and first["unread"] is False)
    second = next((m for m in messages if m["id"] == "2"), None)
    check("unread message flagged unread", second and second["unread"] is True)

    check("listing used BODY.PEEK, never BODY[]",
          all("BODY.PEEK" in c for c in SERVER_LOG["fetch_commands"] if "FETCH" in c),
          "a plain BODY[] fetch would mark mail as read!")

    detail = client.get_message("2", "inbox")
    check("full message loads", "AWS invoice is ready" in detail["body"], detail.get("body", "")[:60])

    # ---- 2. bad credentials give a clear error ---------------------------
    print("\n[2] credential failures explain themselves")
    empty = GmailImapClient("", "")
    try:
        empty.verify()
        check("empty credentials rejected", False)
    except ImapError as exc:
        check("empty credentials rejected with a message", "required" in str(exc).lower(), str(exc))

    # ---- 3. search translation ------------------------------------------
    print("\n[3] search syntax translation")
    check("from: -> IMAP FROM", GmailImapClient._build_search("from:sharma") == 'FROM "sharma"')
    check("subject: -> IMAP SUBJECT", GmailImapClient._build_search("subject:invoice") == 'SUBJECT "invoice"')
    check("is:unread -> UNSEEN", GmailImapClient._build_search("is:unread") == "UNSEEN")
    check("plain text -> TEXT", GmailImapClient._build_search("aqi dataset") == 'TEXT "aqi dataset"')
    check("embedded quotes neutralised (only the 2 delimiters remain)",
          GmailImapClient._build_search('weird"query').count('"') == 2,
          GmailImapClient._build_search('weird"query'))

    # ---- 4. ICS parsing ---------------------------------------------------
    print("\n[4] iCal parsing (folding, escaping, all-day, recurrence)")
    events = parse_ics(ICS_DOCUMENT)
    # The override carries a RECURRENCE-ID so it is folded into its parent series,
    # leaving 5 standalone VEVENTs (that is correct ICS behaviour, not a loss).
    check("5 base VEVENTs parsed", len(events) == 5, f"got {len(events)}")
    weekly = next(e for e in events if e.get("uid") == "weekly-1@google.com")
    check("RECURRENCE-ID override attached to its series",
          len(weekly.get("overrides") or []) == 1, str(len(weekly.get("overrides") or [])))

    single = next(e for e in events if e.get("uid") == "single-1@google.com")
    check("SUMMARY parsed", single["summary"] == "AI Project Progress Review")
    check("LOCATION parsed", single["location"] == "Lab 3")
    check("escaped comma unescaped", "results, dataset" in single["description"], single["description"])
    check("organizer mailto stripped", single["organizer"] == "sharma@university.edu")
    check("attendee parsed", "vtu24334@veltech.edu.in" in single["attendees"])

    folded = next(e for e in events if e.get("uid") == "folded-1@google.com")
    check("folded line rejoined", folded["summary"].endswith("across two physical lines"), folded["summary"])

    allday = next(e for e in events if e.get("uid") == "allday-1@google.com")
    check("all-day event detected", allday["all_day"] is True)

    # ---- 5. expansion through the window ---------------------------------
    print("\n[5] window expansion + recurrence + EXDATE + override")
    result = fetch_feed(f"http://127.0.0.1:{ics_port}/good", days_ahead=15, days_back=30, limit=500)
    expanded = result["events"]
    summaries = [e["summary"] for e in expanded]

    check("events returned", len(expanded) > 0, str(len(expanded)))
    check("single event in range", "AI Project Progress Review" in summaries)
    check("all-day event in range", "College Holiday" in summaries)
    check("weekly recurrence expanded (>=4 standups)",
          sum(1 for s in summaries if s.startswith("Standup")) >= 4,
          f"got {sum(1 for s in summaries if s.startswith('Standup'))}")
    check("RECURRENCE-ID override applied",
          "Standup MOVED to 11:00" in summaries)
    check("EXDATE removed the excluded occurrence",
          not any(e["start"].startswith("2026-09-23T12:00") for e in expanded),
          "the EXDATE'd 23 Sep occurrence is still present")
    check("remaining daily occurrences kept",
          sum(1 for s in summaries if s == "Every other day task") >= 3,
          f"got {sum(1 for s in summaries if s == 'Every other day task')}")
    check("events sorted by start",
          [e["start"] for e in expanded] == sorted(e["start"] for e in expanded))
    check("every event has an id and summary",
          all(e.get("id") and e.get("summary") for e in expanded))

    # ---- 6. bad feeds ------------------------------------------------------
    print("\n[6] bad calendar URLs give clear errors")
    try:
        fetch_feed(f"http://127.0.0.1:{ics_port}/missing")
        check("404 raises a helpful error", False)
    except Exception as exc:
        check("404 raises a helpful error", "404" in str(exc) or "reset" in str(exc), str(exc)[:90])

    try:
        fetch_feed(f"http://127.0.0.1:{ics_port}/html")
        check("HTML page rejected", False)
    except Exception as exc:
        check("HTML page rejected with guidance", "not a calendar" in str(exc), str(exc)[:90])

    try:
        fetch_feed("not-a-url")
        check("non-URL rejected", False)
    except Exception as exc:
        check("non-URL rejected", "calendar URL" in str(exc), str(exc)[:90])

    # ---- 7. API routes, provider dispatch, encryption ---------------------
    print("\n[7] API routes + credential encryption")
    from fastapi.testclient import TestClient
    from app.main import app
    from app.integrations import imap_mail as imap_module

    # point the client at the fake server without touching the route code
    real_init = imap_module.GmailImapClient.__init__

    def patched_init(self, address, app_password, host=imap_module.GMAIL_HOST, port=imap_module.GMAIL_PORT):
        real_init(self, address, app_password, host="127.0.0.1", port=imap_port)

    imap_module.GmailImapClient.__init__ = patched_init
    try:
        api = TestClient(app)
        token = api.post("/api/auth/login", json={
            "username": "Immanuel", "password": "secondbrain", "device_name": "test"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Credentials live in the private harness directory for this run. This
        # block used to DELETE the user's real imap_accounts.enc and
        # calendar_feeds.enc by name, which is why connected mailboxes kept
        # disappearing after a verification run.
        from _harness import active_dir
        store_dir = str(active_dir())

        r = api.post("/api/mail/imap/connect", headers=headers, json={
            "email": "vtu24334@veltech.edu.in",
            "app_password": "abcd efgh ijkl mnop",
            "label": "College"})
        check("connect returns 200", r.status_code == 200, r.text[:200])
        body = r.json()
        check("credentials verified before saving", body.get("verified", {}).get("ok") is True)
        account_id = body["account"]["id"]
        check("account id namespaced for dispatch", account_id.startswith("imap_"))
        check("app_password NOT returned to frontend",
              "app_password" not in r.text, "SECRET LEAK")

        enc_path = os.path.join(store_dir, "imap_accounts.enc")
        blob = open(enc_path, "rb").read()
        check("app password is NOT readable on disk",
              b"abcd efgh ijkl mnop" not in blob, "PLAINTEXT LEAK")
        check("stored under backend/data (git-ignored)",
              "memory_vault" not in os.path.abspath(enc_path).lower())

        r = api.get("/api/mail/accounts", headers=headers)
        check("account listed", len(r.json()) == 1, json.dumps(r.json())[:160])
        check("provider reported as imap", r.json()[0]["provider"] == "imap")

        r = api.get(f"/api/mail/messages?account_id={account_id}&limit=10", headers=headers)
        check("messages route works", r.status_code == 200 and r.json()["count"] == 2, r.text[:160])
        check("provider echoed", r.json()["provider"] == "imap")

        r = api.get(f"/api/mail/messages?account_id={account_id}&folder=unread", headers=headers)
        check("unread folder filters", r.json()["count"] == 1, r.text[:160])

        r = api.get(f"/api/mail/message/2?account_id={account_id}", headers=headers)
        check("message detail route works", r.status_code == 200 and "AWS invoice" in r.json()["body"], r.text[:160])

        r = api.get("/api/mail/messages?account_id=imap_missing")
        check("unauthenticated mail route -> 401", r.status_code == 401)

        r = api.get("/api/mail/messages?account_id=imap_missing", headers=headers)
        check("unknown imap account -> 404", r.status_code == 404, f"got {r.status_code}")
        r = api.get("/api/calendar/source-events?source_id=1", headers=headers)
        check("unknown calendar source -> 404", r.status_code == 404,
              f"got {r.status_code}: {r.text[:100]}")

        # calendar feed
        r = api.post("/api/calendar/feed", headers=headers, json={
            "url": f"http://127.0.0.1:{ics_port}/good", "label": "College Calendar"})
        check("calendar feed added", r.status_code == 200, r.text[:200])
        feed_id = r.json()["source"]["id"]
        check("preview events returned on connect", len(r.json().get("preview_events", [])) > 0)
        check("secret URL NOT returned in full",
              "url_hint" in r.json()["source"] and str(ics_port) not in r.json()["source"].get("url_hint", ""),
              str(r.json()["source"].get("url_hint"))[:60])

        r = api.get("/api/calendar/sources", headers=headers)
        check("calendar source listed", len(r.json()) == 1 and r.json()[0]["provider"] == "ical", r.text[:160])

        r = api.get(f"/api/calendar/source-events?source_id={feed_id}&days_ahead=15&days_back=30", headers=headers)
        check("source-events works", r.status_code == 200 and r.json()["count"] > 0, r.text[:160])

        r = api.delete(f"/api/mail/accounts/{account_id}", headers=headers)
        check("disconnect works", r.status_code == 200, r.text[:160])
        r = api.get("/api/mail/accounts", headers=headers)
        check("account removed", len(r.json()) == 0, r.text[:160])

        r = api.delete(f"/api/calendar/feed/{feed_id}", headers=headers)
        check("calendar feed removed", r.status_code == 200, r.text[:160])
    finally:
        imap_module.GmailImapClient.__init__ = real_init

    ics_server.shutdown()

    print("\n" + "=" * 74)
    if failures:
        print(f"  {len(failures)} CHECK(S) FAILED:")
        for f in failures:
            print(f"    - {f}")
        print("=" * 74)
        return 1
    print("  ALL IMAP MAIL + ICAL CALENDAR CHECKS PASSED")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
