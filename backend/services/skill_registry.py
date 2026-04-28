"""Auto-discovery and dynamic loading of skills from the `skills/` folder.

Each skill folder must contain `skills.md` (with YAML frontmatter) and
`logic.py` exposing a `run(input: dict) -> str` function.

The folder name is used as the canonical skill id so that adding a new
skill requires no central registration.
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from typing import Any, Callable, Dict, List, Optional

from backend.config import SKILLS_DIR, SKIP_SKILL_FOLDERS, ROOT_DIR

_SKILLS: Dict[str, "Skill"] = {}


class Skill:
    def __init__(
        self,
        skill_id: str,
        name: str,
        tags: List[str],
        system_prompt: str,
        run_fn: Callable[[Dict[str, Any]], str],
        folder: str,
    ) -> None:
        self.id = skill_id
        self.name = name
        self.tags = tags
        self.system_prompt = system_prompt
        self.run_fn = run_fn
        self.folder = folder

    def short_description(self) -> str:
        """A meaningful one-paragraph summary of the skill.

        Prefers a paragraph starting with "Your skill is" (the convention
        used by the existing skills.md files), then falls back to the first
        non-boilerplate paragraph.
        """
        paragraphs = [p.strip() for p in self.system_prompt.split("\n\n") if p.strip()]
        for p in paragraphs:
            if p.lower().startswith("your skill is"):
                return p[:280]
        for p in paragraphs:
            if p.startswith("#"):
                continue
            if "you are a socratic tutor" in p.lower():
                continue
            return p[:280]
        return self.name

    def to_public(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "tags": self.tags,
            "description": self.short_description(),
        }


_QUOTE_CHARS = "\"'\u201c\u201d\u2018\u2019"


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] in _QUOTE_CHARS and value[-1] in _QUOTE_CHARS:
        return value[1:-1]
    return value


def _parse_frontmatter(md_text: str) -> Dict[str, Any]:
    """Tolerant frontmatter parser that accepts curly quotes the existing
    skills.md files use (PyYAML rejects them)."""
    if not md_text.startswith("---"):
        return {}
    parts = md_text.split("---", 2)
    if len(parts) < 3:
        return {}
    header = parts[1]
    out: Dict[str, Any] = {}
    for raw_line in header.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1]
            items = [
                _strip_quotes(item.strip())
                for item in inner.split(",")
                if item.strip()
            ]
            out[key] = items
        else:
            out[key] = _strip_quotes(value)
    return out


def _system_prompt_from_md(md_text: str) -> str:
    parts = md_text.split("---", 2)
    body = parts[2] if len(parts) >= 3 else md_text
    return body.strip()


def _import_logic(folder_path: str, module_name: str):
    logic_path = os.path.join(folder_path, "logic.py")
    if not os.path.isfile(logic_path):
        return None
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)
    spec = importlib.util.spec_from_file_location(module_name, logic_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_skills() -> Dict[str, Skill]:
    """Scan SKILLS_DIR and load every skill folder. Idempotent."""
    _SKILLS.clear()
    if not os.path.isdir(SKILLS_DIR):
        return _SKILLS

    for entry in sorted(os.listdir(SKILLS_DIR)):
        if entry in SKIP_SKILL_FOLDERS or entry.startswith("."):
            continue
        folder_path = os.path.join(SKILLS_DIR, entry)
        if not os.path.isdir(folder_path):
            continue
        md_path = os.path.join(folder_path, "skills.md")
        if not os.path.isfile(md_path):
            continue

        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        meta = _parse_frontmatter(md_text)
        name = meta.get("name") or entry.replace("-", " ").title()
        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        system_prompt = _system_prompt_from_md(md_text)

        module = _import_logic(folder_path, f"skills_runtime.{entry}")
        if module is None or not hasattr(module, "run"):
            continue

        skill = Skill(
            skill_id=entry,
            name=name,
            tags=tags,
            system_prompt=system_prompt,
            run_fn=module.run,
            folder=folder_path,
        )
        _SKILLS[entry] = skill

    return _SKILLS


def get_skill(skill_id: str) -> Optional[Skill]:
    return _SKILLS.get(skill_id)


def all_skills() -> List[Skill]:
    return list(_SKILLS.values())
