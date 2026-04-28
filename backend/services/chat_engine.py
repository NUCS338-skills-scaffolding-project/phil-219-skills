"""Conversation orchestration: skill detection, confirmation, and dispatch.

The engine sits between the API layer and the per-skill `logic.py`
modules. It is responsible for:
  * Routing a fresh user message through the SkillDetector.
  * Asking the student to confirm the detected skill before activating it.
  * Building `passage_context` from attached files (per-chat + pinned folder).
  * Calling the active skill's `run()` and recording the assistant reply.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.config import FILES_DIR, MAX_PASSAGE_CHARS
from backend.services import storage
from backend.services.pdf_extract import read_text_cache
from backend.services.skill_detector import detect_skill
from backend.services.skill_registry import all_skills, get_skill


_YES_PATTERN = re.compile(r"^(y|yes|yeah|yep|yup|sure|ok|okay|correct|right|confirm)\b", re.IGNORECASE)
_NO_PATTERN = re.compile(r"^(n|no|nope|nah|not really|incorrect|wrong)\b", re.IGNORECASE)


def _is_yes(text: str) -> bool:
    return bool(_YES_PATTERN.match(text.strip()))


def _is_no(text: str) -> bool:
    return bool(_NO_PATTERN.match(text.strip()))


def _file_text(file_id: str, label: Optional[str] = None) -> str:
    text_path = os.path.join(FILES_DIR, f"{file_id}.txt")
    text = read_text_cache(text_path) or ""
    if not text:
        return ""
    header = f"=== {label or file_id} ===\n"
    return header + text


def _build_passage_context(chat: Dict[str, Any], message_file_ids: List[str]) -> str:
    """Concatenate text from attached chat files and pinned folder PDFs."""
    pieces: List[str] = []
    seen: set = set()

    chat_files = {f["id"]: f for f in chat.get("files", [])}

    for fid in message_file_ids:
        if fid in seen:
            continue
        meta = chat_files.get(fid)
        if not meta:
            continue
        chunk = _file_text(fid, meta.get("label") or meta.get("filename"))
        if chunk:
            pieces.append(chunk)
            seen.add(fid)

    for fid, meta in chat_files.items():
        if fid in seen:
            continue
        chunk = _file_text(fid, meta.get("label") or meta.get("filename"))
        if chunk:
            pieces.append(chunk)
            seen.add(fid)

    for gf_id in chat.get("folder_pins", []):
        if gf_id in seen:
            continue
        meta = storage.get_folder_file(gf_id)
        if not meta:
            continue
        chunk = _file_text(gf_id, meta.get("label") or meta.get("filename"))
        if chunk:
            pieces.append(chunk)
            seen.add(gf_id)

    blob = "\n\n".join(pieces)
    if len(blob) > MAX_PASSAGE_CHARS:
        blob = blob[:MAX_PASSAGE_CHARS] + "\n\n[...truncated...]"
    return blob


def _conversation_for_skill(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Convert stored chat messages into the format skills' run() expects.

    The existing logic.py implementations expect roles `student` / `tutor`.
    """
    out: List[Dict[str, str]] = []
    for m in messages:
        role = m.get("role")
        if role == "user":
            out.append({"role": "student", "content": m.get("content", "")})
        elif role == "assistant":
            out.append({"role": "tutor", "content": m.get("content", "")})
    return out


def _invoke_skill(
    skill_id: str,
    student_message: str,
    history: List[Dict[str, Any]],
    passage_context: str,
) -> str:
    skill = get_skill(skill_id)
    if not skill:
        return (
            "I tried to activate a teaching skill, but it could not be loaded. "
            "Could you rephrase what you'd like help with?"
        )
    payload = {
        "student_message": student_message,
        "conversation_history": _conversation_for_skill(history),
        "passage_context": passage_context,
    }
    try:
        return skill.run_fn(payload)
    except Exception as exc:
        return (
            "I hit an error while running the teaching skill: "
            f"{type(exc).__name__}: {exc}"
        )


