"""
Google integration routes: OAuth connect flow + Gmail + Calendar reads.
===========================================================================
Endpoint map
------------
  GET    /api/google/status                     is Google configured? which accounts?
  POST   /api/google/connect                    -> {auth_url} to open in a browser
  GET    /api/google/callback                   Google redirects here (public, state-protected)
  GET    /api/google/accounts                   connected account metadata
  DELETE /api/google/accounts/{account_id}      revoke at Google + forget locally
  GET    /api/google/gmail/messages             inbox list for one account
  GET    /api/google/gmail/message/{id}         full message body
  GET    /api/google/calendar/events            upcoming events
  GET    /api/google/calendar/calendars         which calendars are visible

NOTE ON AUTH: every route except /callback requires the app JWT. The callback
cannot, because Google does not send our Authorization header - it is protected
by the one-time `state` token we generated in /connect instead.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import settings
from app.database.session import get_db
from app.integrations import google_oauth
from app.integrations.google_oauth import GoogleAuthError, GoogleNotConfigured
from app.integrations.token_store import TokenStoreUnavailable, google_token_store
from app.models.user import User

router = APIRouter(prefix="/api/google", tags=["google"])


class ConnectPayload(BaseModel):
    email: str = ""
    services: Optional[List[str]] = None


def _raise_http(exc: Exception) -> None:
    """Map an integration error onto the right HTTP status."""
    if isinstance(exc, GoogleNotConfigured):
        raise HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, TokenStoreUnavailable):
        raise HTTPException(status_code=500, detail=str(exc))
    if isinstance(exc, GoogleAuthError):
        # 502: the failure is on Google's side / the credential, not our logic.
        raise HTTPException(status_code=502, detail=str(exc))
    raise exc


def _handle(callable_, *args, **kwargs):
    """Wrap a SYNCHRONOUS integration call."""
    try:
        return callable_(*args, **kwargs)
    except (GoogleNotConfigured, TokenStoreUnavailable, GoogleAuthError) as exc:
        _raise_http(exc)


async def _ahandle(coro):
    """
    Wrap an AWAITED integration call.

    This must be a coroutine: a plain sync wrapper returns the coroutine object
    without ever running it, so the exception escapes at `await` time, unwrapped,
    and the client gets an opaque HTTP 500 instead of a clear error.
    """
    try:
        return await coro
    except (GoogleNotConfigured, TokenStoreUnavailable, GoogleAuthError) as exc:
        _raise_http(exc)


# ----------------------------------------------------------------- status
@router.get("/status")
def google_status(_user: User = Depends(get_current_user)):
    accounts = _handle(google_token_store.list_accounts)
    return {
        "configured": settings.google_configured,
        "redirect_uri": settings.google_redirect_uri,
        "accounts": accounts,
        "account_count": len(accounts),
        "setup_help": (
            "" if settings.google_configured
            else "Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to backend/.env - see GOOGLE_SETUP.md"
        ),
    }


# ----------------------------------------------------------------- connect
@router.post("/connect")
def google_connect(payload: ConnectPayload, _user: User = Depends(get_current_user)):
    """Create a consent URL for one specific account."""
    result = _handle(
        google_oauth.build_auth_url,
        hint_email=payload.email,
        services=payload.services,
    )
    return {
        "auth_url": result["auth_url"],
        "state": result["state"],
        "email": payload.email,
    }


# ---------------------------------------------------------------- callback
_SUCCESS_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Jarvis - Account Connected</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
         background:#070a13; color:#e2e8f0;
         font-family:'Inter',-apple-system,Segoe UI,Roboto,sans-serif; }}
  .card {{ width:min(520px,92vw); border:1px solid rgba(53,216,255,.25); border-radius:20px;
           background:linear-gradient(180deg,#0d1326,#070a13); padding:34px 30px; text-align:center;
           box-shadow:0 0 60px rgba(53,216,255,.10); }}
  .badge {{ display:inline-flex; align-items:center; gap:8px; font:600 11px/1 ui-monospace,monospace;
            letter-spacing:.18em; text-transform:uppercase; color:{accent}; }}
  .dot {{ width:8px; height:8px; border-radius:99px; background:{accent}; box-shadow:0 0 12px {accent}; }}
  h1 {{ font-size:21px; margin:16px 0 6px; color:#fff; }}
  p {{ margin:6px 0; color:#94a3b8; font-size:13.5px; line-height:1.6; }}
  .email {{ color:{accent}; font-weight:600; }}
  .hint {{ margin-top:20px; font-size:12px; color:#64748b; }}
</style></head>
<body><div class="card">
  <span class="badge"><span class="dot"></span>JARVIS INTEGRATION</span>
  <h1>{title}</h1>
  <p>{message}</p>
  <p class="hint">You can close this tab and return to Jarvis.</p>
</div></body></html>"""


def _page(title: str, message: str, accent: str = "#35d8ff") -> HTMLResponse:
    return HTMLResponse(
        _SUCCESS_PAGE.format(title=title, message=message, accent=accent)
    )


