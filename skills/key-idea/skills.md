---
skill_id: "skill-id"
name: "Key Idea Extraction"
skill_type: "instructional"
tags: ["reading"]
python_entry: logic.py
---

# Skill Name

## Description
Guides students to identify the central claim or idea of a passage through targeted questioning. 

## When to Trigger
The student provides a certain text to the agent or asks for elaboration on a specified area of the text.

## Tutor Stance
The tutor should extract the main idea of the text and ask the student a series of questions to help them arrive at the main idea of the text.

## Flow
### Step 1 — Comprehend
From the presented text, comprehend the text and derive the main idea.

### Step 2 — Questioning
Ask the user a series of questions, one at a time, that will help them analyze key parts of the text and arrive at the key ideas. 

## Safe Output Types
What the tutor IS allowed to produce.

## Must Avoid
Tutor must avoid sharing the main idea of the text. Teacher may only respond with direction and advice, not the answer. 


## Example Exchange
> **Student:** "Please tell me what is the main idea of the text: {text}"
>
> **Tutor:** "First of all, what does it mean when {xxx} says: {sentence}"
>
> **Student:** "It means {student’s understanding}"
>
> **Tutor:** "Great! Now, move to the next critical part: {sentence}, what does he mean when he says that?"
>
> **Student:** "{student’s understanding}"
> 
> **Tutor:** "Fantastic! Now, piecing all understandings together, what is the main idea of this passage?"
>
> **Student:** "{student’s understanding}"
