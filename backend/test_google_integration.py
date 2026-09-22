"""
Google integration regression test (offline - uses a fake Google server).
===========================================================================
Proves the whole real flow works without touching Google:

  1. /api/google/connect returns a correct consent URL
  2. /api/google/callback exchanges the code and stores the account
  3. tokens on disk are ENCRYPTED (the refresh token must not be readable)
  4. tokens live OUTSIDE memory_vault (the public GitHub sync path)
  5. /api/google/accounts lists the account WITHOUT leaking secrets
  6. Gmail list + message reads work through the refresh-token flow
  7. Calendar events work
  8. disconnect revokes and removes
  9. an expired/rotated refresh token surfaces a clear error, not a crash

Usage (backend folder, venv active):
    python test_google_integration.py
"""
import json
import os
import shutil
import sys
import threading
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
# Fake Google server
# ===========================================================================
FAKE_REFRESH_TOKEN = "1//FAKE_REFRESH_TOKEN_DO_NOT_LEAK"
FAKE_ACCESS_TOKEN = "ya29.FAKE_ACCESS_TOKEN"

MESSAGES = {
    "m1": {
        "id": "m1", "threadId": "t1",
        "snippet": "Please submit your IEEE conference draft before Friday 5 PM.",
        "labelIds": ["INBOX", "UNREAD", "IMPORTANT"], "internalDate": "1758000000000",
        "payload": {
            "mimeType": "multipart/alternative",
            "headers": [
                {"name": "From", "value": "Prof. Sharma <sharma@university.edu>"},
                {"name": "To", "value": "vtu24334@veltech.edu.in"},
                {"name": "Subject", "value": "IEEE draft deadline"},
                {"name": "Date", "value": "Tue, 22 Sep 2026 09:00:00 +0530"},
            ],
            "parts": [
                {"mimeType": "text/plain", "body": {"data": "UGxlYXNlIHN1Ym1pdCB5b3VyIGRyYWZ0Lg=="}},
            ],
        },
    },
    "m2": {
        "id": "m2", "threadId": "t2", "snippet": "AWS bill is ready.",
        "labelIds": ["INBOX"], "internalDate": "1758000100000",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": "AWS <no-reply@aws.amazon.com>"},
                {"name": "Subject", "value": "Your AWS invoice"},
                {"name": "Date", "value": "Tue, 22 Sep 2026 10:00:00 +0530"},
            ],
            "body": {"data": "WW91ciBBV1MgaW52b2ljZSBpcyByZWFkeS4="},
        },
    },
}


