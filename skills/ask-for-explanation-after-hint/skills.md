---
skill_id: "counter-example"          # ≤ 18 chars, kebab-case
name: "Counter-Example"              # human-readable, no trailing "Skill"
skill_type: "instructional"
stance: "socratic"                   # NEW — see Step 5
tags: ["essay", "argument", "kant"]
course_types: ["humanities"]         # NEW — subset of ["cs", "humanities"]
learning_goal_tags:                  # NEW — see Step 6
  - "construct-arguments"
  - "engage-objections"
trigger_signals:                     # NEW — optional; helps the orchestrator route
  - "student-defending-first-position"
chip_icon: "🔁"                      # OPTIONAL — single emoji for the UI
version: "0.1.0"                     # OPTIONAL — semver, defaults to "0.1.0"
# python_entry omitted — this skill has no logic.py
---

# Counter-Example

## Description
What does this skill do? Keep it to 2-3 sentences.

## When to Trigger
- Trigger condition 1
- Trigger condition 2

## Tutor Stance
Non-negotiable rules for how the tutor should behave when this skill is active.

## Flow
### Step 1 — Surface the claim
Describe what the tutor does.

### Step 2 — Offer a probe
Describe what the tutor does.

## Safe Output Types
What the tutor IS allowed to produce.

## Must Avoid
What the tutor must NEVER do.

## Example Exchange
> **Student:** "Example student message"
>
> **Tutor:** "Example tutor response"