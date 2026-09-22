"""
Google OAuth 2.0 + Gmail / Calendar client.
===========================================================================
Deliberately built on `httpx` (already a core dependency) rather than the heavy
`google-api-python-client` stack, so there is nothing new to install.

Flow
----
  1. build_auth_url()      -> a Google consent URL the user opens in a browser
  2. exchange_code()       -> trades the ?code= for tokens (once)
  3. refresh_access_token()-> trades the stored refresh_token for an access
                              token, cached in memory until it expires
  4. gmail_* / calendar_*  -> the actual data reads

The refresh token is the long-lived credential; it only comes back when the
user grants consent with prompt=consent & access_type=offline, which is why
build_auth_url always sends both.
"""
from __future__ import annotations

import secrets
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.integrations.token_store import google_token_store

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"
USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"

GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
CALENDAR_API = "https://www.googleapis.com/calendar/v3"

# Read-only by default: a personal knowledge system needs to READ your inbox and
# calendar. Nothing here can send mail, delete anything, or modify an event.
DEFAULT_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]

# In-flight consent attempts, keyed by the `state` value we send to Google.
# Short lived; only exists to tie the callback back to the account the user
# clicked "Connect" on.
_pending_states: Dict[str, Dict[str, Any]] = {}
_STATE_TTL_SECONDS = 900

# access_token cache: account_id -> (token, expires_at_epoch)
_access_tokens: Dict[str, tuple] = {}


class GoogleNotConfigured(RuntimeError):
    pass


class GoogleAuthError(RuntimeError):
    """Something went wrong talking to Google (bad token, network, 5xx)."""


class AccountNotFound(GoogleAuthError):
    """
    The requested account id is not in the token store.

    This is a CLIENT error, not an upstream failure: the caller asked for an
    account that does not exist (or was disconnected). It must map to 404, not
    502 - 502 means "the service in front of us misbehaved", which would send
    the user hunting for a Google problem that is not there.
    """


# --------------------------------------------------------------------- helpers
def _require_config() -> None:
    if not settings.google_configured:
        raise GoogleNotConfigured(
            "Google is not configured yet. Add GOOGLE_CLIENT_ID and "
            "GOOGLE_CLIENT_SECRET to backend/.env (see GOOGLE_SETUP.md)."
        )


def _purge_expired_states() -> None:
    now = time.time()
    for state in [s for s, v in _pending_states.items() if v.get("created", 0) + _STATE_TTL_SECONDS < now]:
        _pending_states.pop(state, None)


# ---------------------------------------------------------------- auth url
def build_auth_url(hint_email: str = "", services: Optional[List[str]] = None) -> Dict[str, str]:
    """Return {auth_url, state} for the user to open in a browser."""
    _require_config()
    _purge_expired_states()

    scope_list = list(DEFAULT_SCOPES)
    if services and "gmail" not in services:
        scope_list = [s for s in scope_list if "gmail" not in s]
    if services and "calendar" not in services:
        scope_list = [s for s in scope_list if "calendar" not in s]

    state = secrets.token_urlsafe(32)
    _pending_states[state] = {
        "hint_email": (hint_email or "").strip().lower(),
        "services": services or ["gmail", "calendar"],
        "created": time.time(),
    }

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(scope_list),
        # access_type=offline  -> we receive a refresh token
        # prompt=consent       -> we receive it EVERY time, not only the first
        "access_type": "offline",
        "prompt": "consent",
        # include_granted_scopes keeps previously granted scopes when re-consenting
        "include_granted_scopes": "true",
        "state": state,
        "login_hint": _pending_states[state]["hint_email"],
    }
    if not params["login_hint"]:
        params.pop("login_hint")

    return {"auth_url": f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}", "state": state}


def consume_state(state: str) -> Dict[str, Any]:
    _purge_expired_states()
    return _pending_states.pop(state, {}) or {}


# ------------------------------------------------------------ code exchange
async def exchange_code(code: str) -> Dict[str, Any]:
    """Trade the one-time ?code= for tokens. Returns the raw token payload."""
    _require_config()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            TOKEN_ENDPOINT,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if resp.status_code != 200:
        raise GoogleAuthError(f"Token exchange failed ({resp.status_code}): {resp.text[:300]}")
    return resp.json()