class FakeGoogle(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        form = self.rfile.read(length).decode()
        if self.path.startswith("/token"):
            if "grant_type=authorization_code" in form:
                return self._json({
                    "access_token": FAKE_ACCESS_TOKEN,
                    "refresh_token": FAKE_REFRESH_TOKEN,
                    "expires_in": 3600,
                    "scope": ("openid https://www.googleapis.com/auth/userinfo.email "
                              "https://www.googleapis.com/auth/userinfo.profile "
                              "https://www.googleapis.com/auth/gmail.readonly "
                              "https://www.googleapis.com/auth/calendar.readonly"),
                    "token_type": "Bearer",
                })
            if "grant_type=refresh_token" in form:
                if "REVOKED" in form:
                    return self._json({"error": "invalid_grant",
                                       "error_description": "Token has been expired or revoked."}, 400)
                return self._json({"access_token": FAKE_ACCESS_TOKEN, "expires_in": 3600,
                                   "token_type": "Bearer"})
        if self.path.startswith("/revoke"):
            return self._json({})
        return self._json({"error": "not_found"}, 404)

    def do_GET(self):
        if self.path.startswith("/v1/userinfo"):
            return self._json({"email": "vtu24334@veltech.edu.in", "name": "Immanuel L",
                               "picture": "https://example.com/p.png"})
        if "/gmail/v1/users/me/profile" in self.path:
            return self._json({"emailAddress": "vtu24334@veltech.edu.in",
                               "messagesTotal": len(MESSAGES)})
        if "/gmail/v1/users/me/messages/" in self.path:
            mid = self.path.split("/messages/")[1].split("?")[0]
            if mid in MESSAGES:
                return self._json(MESSAGES[mid])
            return self._json({"error": {"message": "Not Found"}}, 404)
        if "/gmail/v1/users/me/messages" in self.path:
            return self._json({"messages": [{"id": k} for k in MESSAGES],
                               "resultSizeEstimate": len(MESSAGES)})
        if "/calendar/v3/users/me/calendarList" in self.path:
            return self._json({"items": [
                {"id": "primary", "summary": "Immanuel", "primary": True, "accessRole": "owner"},
                {"id": "college@veltech.edu.in", "summary": "College", "accessRole": "reader"},
            ]})
        if "/calendar/v3/calendars/" in self.path and "/events" in self.path:
            return self._json({"items": [
                {"id": "e1", "summary": "AI Project Progress Review",
                 "start": {"dateTime": "2026-09-23T10:00:00+05:30"},
                 "end": {"dateTime": "2026-09-23T11:00:00+05:30"},
                 "location": "Lab 3", "organizer": {"email": "sharma@university.edu"},
                 "attendees": [{"email": "vtu24334@veltech.edu.in"}],
                 "htmlLink": "https://calendar.google.com/event?eid=e1", "status": "confirmed"},
                {"id": "e2", "summary": "Holiday", "start": {"date": "2026-09-25"},
                 "end": {"date": "2026-09-26"}, "status": "confirmed"},
            ]})
        return self._json({"error": "not_found"}, 404)


def main():
    print("=" * 74)
    print("  JARVIS OS - GOOGLE INTEGRATION TEST (offline, fake Google server)")
    print("=" * 74)

    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeGoogle)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    # ---- point the integration at the fake server -------------------------
    from app.config import settings
    from app.integrations import google_oauth

    settings.google_client_id = "fake-client-id.apps.googleusercontent.com"
    settings.google_client_secret = "fake-client-secret"
    settings.google_redirect_uri = "http://127.0.0.1:8000/api/google/callback"

    google_oauth.AUTH_ENDPOINT = f"{base}/o/oauth2/v2/auth"
    google_oauth.TOKEN_ENDPOINT = f"{base}/token"
    google_oauth.REVOKE_ENDPOINT = f"{base}/revoke"
    google_oauth.USERINFO_ENDPOINT = f"{base}/v1/userinfo"
    google_oauth.GMAIL_API = f"{base}/gmail/v1/users/me"
    google_oauth.CALENDAR_API = f"{base}/calendar/v3"

    # ---- fresh token store so the test is repeatable ----------------------
    from app.integrations.token_store import google_token_store

    store_dir = os.path.join(os.getcwd(), "data", "integrations")
    if os.path.isdir(store_dir):
        shutil.rmtree(store_dir, ignore_errors=True)
    google_token_store.__init__(directory=os.path.join("./data/integrations"))

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    # ---- 1. status before connecting --------------------------------------
    print("\n[1] /api/google/status before connecting")
    token = client.post("/api/auth/login", json={
        "username": "Immanuel", "password": "secondbrain", "device_name": "test"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/google/status", headers=headers)
    check("status returns 200", r.status_code == 200, r.text[:160])
    check("reports configured=true", r.json()["configured"] is True)
    check("no accounts yet", r.json()["account_count"] == 0)

    # ---- 2. connect returns a consent URL ---------------------------------
    print("\n[2] POST /api/google/connect")
    r = client.post("/api/google/connect", headers=headers,
                    json={"email": "vtu24334@veltech.edu.in", "services": ["gmail", "calendar"]})
    check("connect returns 200", r.status_code == 200, r.text[:200])
    auth_url = r.json()["auth_url"]
    state = r.json()["state"]

    check("auth_url points at Google", auth_url.startswith(f"{base}/o/oauth2/v2/auth?"))
    check("requests offline access (refresh token)", "access_type=offline" in auth_url)
    check("forces consent so a refresh token is returned", "prompt=consent" in auth_url)
    check("requests gmail.readonly", "gmail.readonly" in auth_url)
    check("requests calendar.readonly", "calendar.readonly" in auth_url)
    check("does NOT request write/send scopes",
          "gmail.send" not in auth_url and "gmail.modify" not in auth_url
          and "calendar.events" not in auth_url)
    check("carries our state token", f"state={state}" in auth_url)
    check("hints the email", "login_hint=vtu24334" in auth_url)

    # ---- 3. callback stores the account -----------------------------------
    print("\n[3] GET /api/google/callback (simulating Google's redirect)")
    r = client.get(f"/api/google/callback?code=FAKE_AUTH_CODE&state={state}")
    check("callback returns 200", r.status_code == 200)
    check("callback shows success page", "Connected Successfully" in r.text)
    check("callback names the account", "vtu24334@veltech.edu.in" in r.text)

    # ---- 4. tokens are encrypted on disk ----------------------------------
    print("\n[4] token storage safety")
    enc_path = os.path.join(store_dir, "google_accounts.enc")
    check("token file written", os.path.exists(enc_path))
    blob = open(enc_path, "rb").read()
    check("refresh token is NOT readable in the file",
          FAKE_REFRESH_TOKEN.encode() not in blob,
          "PLAINTEXT LEAK - encryption not working!")
    check("access token is NOT readable in the file", FAKE_ACCESS_TOKEN.encode() not in blob)
    check("stored under backend/data (git-ignored)",
          "memory_vault" not in os.path.abspath(enc_path).lower())

    # ---- 5. accounts list is secret-free ----------------------------------
    print("\n[5] GET /api/google/accounts")
    r = client.get("/api/google/accounts", headers=headers)
    accounts = r.json()
    check("one account listed", len(accounts) == 1, json.dumps(accounts)[:200])
    check("email correct", accounts[0]["email"] == "vtu24334@veltech.edu.in")
    check("name captured", accounts[0]["name"] == "Immanuel L")
    check("scopes captured", any("gmail" in s for s in accounts[0]["scopes"]))
    check("refresh_token NOT exposed to the frontend",
          "refresh_token" not in json.dumps(accounts))

    account_id = accounts[0]["id"]

    # ---- 6. Gmail -------------------------------------------------------
    print("\n[6] Gmail reads")
    r = client.get(f"/api/google/gmail/messages?account_id={account_id}&limit=10", headers=headers)
    check("messages returns 200", r.status_code == 200, r.text[:200])
    body = r.json()
    check("both messages returned", body["count"] == 2, str(body.get("count")))
    first = next((m for m in body["messages"] if m["id"] == "m1"), None)
    check("sender parsed", first and "sharma@university.edu" in first["from"])
    check("subject parsed", first and first["subject"] == "IEEE draft deadline")
    check("unread flag detected", first and first["unread"] is True)
    check("important flag detected", first and first["important"] is True)

    r = client.get(f"/api/google/gmail/message/m1?account_id={account_id}", headers=headers)
    check("full message returns 200", r.status_code == 200, r.text[:200])
    check("body decoded from base64", "submit your draft" in r.json().get("body", "").lower())

    # ---- 7. Calendar ----------------------------------------------------
    print("\n[7] Calendar reads")
    r = client.get(f"/api/google/calendar/events?account_id={account_id}&days_ahead=7", headers=headers)
    check("events returns 200", r.status_code == 200, r.text[:200])
    events = r.json()["events"]
    check("two events returned", len(events) == 2, str(len(events)))
    check("timed event start parsed", events[0]["start"].startswith("2026-09-23T10:00"))
    check("attendees parsed", "vtu24334@veltech.edu.in" in (events[0]["attendees"] or []))
    check("all-day event flagged", events[1]["all_day"] is True)

    r = client.get(f"/api/google/calendar/calendars?account_id={account_id}", headers=headers)
    check("calendar list returns 2", len(r.json()) == 2, r.text[:200])

    # ---- 8. token refresh path ------------------------------------------
    print("\n[8] access-token refresh")
    google_oauth._access_tokens.clear()          # force a real refresh call
    r = client.get(f"/api/google/gmail/profile?account_id={account_id}", headers=headers)
    check("refresh flow works after cache clear", r.status_code == 200, r.text[:200])
    check("profile email correct", r.json().get("emailAddress") == "vtu24334@veltech.edu.in")

    # ---- 9. revoked token gives a clear error, not a crash ---------------
    print("\n[9] revoked / invalid refresh token")
    from app.integrations.token_store import google_token_store as store
    store.update_account(account_id, {"refresh_token": "REVOKED_TOKEN"})
    google_oauth._access_tokens.clear()
    r = client.get(f"/api/google/gmail/messages?account_id={account_id}", headers=headers)
    check("a REVOKED upstream token -> 502 (genuine upstream failure, not 500)",
          r.status_code == 502, f"got {r.status_code}")
    check("the two failure kinds are distinguishable: 404 vs 502",
          r.status_code != 404, "a bad credential must not look like a missing account")
    check("explains invalid_grant and the 7-day testing rule",
          "invalid_grant" in r.text and "Testing" in r.text, r.text[:200])
    store.update_account(account_id, {"refresh_token": FAKE_REFRESH_TOKEN})  # restore

    # ---- 10. unknown account -------------------------------------------
    print("\n[10] unknown account")
    r = client.get("/api/google/gmail/messages?account_id=gacct_missing", headers=headers)
    check("unknown account -> 404 (a client mistake, not an upstream failure)",
          r.status_code == 404, f"got {r.status_code}: {r.text[:120]}")
    check("and it does NOT masquerade as a gateway error", r.status_code != 502,
          "502 would send the user hunting for a Google problem that does not exist")

    # ---- 11. auth is required on data routes ----------------------------
    print("\n[11] routes require the app JWT")
    for path in ["/api/google/accounts", f"/api/google/gmail/messages?account_id={account_id}"]:
        r = client.get(path)
        check(f"unauthenticated {path.split('?')[0]} -> 401", r.status_code == 401, f"got {r.status_code}")

    # ---- 12. disconnect -------------------------------------------------
    print("\n[12] DELETE /api/google/accounts/{id}")
    r = client.delete(f"/api/google/accounts/{account_id}", headers=headers)
    check("disconnect returns 200", r.status_code == 200, r.text[:160])
    r = client.get("/api/google/accounts", headers=headers)
    check("account removed", len(r.json()) == 0, json.dumps(r.json())[:160])

    server.shutdown()

    print("\n" + "=" * 74)
    if failures:
        print(f"  {len(failures)} CHECK(S) FAILED:")
        for f in failures:
            print(f"    - {f}")
        print("=" * 74)
        return 1
    print("  ALL GOOGLE INTEGRATION CHECKS PASSED")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
