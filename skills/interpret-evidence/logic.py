# logic.py — Evidence Interpretation skill
# Make it modular so other teams can import it

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from skills.shared.llm_client import call_llm

SKILL_DIR = os.path.dirname(__file__)


def load_system_prompt():
    """Read skills.md and return the body after the YAML frontmatter as the system prompt."""
    path = os.path.join(SKILL_DIR, "skills.md")
    with open(path, "r") as f:
        content = f.read()
    # Strip YAML frontmatter (between first and second '---')
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return content.strip()


SYSTEM_PROMPT = load_system_prompt()


def run(input):
    """
    Main entry point for the Evidence Interpretation skill.
    :param input: dict with keys: student_message, conversation_history, passage_context (optional)
    :return: Tutor response string
    """
    student_message = input.get("student_message", "")
    conversation_history = input.get("conversation_history", [])
    passage_context = input.get("passage_context", "")

    system = SYSTEM_PROMPT
    if passage_context:
        system += f"\n\nThe philosophical text being discussed:\n{passage_context}"

    # Convert conversation history to OpenAI API format
    messages = []
    for turn in conversation_history:
        role = "user" if turn["role"] == "student" else "assistant"
        messages.append({"role": role, "content": turn["content"]})
    messages.append({"role": "user", "content": student_message})

    return call_llm(system, messages)
