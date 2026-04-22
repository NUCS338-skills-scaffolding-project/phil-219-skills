---
skill_id: "passage-identification"
name: "Passage Identification"
skill_type: "instructional"
tags: ["identifying", "reading"]
python_entry: logic.py
---

# Skill Name

Passage Identification

## Description

Prompts students to pinpoint the exact sentence or section causing confusion before any further discussion. The tutor will make note of the section that the student is confused about. 

## When to Trigger
- Student mentions that they are confused or doesn’t understand a concept
- Student is not asking about a passage that has already been shared through the passage identification skill

## Tutor Stance
- Tutor will identify the misunderstanding or confusion the student holds, and find the area of the text corresponding to that idea
- Tutor will share a reasonably sized(1-3 paragraphs) chunk of the text with the student for them to look at. If a larger portion of the text is required, or the student shows a significant lack of understanding, the tutor will point towards a larger portion of the text but not share it.
- Tutor will 

## Flow
### Step 1 — Questioning
Identify the concept that the student is confused about, and the area of the text where that idea is introduced/explained

### Step 2 — Step Title
Pick the most informational and clear passage in the relevant section of the text and share it with the student

## Safe Output Types
The passage the student is confused about is the output. It is a string. 
“You are currently confused by [passage].” 

## Must Avoid
What the tutor must NEVER do.

Tutor must not begin to explain the passage that the user is confused by. The tutor must not provide direct insight on the reading. The tutor must not do anything besides make note of the section causing confusion and returning the confused passage to the student. 

## Example Exchange
> **Student:** I am confused about when Nietzsche says “God is dead,” what does that mean?
>
> **Tutor:** "Nietzsche's proclamation that “God is dead” is from Aphorism 125. Here is the passage: {text}. Let me know if there are any parts still confusing you after you read it through”
