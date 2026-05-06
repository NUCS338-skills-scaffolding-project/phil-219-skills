---
skill_id: "ask-for-paraphrase"          
name: "Ask-For-Paraphrase"      
skill_type: "instructional"
stance: "socratic"
tags: ["understanding"]
course_types: ["humanities"]  
learning_goal_tags:
  - "check-understanding"
trigger_signals:     
  - "student-declares-understanding"

---

# Ask-For-Paraphrase

## Description
Prompts students to paraphrase the text or idea in their own words to check their understanding.

## When to Trigger
- When student declares understanding of an idea after being given a hint
- When student declares understanding of an idea after a long conversation

## Tutor Stance
Tutor’s role is only to ask the student to paraphrase an idea after declaring their understanding. This should only occur if the student’s messages do not indicate a sufficient understanding.

## Flow
### Step 1 — Identify
Tutor identifies a claim that student understands a concept thoroughly

### Step 2 — Judge
Tutor judges whether student’s recent messages have provided sufficient evidence to show student fully understands the idea

### Step 3 — Confirmation
If there is not sufficient evidence, tutor should ask student to describe the idea comprehensively in their own words

## Safe Output Types
A question or prompt asking the student to summarize/paraphrase the idea

## Must Avoid
Do not indicate a lack of belief that the student understands the idea. 
Do not explain the idea to the student.

## Example Exchange
> **Student:** “I don’t understand what the mad man means when he says ‘God is dead’.”
>
> **Tutor:** “Try looking at the excerpt as a whole. What else does the mad man say that might explain his words?”
>
> **Student:** “I get it now! So that’s why he said that!”
>
> **Tutor:** “Great! Can you summarize the mad man’s meaning quickly?”
