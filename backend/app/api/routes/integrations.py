from datetime import datetime, timezone
import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.activity import Activity
from app.db.models.integration import Integration, IntegrationProvider, IntegrationStatus
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.integration import (
    AuthUrlResponse,
    ConnectRequest,
    ConnectResultResponse,
    IntegrationResponse,
    SaveKeysRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()

PROVIDER_METADATA = {
    IntegrationProvider.SLACK: {
        "name": "Slack",
        "description": "Receive and summarize new Slack messages.",
        "icon": "💬",
    },
    IntegrationProvider.GMAIL: {
        "name": "Gmail",
        "description": "Summarize incoming emails via Google OAuth2.",
        "icon": "✉️",
    },
    IntegrationProvider.GOOGLE_DRIVE: {
        "name": "Google Drive",
        "description": "Track newly uploaded documents.",
        "icon": "📁",
    },
}


def get_or_create_default_user(db: Session) -> User:
    settings = get_settings()
    user = db.scalar(select(User).where(User.email == settings.default_user_email))
    if user is None:
        user = User(email=settings.default_user_email, display_name="Workspace User")
        db.add(user)
        db.flush()
    return user


async def summarize_text_with_gemini(title: str, text: str, gemini_key: str | None) -> str:
    if not gemini_key:
        return text[:150] + "..." if len(text) > 150 else text

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                json={
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": f"Summarize this email in one factual sentence.\nSubject: {title}\nContent: {text}"
                                }
                            ]
                        }
                    ]
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                cand = data.get("candidates", [])
                if cand:
                    parts = cand[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
    except Exception as e:
        logger.warning(f"Could not summarize email with Gemini: {e}")

    return text[:150] + "..." if len(text) > 150 else text


import asyncio


async def fetch_and_process_single_message(client: httpx.AsyncClient, msg_id: str, access_token: str, gemini_key: str | None):
    try:
        msg_resp = await client.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if msg_resp.status_code != 200:
            return None

        msg_data = msg_resp.json()
        headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
        title = headers.get("Subject", "(No Subject)")
        sender = headers.get("From", "Unknown Sender")
        snippet = msg_data.get("snippet", title)
        thread_id = msg_data.get("threadId", msg_id)
        source_url = f"https://mail.google.com/mail/u/0/#all/{thread_id}"

        summary = await summarize_text_with_gemini(title, snippet, gemini_key)

        return {
            "msg_id": msg_id,
            "title": title,
            "sender": sender,
            "snippet": snippet,
            "thread_id": thread_id,
            "source_url": source_url,
            "summary": summary,
        }
    except Exception as e:
        logger.warning(f"Failed to process message {msg_id}: {e}")
        return None


async def sync_gmail_unread_emails_to_db(db: Session, user: User, access_token: str) -> int:
    settings = get_settings()
    synced_count = 0

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            list_resp = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages?q=is:unread&maxResults=8",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if list_resp.status_code != 200:
                logger.error(f"Gmail list messages failed: {list_resp.text}")
                return 0

            messages = list_resp.json().get("messages", [])
            if not messages:
                return 0

            tasks = [
                fetch_and_process_single_message(client, m["id"], access_token, settings.gemini_api_key)
                for m in messages if m.get("id")
            ]
            results = await asyncio.gather(*tasks)

            now = datetime.now(timezone.utc)
            for item in results:
                if not item:
                    continue

                existing = db.scalar(
                    select(Activity).where(
                        Activity.user_id == user.id,
                        Activity.source == "gmail",
                        Activity.external_id == item["msg_id"],
                    )
                )

                if existing is None:
                    activity = Activity(
                        user_id=user.id,
                        source="gmail",
                        activity_type="email",
                        external_id=item["msg_id"],
                        title=item["title"],
                        sender=item["sender"],
                        summary=item["summary"],
                        original_content=item["snippet"],
                        source_url=item["source_url"],
                        event_created_at=now,
                        processed_at=now,
                        metadata_json={"thread_id": item["thread_id"], "subject": item["title"]},
                    )
                    db.add(activity)
                else:
                    existing.title = item["title"]
                    existing.sender = item["sender"]
                    existing.summary = item["summary"]
                    existing.original_content = item["snippet"]
                    existing.processed_at = now

                synced_count += 1

            db.commit()
    except Exception as e:
        logger.error(f"Error syncing Gmail emails: {e}")

    return synced_count


async def sync_google_drive_files_to_db(db: Session, user: User, access_token: str) -> int:
    settings = get_settings()
    synced_count = 0

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://www.googleapis.com/drive/v3/files?pageSize=8&fields=files(id,name,mimeType,description,createdTime,modifiedTime,webViewLink,owners)",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code != 200:
                logger.error(f"Google Drive list files failed: {resp.text}")
                return 0

            files = resp.json().get("files", [])
            now = datetime.now(timezone.utc)

            for file_item in files:
                file_id = file_item.get("id")
                if not file_id:
                    continue

                name = file_item.get("name", "Untitled Document")
                description = file_item.get("description") or f"Google Drive File: {name} ({file_item.get('mimeType', 'file')})"
                owners = file_item.get("owners", [])
                owner_name = owners[0].get("displayName") if owners else "Google Drive Owner"
                web_url = file_item.get("webViewLink") or f"https://drive.google.com/file/d/{file_id}/view"

                summary = await summarize_text_with_gemini(name, description, settings.gemini_api_key)

                existing = db.scalar(
                    select(Activity).where(
                        Activity.user_id == user.id,
                        Activity.source == "google_drive",
                        Activity.external_id == file_id,
                    )
                )

                if existing is None:
                    activity = Activity(
                        user_id=user.id,
                        source="google_drive",
                        activity_type="document",
                        external_id=file_id,
                        title=name,
                        sender=owner_name,
                        summary=summary,
                        original_content=description,
                        source_url=web_url,
                        event_created_at=now,
                        processed_at=now,
                        metadata_json={"file_id": file_id, "mime_type": file_item.get("mimeType")},
                    )
                    db.add(activity)
                else:
                    existing.title = name
                    existing.sender = owner_name
                    existing.summary = summary
                    existing.original_content = description
                    existing.processed_at = now

                synced_count += 1

            db.commit()
    except Exception as e:
        logger.error(f"Error syncing Google Drive files: {e}")

    return synced_count


@router.get("", response_model=list[IntegrationResponse])
def list_integrations(db: Session = Depends(get_db)):
    settings = get_settings()
    user = get_or_create_default_user(db)
    db_integrations = db.scalars(select(Integration).where(Integration.user_id == user.id)).all()
    status_map = {integ.provider: integ for integ in db_integrations}

    result = []
    for provider in IntegrationProvider:
        meta = PROVIDER_METADATA[provider]
        db_item = status_map.get(provider)
        current_status = db_item.status if db_item else IntegrationStatus.DISCONNECTED
        connected_at = db_item.connected_at if db_item else None

        n8n_url = (
            settings.n8n_gmail_webhook_url if provider == IntegrationProvider.GMAIL
            else settings.n8n_slack_webhook_url if provider == IntegrationProvider.SLACK
            else settings.n8n_google_drive_webhook_url
        )

        has_oauth = (
            bool(settings.google_client_id and settings.google_client_secret)
            if provider in (IntegrationProvider.GMAIL, IntegrationProvider.GOOGLE_DRIVE)
            else bool(settings.slack_client_id and settings.slack_client_secret)
        )

        result.append(
            IntegrationResponse(
                provider=provider,
                name=meta["name"],
                description=meta["description"],
                icon=meta["icon"],
                status=current_status,
                connected_at=connected_at,
                n8n_webhook_url=n8n_url,
                has_oauth_config=has_oauth,
            )
        )
    return result


def clean_client_id(cid: str | None) -> str | None:
    if not cid:
        return None
    cleaned = cid.strip()
    if cleaned.startswith("http://"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("https://"):
        cleaned = cleaned[8:]
    return cleaned.rstrip("/")


@router.get("/gmail/auth-url", response_model=AuthUrlResponse)
def get_gmail_auth_url(client_id: str | None = None):
    settings = get_settings()
    effective_client_id = clean_client_id(client_id) or clean_client_id(settings.google_client_id)
    if not effective_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Client ID is missing. Please enter your Client ID in settings or set GOOGLE_CLIENT_ID in backend/.env.",
        )

    params = {
        "client_id": effective_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.email",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return AuthUrlResponse(auth_url=auth_url, provider="gmail")


@router.get("/google_drive/auth-url", response_model=AuthUrlResponse)
def get_google_drive_auth_url(client_id: str | None = None):
    settings = get_settings()
    effective_client_id = clean_client_id(client_id) or clean_client_id(settings.google_client_id)
    if not effective_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Client ID is missing. Please enter your Client ID in settings or set GOOGLE_CLIENT_ID in backend/.env.",
        )

    params = {
        "client_id": effective_client_id,
        "redirect_uri": settings.google_drive_redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/userinfo.email",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return AuthUrlResponse(auth_url=auth_url, provider="google_drive")


@router.get("/slack/auth-url", response_model=AuthUrlResponse)
def get_slack_auth_url(client_id: str | None = None):
    settings = get_settings()
    effective_client_id = clean_client_id(client_id) or clean_client_id(settings.slack_client_id)
    if not effective_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slack Client ID is missing. Please set SLACK_CLIENT_ID in backend/.env.",
        )

    params = {
        "client_id": effective_client_id,
        "user_scope": "channels:history,chat:write,users:read",
        "redirect_uri": settings.slack_redirect_uri,
    }
    auth_url = f"https://slack.com/oauth/v2/authorize?{urlencode(params)}"
    return AuthUrlResponse(auth_url=auth_url, provider="slack")


@router.get("/google_drive/callback")
async def google_drive_oauth_callback(
    code: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if error:
        return RedirectResponse(f"http://localhost:3000/integrations?error={error}")

    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code")

    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth credentials not configured.",
        )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_drive_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if resp.status_code != 200:
            logger.error(f"Failed to exchange Google Drive OAuth code: {resp.text}")
            return RedirectResponse("http://localhost:3000/integrations?error=token_exchange_failed")

        tokens = resp.json()

    user = get_or_create_default_user(db)
    integration = db.scalar(
        select(Integration).where(
            Integration.user_id == user.id,
            Integration.provider == IntegrationProvider.GOOGLE_DRIVE,
        )
    )

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    if integration is None:
        integration = Integration(
            user_id=user.id,
            provider=IntegrationProvider.GOOGLE_DRIVE,
            status=IntegrationStatus.CONNECTED,
            access_token_encrypted=access_token,
            refresh_token_encrypted=refresh_token,
            connected_at=datetime.now(timezone.utc),
        )
        db.add(integration)
    else:
        integration.status = IntegrationStatus.CONNECTED
        integration.access_token_encrypted = access_token
        if refresh_token:
            integration.refresh_token_encrypted = refresh_token
        integration.connected_at = datetime.now(timezone.utc)

    db.commit()

    if access_token:
        await sync_google_drive_files_to_db(db, user, access_token)

    if settings.n8n_google_drive_webhook_url:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                await client.post(
                    settings.n8n_google_drive_webhook_url,
                    json={
                        "event": "connect",
                        "provider": "google_drive",
                        "access_token": access_token,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
        except Exception as e:
            logger.warning(f"Could not trigger n8n after Google Drive OAuth: {e}")

    return RedirectResponse("http://localhost:3000/integrations?connected=google_drive")


@router.get("/slack/callback")
async def slack_oauth_callback(
    code: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if error:
        return RedirectResponse(f"http://localhost:3000/integrations?error={error}")

    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code")

    if not settings.slack_client_id or not settings.slack_client_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slack OAuth credentials (SLACK_CLIENT_ID / SLACK_CLIENT_SECRET) not set.",
        )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "code": code,
                "client_id": settings.slack_client_id,
                "client_secret": settings.slack_client_secret,
                "redirect_uri": settings.slack_redirect_uri,
            },
        )
        if resp.status_code != 200 or not resp.json().get("ok"):
            logger.error(f"Failed to exchange Slack OAuth code: {resp.text}")
            return RedirectResponse("http://localhost:3000/integrations?error=slack_token_failed")

        data = resp.json()
        authed_user = data.get("authed_user", {})
        access_token = authed_user.get("access_token") or data.get("access_token")

    user = get_or_create_default_user(db)
    integration = db.scalar(
        select(Integration).where(
            Integration.user_id == user.id,
            Integration.provider == IntegrationProvider.SLACK,
        )
    )

    if integration is None:
        integration = Integration(
            user_id=user.id,
            provider=IntegrationProvider.SLACK,
            status=IntegrationStatus.CONNECTED,
            access_token_encrypted=access_token,
            connected_at=datetime.now(timezone.utc),
        )
        db.add(integration)
    else:
        integration.status = IntegrationStatus.CONNECTED
        integration.access_token_encrypted = access_token
        integration.connected_at = datetime.now(timezone.utc)

    db.commit()

    if settings.n8n_slack_webhook_url:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                await client.post(
                    settings.n8n_slack_webhook_url,
                    json={
                        "event": "connect",
                        "provider": "slack",
                        "access_token": access_token,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
        except Exception as e:
            logger.warning(f"Could not trigger n8n after Slack OAuth login: {e}")

    return RedirectResponse("http://localhost:3000/integrations?connected=slack")


@router.post("/gmail/save-keys")
def save_keys(payload: SaveKeysRequest):
    settings = get_settings()
    if payload.google_client_id:
        settings.google_client_id = clean_client_id(payload.google_client_id)
    if payload.google_client_secret:
        settings.google_client_secret = payload.google_client_secret.strip()
    if payload.gemini_api_key:
        settings.gemini_api_key = payload.gemini_api_key.strip()

    return {
        "status": "success",
        "message": "Credentials updated successfully.",
        "has_client_id": bool(settings.google_client_id),
        "has_client_secret": bool(settings.google_client_secret),
        "has_gemini_key": bool(settings.gemini_api_key),
    }


@router.post("/{provider}/connect", response_model=ConnectResultResponse)
async def connect_integration(
    provider: IntegrationProvider,
    payload: ConnectRequest | None = None,
    db: Session = Depends(get_db),
):
    settings = get_settings()
    user = get_or_create_default_user(db)

    integration = db.scalar(
        select(Integration).where(
            Integration.user_id == user.id,
            Integration.provider == provider,
        )
    )
    if integration is None:
        integration = Integration(
            user_id=user.id,
            provider=provider,
            status=IntegrationStatus.CONNECTED,
            connected_at=datetime.now(timezone.utc),
        )
        db.add(integration)
    else:
        integration.status = IntegrationStatus.CONNECTED
        integration.connected_at = datetime.now(timezone.utc)

    db.commit()

    if provider == IntegrationProvider.GMAIL and integration.access_token_encrypted:
        await sync_gmail_unread_emails_to_db(db, user, integration.access_token_encrypted)

    target_webhook_url = (payload and payload.webhook_url) or settings.n8n_gmail_webhook_url
    n8n_triggered = False
    message = f"{PROVIDER_METADATA[provider]['name']} connected successfully."

    if target_webhook_url:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.post(
                    target_webhook_url,
                    json={
                        "event": "connect",
                        "provider": provider.value,
                        "access_token": integration.access_token_encrypted,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
                if resp.status_code in (200, 201, 202, 204):
                    n8n_triggered = True
                    message += " n8n workflow triggered to sync activity!"
                else:
                    message += f" Note: n8n webhook returned HTTP {resp.status_code}."
        except Exception as e:
            logger.warning(f"Could not contact n8n webhook at {target_webhook_url}: {e}")
            message += " Saved integration status (n8n workflow offline or waiting for trigger)."

    return ConnectResultResponse(
        provider=provider.value,
        status=IntegrationStatus.CONNECTED,
        n8n_triggered=n8n_triggered,
        message=message,
    )


@router.post("/{provider}/disconnect", response_model=ConnectResultResponse)
def disconnect_integration(
    provider: IntegrationProvider,
    db: Session = Depends(get_db),
):
    user = get_or_create_default_user(db)
    integration = db.scalar(
        select(Integration).where(
            Integration.user_id == user.id,
            Integration.provider == provider,
        )
    )
    if integration:
        integration.status = IntegrationStatus.DISCONNECTED
        db.commit()

    return ConnectResultResponse(
        provider=provider.value,
        status=IntegrationStatus.DISCONNECTED,
        n8n_triggered=False,
        message=f"{PROVIDER_METADATA[provider]['name']} disconnected.",
    )


@router.post("/{provider}/sync", response_model=ConnectResultResponse)
async def sync_integration(
    provider: IntegrationProvider,
    payload: ConnectRequest | None = None,
    db: Session = Depends(get_db),
):
    settings = get_settings()
    user = get_or_create_default_user(db)
    integration = db.scalar(
        select(Integration).where(
            Integration.user_id == user.id,
            Integration.provider == provider,
        )
    )

    synced_count = 0
    if provider == IntegrationProvider.GMAIL and integration and integration.access_token_encrypted:
        synced_count = await sync_gmail_unread_emails_to_db(db, user, integration.access_token_encrypted)

    target_webhook_url = (payload and payload.webhook_url) or settings.n8n_gmail_webhook_url
    n8n_triggered = False
    message = f"Synced {synced_count} unread email(s) for {PROVIDER_METADATA[provider]['name']}."

    if target_webhook_url:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    target_webhook_url,
                    json={
                        "event": "sync",
                        "provider": provider.value,
                        "access_token": integration.access_token_encrypted if integration else None,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
                if resp.status_code in (200, 201, 202, 204):
                    n8n_triggered = True
                    message += " n8n workflow executed!"
        except Exception as e:
            logger.warning(f"Could not send sync trigger to n8n: {e}")

    return ConnectResultResponse(
        provider=provider.value,
        status=IntegrationStatus.CONNECTED,
        n8n_triggered=n8n_triggered,
        message=message,
    )
