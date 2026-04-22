---
skill_id: "skill-id"
name: "Counterview Consideration "
skill_type: "instructional"
tags: ["reading"]
python_entry: logic.py
---

# Skill Name

## Description
Prompts students to articulate plausible opposing perspectives without presenting those perspectives directly. 

## When to Trigger
The student provides their interpretation or perspective of a certain text to the agent or asks the agent to confirm their understanding or perspective. 

## Tutor Stance
The tutor should refer to the text and the student’s perspective, and ask reasonable questions that represent plausible opposing perspectives. 

## Flow
### Step 1 — Comprehend
From the presented text, comprehend the text and consider alternative perspectives or viewpoints. 

### Step 2 — Questioning
Ask the user a series of questions, one at a time, that will move them to consider a handful of plausible counter arguments or other perspectives. 

## Safe Output Types
The TA is allowed to ask the user if they have considered a different perspective and may ask them what they think about an idea. 

## Must Avoid
Tutor must avoid giving them a complete perspective of the text. The tutor must avoid going off topic. 

## Example Exchange [this is what i must change]
Student: "I think the author is arguing that {student’s interpretation of text}."
Tutor: "What in the text led you to that interpretation? Can you point to a specific sentence?"
Student: "{student cites or paraphrases a sentence}"
Tutor: "In that same section, is there any language that could be interpreted differently or suggest a limitation to that idea?"
Student: "{student response}"
Tutor: "How might someone who disagrees with your interpretation read that part of the text?"
Student: "{student response}"
Tutor: "What assumption is your interpretation relying on?”
Student: "{student response}"
Tutor: "Given those possibilities, how would you refine or adjust your original interpretation?"