async def fetch_userinfo(access_token: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(USERINFO_ENDPOINT, headers={"Authorization": f"Bearer {access_token}"})
    if resp.status_code != 200:
        raise GoogleAuthError(f"Could not read Google profile ({resp.status_code})")
    return resp.json()


async def refresh_access_token(account_id: str) -> str:
    """Return a valid access token for a stored account, refreshing if needed."""
    _require_config()

    cached = _access_tokens.get(account_id)
    if cached and cached[1] > time.time() + 60:
        return cached[0]

    record = google_token_store.get_secret(account_id)
    if not record:
        raise AccountNotFound("Account not found - it may have been disconnected.")

    refresh_token = record.get("refresh_token")
    if not refresh_token:
        raise GoogleAuthError("No refresh token stored. Disconnect and reconnect this account.")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            TOKEN_ENDPOINT,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if resp.status_code != 200:
        body = resp.text[:300]
        google_token_store.update_account(account_id, {"status": "error", "error": body})
        if "invalid_grant" in body:
            raise GoogleAuthError(
                "Google rejected the stored token (invalid_grant). This normally means access was "
                "revoked, or the OAuth app is still in 'Testing' mode where refresh tokens expire "
                "after 7 days. Reconnect the account (and publish the app to Production - see "
                "GOOGLE_SETUP.md)."
            )
        raise GoogleAuthError(f"Token refresh failed ({resp.status_code}): {body}")

    payload = resp.json()
    access_token = payload["access_token"]
    expires_in = int(payload.get("expires_in", 3600))

    # Google occasionally rotates the refresh token; keep the newest.
    if payload.get("refresh_token"):
        google_token_store.update_account(account_id, {"refresh_token": payload["refresh_token"]})

    google_token_store.update_account(account_id, {"status": "connected", "error": ""})
    _access_tokens[account_id] = (access_token, time.time() + expires_in)
    return access_token


async def revoke_account(account_id: str) -> bool:
    """Best-effort revocation at Google, then drop local copies."""
    record = google_token_store.get_secret(account_id)
    if not record:
        return False

    token = record.get("refresh_token") or record.get("access_token")
    if token:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                await client.post(REVOKE_ENDPOINT, data={"token": token})
        except Exception:
            pass  # local removal below is what actually matters to the user

    _access_tokens.pop(account_id, None)
    return google_token_store.remove_account(account_id)


# ------------------------------------------------------------------- Gmail
async def gmail_profile(account_id: str) -> Dict[str, Any]:
    token = await refresh_access_token(account_id)
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{GMAIL_API}/profile", headers={"Authorization": f"Bearer {token}"})
    if resp.status_code != 200:
        raise GoogleAuthError(f"Gmail profile unavailable ({resp.status_code}): {resp.text[:200]}")
    return resp.json()


async def gmail_list_messages(account_id: str, query: str = "", limit: int = 25) -> List[Dict[str, Any]]:
    """List messages with the metadata needed for a list view."""
    token = await refresh_access_token(account_id)
    params = {"maxResults": min(limit, 100)}
    if query:
        params["q"] = query

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get(f"{GMAIL_API}/messages", params=params, headers=headers)
        if resp.status_code != 200:
            raise GoogleAuthError(f"Gmail list failed ({resp.status_code}): {resp.text[:200]}")

        message_ids = [m["id"] for m in resp.json().get("messages", [])]

        # Gmail has no batch-get over REST without the batch endpoint, so fetch
        # details concurrently - this keeps a 25-message inbox under ~1s.
        import asyncio

        async def detail(message_id: str) -> Optional[Dict[str, Any]]:
            try:
                r = await client.get(
                    f"{GMAIL_API}/messages/{message_id}",
                    params={"format": "metadata", "metadataHeaders": ["From", "To", "Subject", "Date"]},
                    headers=headers,
                )
                if r.status_code != 200:
                    return None
                return _shape_message(r.json())
            except Exception:
                return None

        results = await asyncio.gather(*(detail(mid) for mid in message_ids))

    return [m for m in results if m]


def _header(headers: List[Dict[str, str]], name: str) -> str:
    for header in headers or []:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _shape_message(raw: Dict[str, Any]) -> Dict[str, Any]:
    payload = raw.get("payload", {}) or {}
    headers = payload.get("headers", []) or []
    label_ids = raw.get("labelIds", []) or []

    return {
        "id": raw.get("id"),
        "thread_id": raw.get("threadId"),
        "snippet": raw.get("snippet", ""),
        "from": _header(headers, "From"),
        "to": _header(headers, "To"),
        "subject": _header(headers, "Subject") or "(no subject)",
        "date": _header(headers, "Date"),
        "internal_date": raw.get("internalDate"),
        "unread": "UNREAD" in label_ids,
        "important": "IMPORTANT" in label_ids,
        "labels": label_ids,
    }


async def gmail_get_message(account_id: str, message_id: str) -> Dict[str, Any]:
    """Full message including a plain-text body."""
    token = await refresh_access_token(account_id)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{GMAIL_API}/messages/{message_id}",
            params={"format": "full"},
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code != 200:
        raise GoogleAuthError(f"Gmail message failed ({resp.status_code}): {resp.text[:200]}")

    raw = resp.json()
    shaped = _shape_message(raw)
    shaped["body"] = _extract_body(raw.get("payload", {}) or {})
    return shaped


def _extract_body(payload: Dict[str, Any], depth: int = 0) -> str:
    """Walk the MIME tree for text/plain, falling back to text/html."""
    import base64

    if depth > 6:
        return ""

    mime = payload.get("mimeType", "")
    body = payload.get("body", {}) or {}
    data = body.get("data")

    if mime == "text/plain" and data:
        try:
            return base64.urlsafe_b64decode(data + "===").decode("utf-8", "replace")
        except Exception:
            return ""

    for part in payload.get("parts", []) or []:
        text = _extract_body(part, depth + 1)
        if text:
            return text

    # No plain text anywhere - fall back to HTML with tags stripped
    if mime == "text/html" and data:
        try:
            import re

            html = base64.urlsafe_b64decode(data + "===").decode("utf-8", "replace")
            return re.sub(r"<[^>]+>", " ", html)
        except Exception:
            return ""

    return ""


# ---------------------------------------------------------------- Calendar
async def calendar_list_calendars(account_id: str) -> List[Dict[str, Any]]:
    token = await refresh_access_token(account_id)
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(
            f"{CALENDAR_API}/users/me/calendarList",
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code != 200:
        raise GoogleAuthError(f"Calendar list failed ({resp.status_code}): {resp.text[:200]}")
    return [
        {
            "id": c.get("id"),
            "summary": c.get("summary"),
            "primary": c.get("primary", False),
            "color": c.get("backgroundColor", ""),
            "access_role": c.get("accessRole", ""),
        }
        for c in resp.json().get("items", [])
    ]


async def calendar_events(
    account_id: str,
    days_ahead: int = 7,
    days_back: int = 1,
    calendar_id: str = "primary",
    limit: int = 50,
) -> List[Dict[str, Any]]:
    token = await refresh_access_token(account_id)

    now = datetime.now(timezone.utc)
    params = {
        "timeMin": (now - timedelta(days=days_back)).isoformat().replace("+00:00", "Z"),
        "timeMax": (now + timedelta(days=days_ahead)).isoformat().replace("+00:00", "Z"),
        "singleEvents": "true",   # expand recurring events into instances
        "orderBy": "startTime",
        "maxResults": min(limit, 250),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{CALENDAR_API}/calendars/{urllib.parse.quote(calendar_id)}/events",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code != 200:
        raise GoogleAuthError(f"Calendar events failed ({resp.status_code}): {resp.text[:200]}")

    events = []
    for item in resp.json().get("items", []):
        start = item.get("start", {}) or {}
        end = item.get("end", {}) or {}
        events.append({
            "id": item.get("id"),
            "summary": item.get("summary") or "(no title)",
            "description": item.get("description", ""),
            "location": item.get("location", ""),
            "start": start.get("dateTime") or start.get("date"),
            "end": end.get("dateTime") or end.get("date"),
            "all_day": "date" in start,
            "status": item.get("status"),
            "html_link": item.get("htmlLink", ""),
            "attendees": [a.get("email") for a in item.get("attendees", []) or []],
            "organizer": (item.get("organizer", {}) or {}).get("email", ""),
            "calendar_id": calendar_id,
        })
    return events


google_client = {
    "build_auth_url": build_auth_url,
    "consume_state": consume_state,
    "exchange_code": exchange_code,
    "fetch_userinfo": fetch_userinfo,
    "refresh_access_token": refresh_access_token,
    "revoke_account": revoke_account,
    "AccountNotFound": AccountNotFound,
    "gmail_profile": gmail_profile,
    "gmail_list_messages": gmail_list_messages,
    "gmail_get_message": gmail_get_message,
    "calendar_list_calendars": calendar_list_calendars,
    "calendar_events": calendar_events,
}
