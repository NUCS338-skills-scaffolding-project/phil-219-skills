"""Two-stage skill detection: keyword heuristics first, then an LLM
classifier fallback. Returns the matched skill id (folder name).
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple

from skills.shared.llm_client import call_llm

from backend.services.skill_registry import all_skills, get_skill


# Curated keyword bags. Phrases are matched as substrings (case-insensitive)
# and weighted; single-word tokens are matched as whole words with a lower
# weight to avoid false positives.
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


def _keyword_detect(message: str) -> Tuple[Optional[str], int, int]:
    """Return (best_skill_id, top_score, runner_up_score)."""
    scored: List[Tuple[str, int]] = []
    for skill in all_skills():
        bag = SKILL_KEYWORDS.get(skill.id, {})
        scored.append((skill.id, _score(message, bag)))
    scored.sort(key=lambda x: x[1], reverse=True)
    if not scored:
        return None, 0, 0
    top_id, top_score = scored[0]
    runner = scored[1][1] if len(scored) > 1 else 0
    return top_id, top_score, runner


def _llm_classify(message: str, history: List[Dict[str, str]]) -> Optional[str]:
    """Ask the LLM to pick the best-fitting skill. Returns a folder id or None."""
    skills = all_skills()
    if not skills:
        return None
    catalog_lines = []
    for s in skills:
        catalog_lines.append(f"- id: {s.id} | name: {s.name} | description: {s.short_description()}")
    catalog = "\n".join(catalog_lines)

    system = (
        "You classify a student's message into one of the available "
        "Socratic teaching skills. Read the message and pick the single "
        "best-matching skill id from the catalog. Reply with strict JSON "
        'of the form {"skill_id": "<id>"} where <id> is exactly one of '
        "the listed ids, or null if none clearly fits.\n\nCatalog:\n"
        f"{catalog}"
    )

    convo = []
    for turn in history[-6:]:
        role = "user" if turn.get("role") == "user" else "assistant"
        convo.append({"role": role, "content": turn.get("content", "")})
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
    if candidate and get_skill(candidate):
        return candidate
    return None


def detect_skill(message: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
    """Return the best-matching skill id, or None if undetermined."""
    history = history or []
    top_id, top_score, runner = _keyword_detect(message)

    KEYWORD_THRESHOLD = 3
    KEYWORD_MARGIN = 2

    if top_id and top_score >= KEYWORD_THRESHOLD and (top_score - runner) >= KEYWORD_MARGIN:
        return top_id

    return _llm_classify(message, history)
