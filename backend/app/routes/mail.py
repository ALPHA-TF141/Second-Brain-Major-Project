"""
Mail sources (Gmail via OAuth/IMAP).
===========================================================================
Two ways to connect, so the user is never forced into Google's verification
process just to read their own inbox:

  MAIL
    /api/mail/imap/connect      Gmail over IMAP + App Password  (no OAuth, free)
    /api/mail/accounts          every account, from either provider
    /api/mail/messages          inbox list, provider-agnostic
    /api/mail/message/{uid}     full message, provider-agnostic
    /api/mail/accounts/{id}     disconnect


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
from app.integrations.imap_mail import ImapError, GmailImapClient
from app.integrations.local_store import EncryptedStore, StoreUnavailable
from app.integrations.token_store import TokenStoreUnavailable, google_token_store
from app.models.user import User

router = APIRouter(prefix="/api", tags=["mail"])

mail_accounts = EncryptedStore("imap_accounts.enc", collection="accounts")


# ------------------------------------------------------------------ models
class ImapConnectPayload(BaseModel):
    email: str
    app_password: str
    label: Optional[str] = ""


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
