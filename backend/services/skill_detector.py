"""Two-stage skill detection: keyword heuristics first, then an LLM
classifier fallback. Returns the matched skill id (folder name).
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple

from skills.shared.llm_client import call_llm

from backend.services.skill_registry import all_skills, get_skill


SKILL_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "passage-identification": {
        "phrases": [
            "where does",
            "where in the text",
            "find the passage",
            "find a passage",
            "which passage",
            "what passage",
            "section about",
            "what does it say about",
            "where can i find",
            "i can't find",
            "i cannot find",
            "what part of the text",
            "i don't get",
            "i do not get",
            "i'm confused about",
            "i am confused about",
            "what does this mean",
            "what does that mean",
            "what does the author mean",
        ],
        "words": ["passage", "quote", "aphorism", "section"],
    },
    "key-idea": {
        "phrases": [
            "main idea",
            "central claim",
            "central idea",
            "main point",
            "main argument",
            "what is this about",
            "what is this passage about",
            "what's this about",
            "summarize",
            "summary",
            "thesis",
            "what is the author saying",
            "overall point",
            "gist",
            "in a nutshell",
        ],
        "words": ["main", "thesis", "summarize"],
    },
    "evidence-interpretation": {
        "phrases": [
            "supports my claim",
            "supports the claim",
            "shows that",
            "this proves",
            "this evidence",
            "the evidence shows",
            "this quote shows",
            "this quote proves",
            "this quote demonstrates",
            "back up my argument",
            "back up my claim",
            "this passage supports",
            "use this as evidence",
        ],
        "words": ["evidence", "supports", "proves", "demonstrates"],
    },
    "assumption-surfacing": {
        "phrases": [
            "therefore",
            "so this means",
            "which means that",
            "this means that",
            "it follows that",
            "thus the author",
            "so the author is saying",
            "this clearly shows",
            "obviously the author",
            "i'm arguing that",
            "i am arguing that",
            "my argument is",
        ],
        "words": ["therefore", "thus", "obviously", "clearly"],
    },
    "counterview-consideration": {
        "phrases": [
            "i think",
            "i believe",
            "my interpretation",
            "in my opinion",
            "i would argue",
            "i'd argue",
            "my reading is",
            "i interpret",
            "from my perspective",
            "i feel like",
            "is my interpretation right",
            "am i interpreting this correctly",
            "is this a correct reading",
        ],
        "words": ["interpretation", "perspective", "viewpoint"],
    },
}


def _score(text: str, bag: Dict[str, List[str]]) -> int:
    text_lower = text.lower()
    score = 0
    for phrase in bag.get("phrases", []):
        if phrase in text_lower:
            score += 3
    for word in bag.get("words", []):
        if re.search(rf"\b{re.escape(word)}\b", text_lower):
            score += 1
    return score


def _keyword_scores(message: str) -> List[Tuple[str, int]]:
    """Return all skills sorted by keyword score descending."""
    scored: List[Tuple[str, int]] = []
    for skill in all_skills():
        bag = SKILL_KEYWORDS.get(skill.id, {})
        scored.append((skill.id, _score(message, bag)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def _llm_classify(message: str, history: List[Dict[str, str]]) -> Optional[str]:
    """Ask the LLM to pick the single best-fitting skill. Returns a skill id or None."""
    skills = all_skills()
    if not skills:
        return None
    catalog = "\n".join(
        f"- id: {s.id} | name: {s.name} | description: {s.short_description()}"
        for s in skills
    )
    system = (
        "You classify a student's message into one of the available "
        "Socratic teaching skills. Read the message and pick the single "
        "best-matching skill id from the catalog. Reply with strict JSON "
        'of the form {"skill_id": "<id>"} where <id> is exactly one of '
        "the listed ids, or null if none clearly fits.\n\nCatalog:\n"
        f"{catalog}"
    )
    convo = [
        {"role": "user" if t.get("role") == "user" else "assistant", "content": t.get("content", "")}
        for t in history[-6:]
    ]
    convo.append({"role": "user", "content": f"Student message:\n{message}"})
    try:
        raw = call_llm(system, convo)
    except Exception:
        return None
    match = re.search(r"\{[^}]*\}", raw or "")
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    candidate = data.get("skill_id")
    return candidate if candidate and get_skill(candidate) else None


def _llm_classify_top(
    message: str,
    history: List[Dict[str, str]],
    n: int = 3,
    exclude: Optional[str] = None,
) -> List[str]:
    """Ask the LLM for the top N skill IDs ranked by fit. Returns a list (may be shorter than n)."""
    skills = [s for s in all_skills() if s.id != exclude]
    if not skills:
        return []
    catalog = "\n".join(
        f"- id: {s.id} | name: {s.name} | description: {s.short_description()}"
        for s in skills
    )
    system = (
        f"You rank a student's message against the available Socratic teaching skills. "
        f"Return the top {n} best-matching skill ids in order of fit. "
        f'Reply with strict JSON of the form {{"skill_ids": ["id1", "id2", ...]}} '
        f"using only ids from the catalog. Use fewer than {n} entries if fewer clearly fit. "
        f"Return an empty list if nothing fits.\n\nCatalog:\n{catalog}"
    )
    convo = [
        {"role": "user" if t.get("role") == "user" else "assistant", "content": t.get("content", "")}
        for t in history[-6:]
    ]
    convo.append({"role": "user", "content": f"Student message:\n{message}"})
    try:
        raw = call_llm(system, convo)
    except Exception:
        return []
    match = re.search(r"\{[^}]*\}", raw or "", re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    ids = data.get("skill_ids", [])
    return [sid for sid in ids if get_skill(sid) and sid != exclude][:n]


def detect_skill(message: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
    """Return the single best-matching skill id, or None if undetermined."""
    history = history or []
    scored = _keyword_scores(message)
    if not scored:
        return _llm_classify(message, history)

    top_id, top_score = scored[0]
    runner = scored[1][1] if len(scored) > 1 else 0

    KEYWORD_THRESHOLD = 3
    KEYWORD_MARGIN = 2

    if top_score >= KEYWORD_THRESHOLD and (top_score - runner) >= KEYWORD_MARGIN:
        return top_id

    return _llm_classify(message, history)


def detect_top_skills(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    n: int = 3,
    exclude: Optional[str] = None,
) -> List[str]:
    """Return up to n skill IDs ranked by how well they fit the message.

    Combines keyword scores with an LLM ranking pass. The result is
    deduplicated and excludes `exclude` (e.g. a skill the student just rejected).
    """
    history = history or []
    scored = _keyword_scores(message)

    # Take keyword candidates with any positive score
    kw_candidates = [sid for sid, sc in scored if sc > 0 and sid != exclude]

    # Always run the LLM ranker so confidence ordering is better
    llm_candidates = _llm_classify_top(message, history, n=n, exclude=exclude)

    # Merge: LLM order wins, fill remaining slots from keyword list
    seen: set = set()
    merged: List[str] = []
    for sid in llm_candidates + kw_candidates:
        if sid not in seen:
            seen.add(sid)
            merged.append(sid)
        if len(merged) == n:
            break

    return merged
