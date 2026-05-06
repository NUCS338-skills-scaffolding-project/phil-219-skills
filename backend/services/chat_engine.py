"""Conversation orchestration: skill detection, confirmation, and dispatch.

State machine per chat:
  fresh            → detect skill → pending (ask confirmation) or candidates (show short list)
  pending          → yes → active | no → candidates (short list) | other → activate + run
  candidates       → substring match → active (no re-confirmation) | no match → re-detect
  active           → route every message to the skill
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from backend.config import FILES_DIR, MAX_PASSAGE_CHARS
from backend.services import storage
from backend.services.pdf_extract import extract_text, read_text_cache, write_text_cache
from backend.services.skill_detector import detect_skill, detect_top_skills
from backend.services.skill_registry import all_skills, get_skill
from skills.shared.llm_client import call_llm


_YES_PATTERN = re.compile(r"^(y|yes|yeah|yep|yup|sure|ok|okay|correct|right|confirm)\b", re.IGNORECASE)
_NO_PATTERN = re.compile(r"^(n|no|nope|nah|not really|incorrect|wrong)\b", re.IGNORECASE)
_RESTART_PATTERN = re.compile(
    r"^(restart|reset|stop|start over|begin again|clear|exit|quit|nevermind|never mind|forget it|go back|new)\b",
    re.IGNORECASE,
)
_CHITCHAT_PATTERN = re.compile(
    r"\b(how are you|how is your day|hows? it going|what'?s up|good (morning|afternoon|evening)|"
    r"hello|hi there|hey there|thanks|thank you|who are you|what are you|"
    r"hows? your day|how was your day|you'?re (great|awesome|helpful|amazing)|"
    r"how'?s everything|how have you been|what are you up to)\b",
    re.IGNORECASE,
)

# These skills are triggered by the system based on conversation signals —
# never shown to the student as options they manually pick.
META_SKILLS = {"prompt-reflection", "affirm-progress", "summarize-progress"}

# Student-facing descriptions — written from the student's perspective,
# not the tutor's. Shown in skill lists presented to the user.
STUDENT_SKILL_DESCRIPTIONS: Dict[str, str] = {
    "passage-identification": (
        "Not sure where in the text your confusion is coming from? "
        "I'll help you find the exact passage."
    ),
    "key-idea": (
        "Struggling to pin down what a passage is actually saying? "
        "I'll guide you to the main idea in your own words."
    ),
    "evidence-interpretation": (
        "Have a quote but not sure how it supports your argument? "
        "I'll help you work out the connection yourself."
    ),
    "assumption-surfacing": (
        "Think you might be making a logical leap in your argument? "
        "I'll help you identify and address it."
    ),
    "counterview-consideration": (
        "Have an interpretation but want to stress-test it? "
        "I'll prompt you to think through other possible readings."
    ),
    "summarize-progress": (
        "Feeling lost after a long conversation? I'll give you a clear picture "
        "of what you've figured out, what's still open, and where to go next."
    ),
    "prompt-reflection": (
        "Feel like you've made progress? I'll help you look back at how your "
        "thinking has shifted and what you've figured out."
    ),
    "affirm-progress": (
        "Made an attempt but not sure if you're on the right track? "
        "I'll tell you exactly what you got right and where to go next."
    ),
}


def _is_yes(text: str) -> bool:
    return bool(_YES_PATTERN.match(text.strip()))


def _is_no(text: str) -> bool:
    return bool(_NO_PATTERN.match(text.strip()))


def _is_restart(text: str) -> bool:
    return bool(_RESTART_PATTERN.match(text.strip()))


def _is_chitchat(text: str) -> bool:
    return bool(_CHITCHAT_PATTERN.search(text.strip()))


def _chitchat_response(message: str) -> str:
    system = (
        "You are a warm, witty teaching assistant for a philosophy course on existentialism. "
        "Respond to casual conversation in a friendly, professional tone with occasional dry humor — "
        "think the kind of TA who actually enjoys office hours. "
        "Keep it short: 1-3 sentences max. "
        "After your response, naturally redirect the student back to coursework "
        "with something like 'Anyway, what can I help you with today?' or similar. "
        "Do not introduce yourself as an AI."
    )
    try:
        raw = call_llm(system, [{"role": "user", "content": message}])
        return raw or "Ha — good question. Anyway, what can I help you with today?"
    except Exception:
        return "Ha — I appreciate the check-in! What can I help you with today?"


# ---------- file helpers (unchanged) ----------

def _file_text(file_id: str, label: Optional[str] = None, disk_name: Optional[str] = None) -> str:
    text_path = os.path.join(FILES_DIR, f"{file_id}.txt")
    text = read_text_cache(text_path) or ""
    if not text and disk_name:
        raw_path = os.path.join(FILES_DIR, disk_name)
        if os.path.isfile(raw_path):
            text = extract_text(raw_path) or ""
            if text:
                write_text_cache(text_path, text)
    if not text:
        return ""
    return f"=== {label or file_id} ===\n" + text


def _refresh_has_text_flags(chat_id: str) -> None:
    chat = storage.get_chat(chat_id)
    if not chat:
        return
    for f in chat.get("files", []):
        if f.get("has_text"):
            continue
        cached = read_text_cache(os.path.join(FILES_DIR, f"{f['id']}.txt"))
        if cached:
            storage.update_chat_file(chat_id, f["id"], has_text=True)
    for gf_id in chat.get("folder_pins", []):
        gmeta = storage.get_folder_file(gf_id)
        if not gmeta or gmeta.get("has_text"):
            continue
        cached = read_text_cache(os.path.join(FILES_DIR, f"{gf_id}.txt"))
        if cached:
            storage.update_folder_file(gf_id, has_text=True)


def _build_passage_context(chat: Dict[str, Any], message_file_ids: List[str]) -> str:
    pieces: List[str] = []
    seen: set = set()
    chat_files = {f["id"]: f for f in chat.get("files", [])}

    def add(fid: str, meta: Dict[str, Any]) -> None:
        if fid in seen:
            return
        chunk = _file_text(fid, meta.get("label") or meta.get("filename"), meta.get("disk_name"))
        if chunk:
            pieces.append(chunk)
            seen.add(fid)

    for fid in message_file_ids:
        meta = chat_files.get(fid)
        if meta:
            add(fid, meta)
    for fid, meta in chat_files.items():
        add(fid, meta)
    for gf_id in chat.get("folder_pins", []):
        meta = storage.get_folder_file(gf_id)
        if meta:
            add(gf_id, meta)

    blob = "\n\n".join(pieces)
    if len(blob) > MAX_PASSAGE_CHARS:
        blob = blob[:MAX_PASSAGE_CHARS] + "\n\n[...truncated...]"
    return blob


def _attached_file_summary(chat: Dict[str, Any]) -> str:
    items: List[str] = []
    for f in chat.get("files", []):
        flag = "" if f.get("has_text") else " (text not extractable — likely scanned/image PDF)"
        items.append(f"- {f.get('label') or f.get('filename')}{flag}")
    for gf_id in chat.get("folder_pins", []):
        meta = storage.get_folder_file(gf_id)
        if not meta:
            continue
        flag = "" if meta.get("has_text") else " (text not extractable)"
        items.append(f"- {meta.get('label') or meta.get('filename')} [pinned from Shared Folder]{flag}")
    return "\n".join(items)


def _resolve_passage_context(chat_id: str, message_file_ids: List[str]) -> str:
    chat = storage.get_chat(chat_id) or {}
    body = _build_passage_context(chat, message_file_ids)
    _refresh_has_text_flags(chat_id)
    chat = storage.get_chat(chat_id) or chat
    summary = _attached_file_summary(chat)
    parts: List[str] = []
    if summary:
        parts.append(
            "Documents the student has uploaded for this chat (refer to them "
            "by their labels):\n" + summary
        )
    if body:
        parts.append(body)
    return "\n\n".join(parts)


def _conversation_for_skill(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for m in messages:
        role = m.get("role")
        if role == "user":
            out.append({"role": "student", "content": m.get("content", "")})
        elif role == "assistant":
            out.append({"role": "tutor", "content": m.get("content", "")})
    return out


# ---------- skill dispatch ----------

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
        return f"I hit an error while running the teaching skill: {type(exc).__name__}: {exc}"


# ---------- prompt builders ----------

def _confirmation_prompt(skill_id: str) -> str:
    skill = get_skill(skill_id)
    name = skill.name if skill else skill_id
    return (
        f"It looks like you could use **{name}**. Does that sound right? "
        "(Reply *yes* to begin, or *no* and I'll suggest a few other options.)"
    )


def _student_description(skill_id: str, skill_name: str) -> str:
    return STUDENT_SKILL_DESCRIPTIONS.get(skill_id, f"I can help you with {skill_name}.")


def _candidates_prompt(candidate_ids: List[str]) -> str:
    lines = []
    for sid in candidate_ids:
        if sid in META_SKILLS:
            continue
        skill = get_skill(sid)
        if skill:
            lines.append(f"- **{skill.name}**: {_student_description(sid, skill.name)}")
    if not lines:
        return _full_skills_prompt()
    options = "\n".join(lines)
    return (
        "Here are a few options that might fit what you're working on:\n\n"
        f"{options}\n\n"
        "Just reply with any word from the skill name and I'll start right away."
    )


def _full_skills_prompt() -> str:
    lines = [
        f"- **{s.name}**: {_student_description(s.id, s.name)}"
        for s in all_skills()
        if s.id not in META_SKILLS
    ]
    return (
        "Here's everything I can help with — just reply with any word from the skill name "
        "and I'll get started:\n\n"
        + ("\n".join(lines) or "(no skills loaded)")
    )


def _all_skill_ids() -> List[str]:
    return [s.id for s in all_skills() if s.id not in META_SKILLS]


# ---------- candidate matching ----------

def _match_from_candidates(response: str, candidate_ids: List[str]) -> Optional[str]:
    """Return the candidate whose name/id best matches words in the student's response.

    Any word in the response that appears as a substring of a skill's name or id
    counts as a hit. The candidate with the most hits wins. Ties go to the
    candidate that appears first in the list (i.e. highest ranked).
    """
    words = [w for w in re.split(r"\W+", response.lower()) if len(w) >= 2]
    if not words:
        return None

    best_id: Optional[str] = None
    best_score = 0

    for sid in candidate_ids:
        skill = get_skill(sid)
        if not skill:
            continue
        haystack = (skill.name + " " + sid).lower()
        score = sum(1 for w in words if w in haystack)
        if score > best_score:
            best_score = score
            best_id = sid

    return best_id if best_score > 0 else None


# ---------- main handler ----------

def handle_user_message(
    chat_id: str,
    content: str,
    file_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    file_ids = file_ids or []

    chat = storage.get_chat(chat_id)
    if not chat:
        raise ValueError(f"Chat {chat_id} not found")

    user_msg = storage.append_message(chat_id, "user", content, file_ids)
    chat = storage.get_chat(chat_id) or chat

    pending = chat.get("pending_skill")
    active = chat.get("active_skill")
    candidates: Optional[List[str]] = chat.get("skill_candidates")

    assistant_text: str
    state_change: Dict[str, Any] = {}

    # ── Restart / stop — clear all state and greet ─────────────────────────
    if _is_restart(content):
        storage.update_chat(
            chat_id,
            active_skill=None,
            pending_skill=None,
            skill_candidates=None,
        )
        assistant_text = "Of course! How can I help you today?"
        assistant_msg = storage.append_message(chat_id, "assistant", assistant_text)
        chat = storage.get_chat(chat_id) or chat
        return {
            "user_message": user_msg,
            "assistant_message": assistant_msg,
            "chat": {
                "id": chat["id"],
                "title": chat.get("title"),
                "active_skill": None,
                "pending_skill": None,
                "skill_candidates": None,
            },
            "state_change": {"active_skill": None, "pending_skill": None, "skill_candidates": None},
        }

    # ── Chitchat — respond naturally regardless of session state ───────────
    if _is_chitchat(content):
        assistant_text = _chitchat_response(content)
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
                "skill_candidates": chat.get("skill_candidates"),
            },
            "state_change": {},
        }

    # ── Branch 1: student is choosing from a short candidate list ──────────
    if candidates:
        matched = _match_from_candidates(content, candidates)
        if matched:
            # Activate immediately — no re-confirmation
            storage.update_chat(chat_id, active_skill=matched, skill_candidates=None, pending_skill=None)
            history_excl = chat.get("messages", [])[:-1]
            last_msg = _last_substantive_student_message(history_excl) or content
            passage_context = _resolve_passage_context(chat_id, file_ids)
            assistant_text = _invoke_skill(matched, last_msg, history_excl, passage_context)
            state_change = {"active_skill": matched, "skill_candidates": None, "pending_skill": None}
        else:
            # No match — clear candidates and re-detect from scratch
            storage.update_chat(chat_id, skill_candidates=None, pending_skill=None)
            history_for_detector = [
                {"role": m["role"], "content": m["content"]}
                for m in chat.get("messages", [])[:-1]
            ]
            detected = detect_skill(content, history_for_detector)
            if detected:
                storage.update_chat(chat_id, pending_skill=detected)
                assistant_text = _confirmation_prompt(detected)
                state_change = {"pending_skill": detected, "skill_candidates": None}
            else:
                top = detect_top_skills(content, history_for_detector, n=3)
                fallback = top or _all_skill_ids()
                storage.update_chat(chat_id, skill_candidates=fallback)
                assistant_text = _candidates_prompt(top) if top else _full_skills_prompt()
                state_change = {"skill_candidates": fallback}

    # ── Branch 2: waiting for yes/no on a pending skill ────────────────────
    elif pending:
        if _is_yes(content):
            storage.update_chat(chat_id, active_skill=pending, pending_skill=None, skill_candidates=None)
            history_excl = chat.get("messages", [])[:-1]
            last_msg = _last_substantive_student_message(history_excl) or content
            passage_context = _resolve_passage_context(chat_id, file_ids)
            assistant_text = _invoke_skill(pending, last_msg, history_excl, passage_context)
            state_change = {"active_skill": pending, "pending_skill": None}

        elif _is_no(content):
            # Student rejected the suggestion — show a ranked short list of alternatives
            storage.update_chat(chat_id, pending_skill=None, skill_candidates=None)
            history_for_detector = [
                {"role": m["role"], "content": m["content"]}
                for m in chat.get("messages", [])[:-1]
            ]
            top = detect_top_skills(content, history_for_detector, n=3, exclude=pending)
            fallback = top or _all_skill_ids()
            storage.update_chat(chat_id, skill_candidates=fallback)
            assistant_text = "No problem. " + (_candidates_prompt(top) if top else _full_skills_prompt())
            state_change = {"pending_skill": None, "skill_candidates": fallback}

        else:
            # Treat as implicit yes — activate and run with this new message
            storage.update_chat(chat_id, active_skill=pending, pending_skill=None, skill_candidates=None)
            history_excl = chat.get("messages", [])[:-1]
            passage_context = _resolve_passage_context(chat_id, file_ids)
            assistant_text = _invoke_skill(pending, content, history_excl, passage_context)
            state_change = {"active_skill": pending, "pending_skill": None}

    # ── Branch 3: skill already active ─────────────────────────────────────
    elif active:
        history_excl = chat.get("messages", [])[:-1]
        passage_context = _resolve_passage_context(chat_id, file_ids)
        assistant_text = _invoke_skill(active, content, history_excl, passage_context)

    # ── Branch 4: fresh message, no state ──────────────────────────────────
    else:
        history_for_detector = [
            {"role": m["role"], "content": m["content"]}
            for m in chat.get("messages", [])[:-1]
        ]
        detected = detect_skill(content, history_for_detector)
        if detected:
            storage.update_chat(chat_id, pending_skill=detected)
            assistant_text = _confirmation_prompt(detected)
            state_change = {"pending_skill": detected}
        else:
            top = detect_top_skills(content, history_for_detector, n=3)
            fallback = top or _all_skill_ids()
            storage.update_chat(chat_id, skill_candidates=fallback)
            assistant_text = _candidates_prompt(top) if top else _full_skills_prompt()
            state_change = {"skill_candidates": fallback}

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
            "skill_candidates": chat.get("skill_candidates"),
        },
        "state_change": state_change,
    }


def _last_substantive_student_message(messages: List[Dict[str, Any]]) -> Optional[str]:
    for m in reversed(messages):
        if m.get("role") != "user":
            continue
        content = m.get("content", "")
        if _is_yes(content) or _is_no(content):
            continue
        return content
    return None
