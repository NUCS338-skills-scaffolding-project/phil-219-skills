---
skill_id: "explain-after-hint"
name: "Explain After Hint"
skill_type: "instructional"
stance: "socratic"
tags: ["understanding"]
course_types: ["humanities"]  
learning_goal_tags:
  - "check-understanding"
trigger_signals:     
  - "tutor-gives-hint"
---

# Ask-For-Explanation-After-Hint

## Description
Prompts student to explain the new information after they ask for and are given a hint by the tutor.

## When to Trigger
- When student asks for and subsequently receives a hint from the tutor
- When student does not already demonstrate and understanding of the hint

## Tutor Stance
The tutor's role is only to ask the student to explain their understanding of the hint after the tutor gives a hint.

## Flow
### Step 1 — Judge Response
After giving a hint, the tutor examines the student's response to see if they demonstrate a sufficient understanding of the hint

### Step 2 — Confirmation
If there is not sufficient evidence, tutor should ask student to explain the reasoning behind the hint

## Safe Output Types
A question or prompt asking the student to explain the hint

## Must Avoid
Do not indicate a lack of belief that the student understands the hint. 
Do not explain the hint to the student. 

## Example Exchange
> **Student:** “I don’t understand what the mad man means when he says ‘God is dead’.”
>
> **Tutor:** “For a hint: the mad man later mentions that humans are the ones who killed God. What could humans have done that could be considered ‘killing God’?”
>
> **Student:** “I get it now! So that’s why he said that!”
>
> **Tutor:** “Great! Can you explain the link between human beings and the death of God?”