def _confirmation_prompt(skill_id: str) -> str:
    skill = get_skill(skill_id)
    name = skill.name if skill else skill_id
    return (
        f"It sounds like you may need help with **{name}**. Is that correct? "
        "(Reply *yes* to start, or *no* to pick a different focus.)"
    )


def _list_available_skills() -> str:
    lines = []
    for s in all_skills():
        lines.append(f"- **{s.name}**: {s.short_description()}")
    return "\n".join(lines) or "(no skills loaded)"


def _no_match_prompt() -> str:
    return (
        "I'm not sure which kind of help fits your message yet. "
        "Could you say a bit more about what you're working on? Here are the "
        "approaches I can take:\n\n" + _list_available_skills()
    )


def handle_user_message(
    chat_id: str,
    content: str,
    file_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Process one user message and produce one assistant reply.

    Returns a dict with the persisted user + assistant message records and
    the chat's updated state fields.
    """
    file_ids = file_ids or []

    chat = storage.get_chat(chat_id)
    if not chat:
        raise ValueError(f"Chat {chat_id} not found")

    user_msg = storage.append_message(chat_id, "user", content, file_ids)
    chat = storage.get_chat(chat_id) or chat

    pending = chat.get("pending_skill")
    active = chat.get("active_skill")

    assistant_text: str
    state_change: Dict[str, Any] = {}

    if pending:
        if _is_yes(content):
            chat = storage.update_chat(chat_id, active_skill=pending, pending_skill=None) or chat
            history_excl_current = chat.get("messages", [])[:-1]
            last_student_message = _last_substantive_student_message(history_excl_current) or content
            passage_context = _build_passage_context(chat, file_ids)
            assistant_text = _invoke_skill(
                pending,
                last_student_message,
                history_excl_current,
                passage_context,
            )
            state_change = {"active_skill": pending, "pending_skill": None}
        elif _is_no(content):
            chat = storage.update_chat(chat_id, pending_skill=None) or chat
            assistant_text = (
                "No problem — let's pick a different focus. " + _no_match_prompt()
            )
            state_change = {"pending_skill": None}
        else:
            history_excl_current = chat.get("messages", [])[:-1]
            passage_context = _build_passage_context(chat, file_ids)
            chat = storage.update_chat(chat_id, active_skill=pending, pending_skill=None) or chat
            assistant_text = _invoke_skill(
                pending,
                content,
                history_excl_current,
                passage_context,
            )
            state_change = {"active_skill": pending, "pending_skill": None}

    elif active:
        history_excl_current = chat.get("messages", [])[:-1]
        passage_context = _build_passage_context(chat, file_ids)
        assistant_text = _invoke_skill(
            active,
            content,
            history_excl_current,
            passage_context,
        )

    else:
        history_excl_current = chat.get("messages", [])[:-1]
        history_for_detector = [
            {"role": m["role"], "content": m["content"]}
            for m in history_excl_current
        ]
        detected = detect_skill(content, history_for_detector)
        if detected:
            chat = storage.update_chat(chat_id, pending_skill=detected) or chat
            assistant_text = _confirmation_prompt(detected)
            state_change = {"pending_skill": detected}
        else:
            assistant_text = _no_match_prompt()

    assistant_msg = storage.append_message(chat_id, "assistant", assistant_text)
    chat = storage.get_chat(chat_id) or chat

    return {
        "user_message": user_msg,
        "assistant_message": assistant_msg,
        "chat": {
            "id": chat["id"],
            "title": chat.get("title"),
            "active_skill": chat.get("active_skill"),
            "pending_skill": chat.get("pending_skill"),
        },
        "state_change": state_change,
    }


def _last_substantive_student_message(messages: List[Dict[str, Any]]) -> Optional[str]:
    """Find the most recent user message that wasn't a yes/no confirmation."""
    for m in reversed(messages):
        if m.get("role") != "user":
            continue
        content = m.get("content", "")
        if _is_yes(content) or _is_no(content):
            continue
        return content
    return None
