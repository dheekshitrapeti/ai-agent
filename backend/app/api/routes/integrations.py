from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_integrations():
    return [
        {"provider": "slack", "name": "Slack", "description": "Receive and summarize new Slack messages.", "status": "disconnected"},
        {"provider": "gmail", "name": "Gmail", "description": "Summarize incoming emails.", "status": "disconnected"},
        {"provider": "google_drive", "name": "Google Drive", "description": "Track newly uploaded documents.", "status": "disconnected"},
    ]
