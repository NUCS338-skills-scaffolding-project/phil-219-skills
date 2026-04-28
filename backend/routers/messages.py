"""POST /api/chats/{chat_id}/messages — send a user turn, get an assistant reply."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services import chat_engine, storage

router = APIRouter(prefix="/api/chats", tags=["messages"])


class SendMessageBody(BaseModel):
    content: str
    file_ids: Optional[List[str]] = None


@router.post("/{chat_id}/messages")
def send_message(chat_id: str, body: SendMessageBody):
    if not storage.get_chat(chat_id):
        raise HTTPException(status_code=404, detail="Chat not found")
    if not body.content or not body.content.strip():
        raise HTTPException(status_code=400, detail="Message content is required")
    try:
        result = chat_engine.handle_user_message(
            chat_id, body.content, body.file_ids or []
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return result
