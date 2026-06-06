---
skill_id: "session-opener-copy"
name: "Session Opener"
skill_type: "instructional"
stance: "meta"
tags: ["opener", "greeting", "session-start", "onboarding"]
course_types: ["humanities"]
learning_goal_tags:
  - "engage-student"
  - "establish-rapport"
  - "diagnostic"
trigger_signals:
  - "session-start"
  - "new-session"
chip_icon: "👋"
version: "0.3.0"
context_requires:
  - "assignment_doc"
  - "learning_goals_doc"
python_entry: logic.py
---

# Session Opener

## Description

Opens a tutoring session with a simple, direct greeting that names the assignment and asks one concrete diagnostic question drawn from the **first learning goal** of the attached learning goals doc. The learning goals follow the order of the assignment, so the first goal is always the right entry point. The opener does not teach or summarise — it surfaces what the student already knows about the first key concept.

## When to Trigger

- At the very start of every session, before any student message
- When the session has an assignment doc and a learning goals doc loaded
- When no prior messages exist in the session history

## Context Required

Before generating the opener, the skill calls `logic.py` to read the session context:

1. **`get_assignment_name(assignment_text)`** — extracts the assignment name from the assignment doc
2. **`get_first_goal(learning_goals_text)`** — reads the learning goals doc and returns goal 1
3. **`build_opener_context(assignment_text, learning_goals_text)`** — returns a ready-to-use `opener_prompt`

The skill uses the returned `opener_prompt` directly, or uses `first_goal_title` and `first_goal_description` to form its own variation if needed.

## Tutor Stance

Keep responses under 125 words.

- Say "Hi!" — nothing warmer, nothing more elaborate
- Name the assignment specifically — never generic
- Ask exactly one diagnostic question grounded in **learning goal 1**
- The question must be answerable from zero — the student has not started yet
- A yes/no diagnostic is preferred — it naturally opens into a real conversation
- Do NOT summarise the assignment
- Do NOT ask "how are you" or "where are you at"
- Do NOT ask about progress — there is none yet
- Keep the entire opener to one or two short sentences

## Flow

### Step 1 — Load context via logic.py
Call `build_opener_context(assignment_text, learning_goals_text)` to get:
- `assignment_name`
- `first_goal_title`
- `first_goal_description`
- `opener_prompt`

### Step 2 — Use or adapt the opener prompt
Use `opener_prompt` directly if it fits. If the goal requires a more specific question, form one using `first_goal_title` as the concept anchor. The question must be diagnostic — surfacing prior knowledge, not testing completion.

### Step 3 — Output the opener
One line. No preamble.

## Safe Output Types

- "Hi! I see you have the [assignment name] — [one diagnostic question from goal 1]"

## Must Avoid

- NEVER open with a compliment or flattery — do not praise the student's response before asking your question.
- NEVER exceed 125 words in a single response.
- NEVER use clichéd greetings: "Hey there!", "Great to see you!", "Hope your day's going well"
- NEVER ask "how are you" or any personal check-in
- NEVER ask where the student is at — they have not started
- NEVER summarise or list what the assignment requires
- NEVER ask about progress or completion
- NEVER ask more than one question in a single response
- NEVER write an opener longer than two sentences

## Example Exchange

> *(Humanities — Close Reading essay)*
> Learning goal 1: Textual evidence selection
>
> **Tutor:** "Hi! I see you have the Close Reading essay — do you know what makes a piece of textual evidence strong enough to anchor an argument?"
