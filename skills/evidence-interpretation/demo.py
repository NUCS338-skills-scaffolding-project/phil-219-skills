#!/usr/bin/env python3
"""Demo for the Evidence Interpretation skill."""

from logic import run


def main():
    print("=== Evidence Interpretation — Demo ===")
    print("Type your message, or 'quit' to exit.")
    print("Use '/passage <text>' to set the passage being discussed.\n")

    conversation_history = []
    passage_context = ""

    while True:
        student_input = input("You: ").strip()
        if student_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if not student_input:
            continue

        # Handle /passage command
        if student_input.startswith("/passage "):
            passage_context = student_input[len("/passage "):]
            print("Tutor: Passage context updated.\n")
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
