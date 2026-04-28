"""JSON-on-disk persistence for chats and the global folder.

Uses an in-memory cache plus atomic write-through to keep things simple
and safe at this scale. All public functions are synchronous and return
plain dicts/lists that callers may mutate after re-fetching.
"""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.config import CHATS_PATH, FOLDER_PATH, ensure_data_dirs

_lock = threading.RLock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write(path: str, data: Dict[str, Any]) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def _load(path: str, default: Dict[str, Any]) -> Dict[str, Any]:
    if not os.path.exists(path):
        return json.loads(json.dumps(default))
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return json.loads(json.dumps(default))


def _load_chats() -> Dict[str, Any]:
    return _load(CHATS_PATH, {"chats": []})


def _load_folder() -> Dict[str, Any]:
    return _load(FOLDER_PATH, {"files": []})


def _save_chats(state: Dict[str, Any]) -> None:
    _atomic_write(CHATS_PATH, state)


def _save_folder(state: Dict[str, Any]) -> None:
    _atomic_write(FOLDER_PATH, state)


def init_storage() -> None:
    ensure_data_dirs()
    if not os.path.exists(CHATS_PATH):
        _save_chats({"chats": []})
    if not os.path.exists(FOLDER_PATH):
        _save_folder({"files": []})


# ---------- Chats ----------

def list_chats() -> List[Dict[str, Any]]:
    with _lock:
        chats = _load_chats()["chats"]
        return [
            {
                "id": c["id"],
                "title": c.get("title", "New chat"),
                "created_at": c.get("created_at"),
                "updated_at": c.get("updated_at", c.get("created_at")),
                "active_skill": c.get("active_skill"),
                "pending_skill": c.get("pending_skill"),
                "message_count": len(c.get("messages", [])),
            }
            for c in sorted(
                chats,
                key=lambda c: c.get("updated_at") or c.get("created_at") or "",
                reverse=True,
            )
        ]


def get_chat(chat_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        for c in _load_chats()["chats"]:
            if c["id"] == chat_id:
                return c
        return None


def create_chat(title: str = "New chat") -> Dict[str, Any]:
    with _lock:
        state = _load_chats()
        chat = {
            "id": f"chat_{uuid.uuid4().hex[:10]}",
            "title": title,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "active_skill": None,
            "pending_skill": None,
            "messages": [],
            "files": [],
            "folder_pins": [],
        }
        state["chats"].append(chat)
        _save_chats(state)
        return chat


def delete_chat(chat_id: str) -> bool:
    with _lock:
        state = _load_chats()
        before = len(state["chats"])
        state["chats"] = [c for c in state["chats"] if c["id"] != chat_id]
        if len(state["chats"]) == before:
            return False
        _save_chats(state)
        return True


def update_chat(chat_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
    """Patch top-level fields on a chat (title, active_skill, pending_skill, folder_pins)."""
    allowed = {"title", "active_skill", "pending_skill", "folder_pins"}
    with _lock:
        state = _load_chats()
        for c in state["chats"]:
            if c["id"] == chat_id:
                for k, v in fields.items():
                    if k in allowed:
                        c[k] = v
                c["updated_at"] = _now_iso()
                _save_chats(state)
                return c
        return None


def append_message(chat_id: str, role: str, content: str, file_ids: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    with _lock:
        state = _load_chats()
        for c in state["chats"]:
            if c["id"] == chat_id:
                msg = {
                    "id": f"msg_{uuid.uuid4().hex[:10]}",
                    "role": role,
                    "content": content,
                    "file_ids": file_ids or [],
                    "created_at": _now_iso(),
                }
                c.setdefault("messages", []).append(msg)
                c["updated_at"] = _now_iso()
                if role == "user" and (not c.get("title") or c["title"] == "New chat"):
                    snippet = content.strip().splitlines()[0] if content.strip() else ""
                    if snippet:
                        c["title"] = snippet[:60]
                _save_chats(state)
                return msg
        return None


def add_chat_file(chat_id: str, file_meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    with _lock:
        state = _load_chats()
        for c in state["chats"]:
            if c["id"] == chat_id:
                c.setdefault("files", []).append(file_meta)
                c["updated_at"] = _now_iso()
                _save_chats(state)
                return file_meta
        return None


def update_chat_file(chat_id: str, file_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
    allowed = {"label", "has_text"}
    with _lock:
        state = _load_chats()
        for c in state["chats"]:
            if c["id"] != chat_id:
                continue
            for f in c.get("files", []):
                if f["id"] == file_id:
                    for k, v in fields.items():
                        if k in allowed:
                            f[k] = v
                    c["updated_at"] = _now_iso()
                    _save_chats(state)
                    return f
        return None


def remove_chat_file(chat_id: str, file_id: str) -> bool:
    with _lock:
        state = _load_chats()
        for c in state["chats"]:
            if c["id"] == chat_id:
                before = len(c.get("files", []))
                c["files"] = [f for f in c.get("files", []) if f["id"] != file_id]
                if len(c["files"]) == before:
                    return False
                c["updated_at"] = _now_iso()
                _save_chats(state)
                return True
        return False


def get_chat_file(chat_id: str, file_id: str) -> Optional[Dict[str, Any]]:
    chat = get_chat(chat_id)
    if not chat:
        return None
    for f in chat.get("files", []):
        if f["id"] == file_id:
            return f
    return None


# ---------- Folder (global) ----------

def list_folder_files() -> List[Dict[str, Any]]:
    with _lock:
        return list(_load_folder().get("files", []))


def add_folder_file(file_meta: Dict[str, Any]) -> Dict[str, Any]:
    with _lock:
        state = _load_folder()
        state.setdefault("files", []).append(file_meta)
        _save_folder(state)
        return file_meta


def remove_folder_file(file_id: str) -> bool:
    with _lock:
        state = _load_folder()
        before = len(state.get("files", []))
        state["files"] = [f for f in state.get("files", []) if f["id"] != file_id]
        if len(state["files"]) == before:
            return False
        _save_folder(state)
        return True


def get_folder_file(file_id: str) -> Optional[Dict[str, Any]]:
    for f in list_folder_files():
        if f["id"] == file_id:
            return f
    return None


def update_folder_file(file_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
    allowed = {"label", "has_text"}
    with _lock:
        state = _load_folder()
        for f in state.get("files", []):
            if f["id"] == file_id:
                for k, v in fields.items():
                    if k in allowed:
                        f[k] = v
                _save_folder(state)
                return f
        return None
