"""/api/chats — list, create, fetch, rename, delete chats and toggle folder pins."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services import storage

router = APIRouter(prefix="/api/chats", tags=["chats"])


class CreateChatBody(BaseModel):
    title: Optional[str] = None


class PatchChatBody(BaseModel):
    title: Optional[str] = None
    folder_pins: Optional[List[str]] = None
    active_skill: Optional[str] = None


@router.get("")
def list_chats():
    return {"chats": storage.list_chats()}


@router.post("")
def create_chat(body: CreateChatBody):
    chat = storage.create_chat(body.title or "New chat")
    return chat


@router.get("/{chat_id}")
def get_chat(chat_id: str):
    chat = storage.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.patch("/{chat_id}")
def patch_chat(chat_id: str, body: PatchChatBody):
    fields = {k: v for k, v in body.dict(exclude_unset=True).items() if v is not None}
    if not fields:
        chat = storage.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        return chat
    chat = storage.update_chat(chat_id, **fields)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("/{chat_id}")
def delete_chat(chat_id: str):
    if not storage.delete_chat(chat_id):
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"ok": True}
