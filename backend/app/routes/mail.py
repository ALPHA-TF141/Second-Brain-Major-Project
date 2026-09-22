"""
Unified mail + calendar sources.
===========================================================================
Two ways to connect, so the user is never forced into Google's verification
process just to read their own inbox:

  MAIL
    /api/mail/imap/connect      Gmail over IMAP + App Password  (no OAuth, free)
    /api/mail/accounts          every account, from either provider
    /api/mail/messages          inbox list, provider-agnostic
    /api/mail/message/{uid}     full message, provider-agnostic
    /api/mail/accounts/{id}     disconnect

  CALENDAR
    /api/calendar/feed          add a private iCal (ICS) address (no OAuth, free)
    /api/calendar/sources       every calendar source
    /api/calendar/source-events events from whichever provider
    /api/calendar/feed/{id}     remove

The Google OAuth routes still exist in /api/google/* and appear in these lists
when configured - so nothing that worked before stopped working.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.integrations import google_oauth
from app.integrations.google_oauth import AccountNotFound, GoogleAuthError, GoogleNotConfigured
from app.integrations.ical_calendar import CalendarFeedError, fetch_feed
from app.integrations.imap_mail import ImapError, GmailImapClient
from app.integrations.local_store import EncryptedStore, StoreUnavailable
from app.integrations.token_store import TokenStoreUnavailable, google_token_store
from app.models.user import User

router = APIRouter(prefix="/api", tags=["mail"])

mail_accounts = EncryptedStore("imap_accounts.enc", collection="accounts")
calendar_feeds = EncryptedStore("calendar_feeds.enc", collection="feeds")


# ------------------------------------------------------------------ models
class ImapConnectPayload(BaseModel):
    email: str
    app_password: str
    label: Optional[str] = ""


class CalendarFeedPayload(BaseModel):
    url: str
    label: Optional[str] = ""
    account_email: Optional[str] = ""


def _friendly(exc: Exception) -> str:
    return str(exc)


def _google_error(exc: Exception) -> HTTPException:
    """Map a Google-layer failure onto a clear HTTP status.

    GoogleNotConfigured is a RuntimeError subclass, so if it is not handled
    explicitly it escapes as an opaque HTTP 500. It is really "you have not set
    up credentials yet" - a 400 with instructions, not a server fault.
    """
    if isinstance(exc, GoogleNotConfigured):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, AccountNotFound):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=502, detail=str(exc))


# ================================================================== MAIL
@router.get("/mail/accounts")
def list_mail_accounts(_user: User = Depends(get_current_user)):
    """Every mail account, whichever way it is connected."""
    accounts: List[Dict[str, Any]] = []

    try:
        for account in google_token_store.list_accounts():
            if "gmail" in (account.get("services") or ["gmail"]):
                accounts.append({**account, "provider": "google", "provider_label": "Google OAuth"})
    except (TokenStoreUnavailable, Exception):
        pass

    try:
        for account in mail_accounts.all():
            accounts.append({
                "id": account.get("id"),
                "email": account.get("email"),
                "name": account.get("label") or "IMAP account",
                "services": ["gmail"],
                "scopes": [],
                "connected_at": account.get("created_at"),
                "last_used": account.get("last_used"),
                "status": account.get("status", "connected"),
                "error": account.get("error", ""),
                "provider": "imap",
                "provider_label": "IMAP + App Password",
                "stats": account.get("stats", {}),
            })
    except StoreUnavailable:
        pass

    return accounts


@router.post("/mail/imap/connect")
async def connect_imap(payload: ImapConnectPayload, _user: User = Depends(get_current_user)):
    """
    Verify an app password by actually logging in, then store it encrypted.
    Credentials are never saved unless the login succeeds.
    """
    address = payload.email.strip()
    if "@" not in address:
        raise HTTPException(status_code=400, detail="Enter a full email address.")
    if not payload.app_password.strip():
        raise HTTPException(status_code=400, detail="Enter the 16-character app password.")

    client = GmailImapClient(address, payload.app_password)

    try:
        # IMAP is blocking; keep it off the event loop.
        result = await asyncio.to_thread(client.verify)
    except ImapError as exc:
        raise HTTPException(status_code=400, detail=_friendly(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"IMAP error: {_friendly(exc)}")

    existing = next((a for a in mail_accounts.all() if (a.get("email") or "").lower() == address.lower()), None)

    record = {
        "id": existing["id"] if existing else f"imap_{uuid.uuid4().hex[:12]}",
        "email": address,
        "label": payload.label or "Gmail via IMAP",
        "app_password": payload.app_password.replace(" ", "").strip(),
        "status": "connected",
        "error": "",
        "stats": {
            "total_messages": result.get("total_messages", 0),
            "unread": result.get("unread", 0),
            "checked_at": result.get("checked_at", ""),
        },
    }

    saved = mail_accounts.put(record)
    return {"success": True, "account": {**saved, "provider": "imap"}, "verified": result}


@router.get("/mail/imap/recheck/{account_id}")
async def recheck_imap(account_id: str, _user: User = Depends(get_current_user)):
    record = mail_accounts.get(account_id)
    if not record:
        raise HTTPException(status_code=404, detail="Account not found")

    client = GmailImapClient(record["email"], record.get("app_password", ""))
    try:
        result = await asyncio.to_thread(client.verify)
    except Exception as exc:
        mail_accounts.update(account_id, {"status": "error", "error": _friendly(exc)})
        raise HTTPException(status_code=502, detail=_friendly(exc))

    mail_accounts.update(account_id, {
        "status": "connected",
        "error": "",
        "stats": {
            "total_messages": result.get("total_messages", 0),
            "unread": result.get("unread", 0),
            "checked_at": result.get("checked_at", ""),
        },
    })
    return result


@router.delete("/mail/accounts/{account_id}")
async def disconnect_mail(account_id: str, _user: User = Depends(get_current_user)):
    """Handles both providers so the UI needs one button."""
    if account_id.startswith("imap_"):
        if not mail_accounts.remove(account_id):
            raise HTTPException(status_code=404, detail="Account not found")
        return {"success": True, "account_id": account_id, "provider": "imap"}

    removed = await google_oauth.revoke_account(account_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"success": True, "account_id": account_id, "provider": "google"}


@router.get("/mail/messages")
async def mail_messages(
    account_id: str = Query(...),
    folder: str = Query(default="inbox"),
    q: str = Query(default=""),
    limit: int = Query(default=30, ge=1, le=100),
    _user: User = Depends(get_current_user),
):
    """Inbox listing that works for either provider."""
    if account_id.startswith("imap_"):
        record = mail_accounts.get(account_id)
        if not record:
            raise HTTPException(status_code=404, detail="Account not found")

        client = GmailImapClient(record["email"], record.get("app_password", ""))
        try:
            messages = await asyncio.to_thread(client.list_messages, folder, limit, q)
        except Exception as exc:
            mail_accounts.update(account_id, {"status": "error", "error": _friendly(exc)})
            raise HTTPException(status_code=502, detail=_friendly(exc))

        mail_accounts.update(account_id, {"last_used": datetime.utcnow().isoformat()})
        return {
            "account_id": account_id, "provider": "imap", "folder": folder,
            "query": q, "count": len(messages), "messages": messages,
        }

    # Resolve the account locally FIRST. Otherwise an unknown id reaches Google,
    # and the status code ends up depending on whether Google happens to be
    # configured (400) or not (404) - which is not a property of the request.
    # A missing account is always 404, and we never call the provider for one.
    if not google_token_store.get_secret(account_id):
        raise HTTPException(status_code=404, detail="Mail account not found - it may have been disconnected.")

    try:
        messages = await google_oauth.gmail_list_messages(account_id, q, limit)
    except (AccountNotFound, GoogleAuthError, GoogleNotConfigured) as exc:
        raise _google_error(exc)
    google_token_store.touch(account_id)
    return {
        "account_id": account_id, "provider": "google", "folder": folder,
        "query": q, "count": len(messages), "messages": messages,
    }


@router.get("/mail/message/{message_id}")
async def mail_message(
    message_id: str,
    account_id: str = Query(...),
    folder: str = Query(default="inbox"),
    _user: User = Depends(get_current_user),
):
    if account_id.startswith("imap_"):
        record = mail_accounts.get(account_id)
        if not record:
            raise HTTPException(status_code=404, detail="Account not found")
        client = GmailImapClient(record["email"], record.get("app_password", ""))
        try:
            return await asyncio.to_thread(client.get_message, message_id, folder)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=_friendly(exc))

    if not google_token_store.get_secret(account_id):
        raise HTTPException(status_code=404, detail="Mail account not found")

    try:
        return await google_oauth.gmail_get_message(account_id, message_id)
    except (AccountNotFound, GoogleAuthError, GoogleNotConfigured) as exc:
        raise _google_error(exc)


# ============================================================== CALENDAR
@router.get("/calendar/sources")
def list_calendar_sources(_user: User = Depends(get_current_user)):
    sources: List[Dict[str, Any]] = []

    try:
        for account in google_token_store.list_accounts():
            if "calendar" in (account.get("services") or ["gmail", "calendar"]):
                sources.append({**account, "provider": "google", "provider_label": "Google OAuth",
                                "kind": "live"})
    except Exception:
        pass

    try:
        for feed in calendar_feeds.all():
            sources.append({
                "id": feed.get("id"),
                "email": feed.get("label") or feed.get("account_email") or "Calendar feed",
                "name": feed.get("label") or "iCal feed",
                "connected_at": feed.get("created_at"),
                "last_used": feed.get("last_used"),
                "status": feed.get("status", "connected"),
                "error": feed.get("error", ""),
                "provider": "ical",
                "provider_label": "iCal secret address",
                "kind": "snapshot",
                "url_hint": feed.get("url_hint", ""),
            })
    except StoreUnavailable:
        pass

    return sources


@router.post("/calendar/feed")
async def add_calendar_feed(payload: CalendarFeedPayload, _user: User = Depends(get_current_user)):
    """Validate the ICS URL by fetching it once, then store it encrypted."""
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Paste the calendar's iCal address.")

    try:
        preview = await asyncio.to_thread(fetch_feed, url, 7, 0, 5)
    except CalendarFeedError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    existing = next((f for f in calendar_feeds.all() if f.get("url_hash") == str(abs(hash(url)))), None)

    record = {
        "id": existing["id"] if existing else f"ics_{uuid.uuid4().hex[:12]}",
        "label": payload.label or payload.account_email or "Calendar",
        "account_email": payload.account_email or "",
        "secret_url": url,
        "url_hash": str(abs(hash(url))),
        "status": "connected",
        "error": "",
        "stats": {"parsed_events": preview.get("parsed_events", 0),
                  "in_window": preview.get("total_in_window", 0)},
    }
    saved = calendar_feeds.put(record)
    return {"success": True, "source": saved, "preview_events": preview.get("events", [])}


@router.get("/calendar/source-events")
async def calendar_source_events(
    source_id: str = Query(...),
    days_ahead: int = Query(default=7, ge=1, le=90),
    days_back: int = Query(default=1, ge=0, le=30),
    limit: int = Query(default=200, ge=1, le=1000),
    _user: User = Depends(get_current_user),
):
    if source_id.startswith("ics_"):
        feed = calendar_feeds.get(source_id)
        if not feed:
            raise HTTPException(status_code=404, detail="Calendar feed not found")
        try:
            result = await asyncio.to_thread(fetch_feed, feed["secret_url"], days_ahead, days_back, limit)
        except CalendarFeedError as exc:
            calendar_feeds.update(source_id, {"status": "error", "error": str(exc)})
            raise HTTPException(status_code=502, detail=str(exc))
        calendar_feeds.update(source_id, {
            "last_used": datetime.utcnow().isoformat(), "status": "connected", "error": "",
        })
        return {"source_id": source_id, "provider": "ical", "count": len(result["events"]),
                "events": result["events"]}

    if not google_token_store.get_secret(source_id):
        raise HTTPException(
            status_code=404,
            detail="Calendar source not found. Use /api/calendar/sources to list the connected ones.",
        )

    try:
        events = await google_oauth.calendar_events(source_id, days_ahead, days_back, "primary", limit)
    except (AccountNotFound, GoogleAuthError, GoogleNotConfigured) as exc:
        raise _google_error(exc)
    google_token_store.touch(source_id)
    return {"source_id": source_id, "provider": "google", "count": len(events), "events": events}


# ============================================================ INGESTION
class SyncPayload(BaseModel):
    account_id: Optional[str] = ""      # empty = every connected account
    folders: Optional[List[str]] = None
    limit: Optional[int] = None
    store_in_vault: Optional[bool] = None


@router.get("/mail/sync/status")
def mail_sync_status(_user: User = Depends(get_current_user)):
    from app.agents.mail_ingestion_agent import mail_ingestion_agent

    status = mail_ingestion_agent.status()
    # Which accounts are actually available to sync right now
    try:
        imap_ids = [a["id"] for a in mail_accounts.all()]
    except StoreUnavailable:
        imap_ids = []
    status["syncable_accounts"] = imap_ids
    return status


@router.post("/mail/sync")
async def mail_sync(payload: SyncPayload, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """
    Read new mail from the connected account(s) and turn it into memories.

    Runs in a worker thread: IMAP is blocking, and a first sync can take a while.
    """
    from app.agents.mail_ingestion_agent import mail_ingestion_agent

    if payload.store_in_vault is not None:
        settings.mail_store_in_vault = bool(payload.store_in_vault)

    def run():
        from app.database.session import SessionLocal

        local = SessionLocal()
        try:
            if payload.account_id:
                return mail_ingestion_agent.sync_account(
                    local, payload.account_id, user.id,
                    folders=payload.folders, limit=payload.limit,
                )
            return mail_ingestion_agent.sync_all(local, user.id)
        finally:
            local.close()

    result = await asyncio.to_thread(run)
    if result.get("errors") and not result.get("ingested"):
        # Surface the first error clearly rather than a silent empty result
        first = result["errors"][0] if isinstance(result.get("errors"), list) else str(result["errors"])
        raise HTTPException(status_code=502, detail=first)
    return result


@router.delete("/calendar/feed/{source_id}")
def remove_calendar_feed(source_id: str, _user: User = Depends(get_current_user)):
    if not calendar_feeds.remove(source_id):
        raise HTTPException(status_code=404, detail="Calendar feed not found")
    return {"success": True, "source_id": source_id}
