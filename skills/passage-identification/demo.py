#!/usr/bin/env python3
"""Demo for the Passage Identification skill."""

from logic import run


def main():
    print("=== Passage Identification — Demo ===")
    print("Type your message, or 'quit' to exit.")
    print("Use '/text <text>' to load the course text the tutor can draw passages from.\n")

    conversation_history = []
    passage_context = ""

    while True:
        student_input = input("You: ").strip()
        if student_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if not student_input:
            continue

        # Handle /text command to load course reading
        if student_input.startswith("/text "):
            passage_context = student_input[len("/text "):]
            print("Tutor: Course text loaded.\n")
            continue

        # Call the skill
        response = run({
            "student_message": student_input,
            "conversation_history": conversation_history,
            "passage_context": passage_context,
        })

        print(f"Tutor: {response}\n")

        conversation_history.append({"role": "student", "content": student_input})
        conversation_history.append({"role": "tutor", "content": response})


if __name__ == "__main__":
    main()