@router.get("/callback", response_class=HTMLResponse)
async def google_callback(
    code: str = Query(default=""),
    state: str = Query(default=""),
    error: str = Query(default=""),
):
    """
    Google redirects the browser here after the user approves (or denies).
    This route is intentionally NOT behind the app JWT.
    """
    if error:
        return _page(
            "Connection Cancelled",
            f"Google returned: <b>{error}</b>. Nothing was connected.",
            accent="#fbbf24",
        )

    if not code or not state:
        return _page("Invalid Callback", "Missing authorization code or state.", accent="#f87171")

    pending = google_oauth.consume_state(state)
    if not pending:
        return _page(
            "Link Expired",
            "This connection link was already used or has expired (15 minute limit). "
            "Start again from Jarvis.",
            accent="#fbbf24",
        )

    try:
        tokens = await google_oauth.exchange_code(code)
    except Exception as exc:
        return _page("Connection Failed", f"<code>{str(exc)[:220]}</code>", accent="#f87171")

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        return _page(
            "No Refresh Token",
            "Google did not return a long-lived token. Remove Jarvis from your Google account's "
            "third-party access list, then connect again.",
            accent="#fbbf24",
        )

    try:
        profile = await google_oauth.fetch_userinfo(tokens["access_token"])
    except Exception as exc:
        return _page("Profile Lookup Failed", f"<code>{str(exc)[:220]}</code>", accent="#f87171")

    email = (profile.get("email") or pending.get("hint_email") or "").lower()
    if not email:
        return _page("Connection Failed", "Google did not return an email address.", accent="#f87171")

    services = pending.get("services") or ["gmail", "calendar"]
    scopes = (tokens.get("scope") or "").split()

    google_token_store.upsert_account({
        "id": (google_token_store.find_by_email(email) or {}).get("id") or f"gacct_{uuid.uuid4().hex[:12]}",
        "email": email,
        "name": profile.get("name", ""),
        "picture": profile.get("picture", ""),
        "refresh_token": refresh_token,
        "access_token": tokens.get("access_token", ""),
        "scopes": scopes,
        "services": [s for s in services if f"{s}." in " ".join(scopes)] or services,
        "connected_at": datetime.utcnow().isoformat(),
        "status": "connected",
        "error": "",
    })

    granted = []
    if any("gmail" in s for s in scopes):
        granted.append("Gmail (read-only)")
    if any("calendar" in s for s in scopes):
        granted.append("Calendar (read-only)")

    return _page(
        "Connected Successfully",
        f"<span class='email'>{email}</span> is now linked to your Second Brain.<br>"
        f"Access granted: {', '.join(granted) if granted else 'profile only'}",
        accent="#5ef2b8",
    )


# ---------------------------------------------------------------- accounts
@router.get("/accounts")
def list_accounts(_user: User = Depends(get_current_user)):
    return _handle(google_token_store.list_accounts)


@router.delete("/accounts/{account_id}")
async def disconnect_account(account_id: str, _user: User = Depends(get_current_user)):
    removed = await google_oauth.revoke_account(account_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"success": True, "account_id": account_id}


# ------------------------------------------------------------------- Gmail
@router.get("/gmail/messages")
async def gmail_messages(
    account_id: str = Query(...),
    q: str = Query(default=""),
    limit: int = Query(default=25, ge=1, le=100),
    _user: User = Depends(get_current_user),
):
    messages = await _ahandle(google_oauth.gmail_list_messages(account_id, q, limit))
    google_token_store.touch(account_id)
    return {"account_id": account_id, "query": q, "count": len(messages), "messages": messages}


@router.get("/gmail/message/{message_id}")
async def gmail_message(
    message_id: str,
    account_id: str = Query(...),
    _user: User = Depends(get_current_user),
):
    return await _ahandle(google_oauth.gmail_get_message(account_id, message_id))


@router.get("/gmail/profile")
async def gmail_profile(account_id: str = Query(...), _user: User = Depends(get_current_user)):
    return await _ahandle(google_oauth.gmail_profile(account_id))


# ---------------------------------------------------------------- Calendar
@router.get("/calendar/events")
async def calendar_events(
    account_id: str = Query(...),
    days_ahead: int = Query(default=7, ge=1, le=90),
    days_back: int = Query(default=1, ge=0, le=30),
    calendar_id: str = Query(default="primary"),
    limit: int = Query(default=50, ge=1, le=250),
    _user: User = Depends(get_current_user),
):
    events = await _ahandle(
        google_oauth.calendar_events(account_id, days_ahead, days_back, calendar_id, limit)
    )
    google_token_store.touch(account_id)
    return {"account_id": account_id, "calendar_id": calendar_id, "count": len(events), "events": events}


@router.get("/calendar/calendars")
async def calendar_calendars(account_id: str = Query(...), _user: User = Depends(get_current_user)):
    return await _ahandle(google_oauth.calendar_list_calendars(account_id))
