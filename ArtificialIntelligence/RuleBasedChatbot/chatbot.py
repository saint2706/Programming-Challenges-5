"""Simple rule-based chatbot.

This script loops for user input until a goodbye keyword is received. It uses
explicit pattern checks to respond to greetings, business hours inquiries, and
fallback cases.

Rules table:
- Greeting: keywords such as "hi", "hello", or "hey" -> friendly greeting.
- Hours inquiry: mentions of "hours", "open", or "closing" -> returns hours info.
- Goodbye: "goodbye", "bye", "exit", or "quit" -> ends the conversation.
- Fallback: any other text -> ask for clarification.
"""

from __future__ import annotations

import re
from typing import Optional


GOODBYE_KEYWORDS = {"goodbye", "bye", "exit", "quit"}
GREETINGS_PATTERN = re.compile(r"\b(hi|hello|hey|good\s+morning|good\s+evening)\b", re.IGNORECASE)
HOURS_PATTERN = re.compile(r"\b(hours?|open|closing|close)\b", re.IGNORECASE)


def classify_intent(message: str) -> str:
    """Classify the user's message into an intent string."""
    normalized = message.strip().lower()
    if not normalized:
        return "fallback"
    if any(keyword in normalized.split() for keyword in GOODBYE_KEYWORDS):
        return "goodbye"
    if GREETINGS_PATTERN.search(message):
        return "greeting"
    if HOURS_PATTERN.search(message):
        return "hours"
    return "fallback"


def generate_response(message: str) -> Optional[str]:
    """Generate a response based on the detected intent.

    Returns a string to display or ``None`` when the conversation should end.
    """
    intent = classify_intent(message)
    if intent == "goodbye":
        return None
    if intent == "greeting":
        return "Hello! How can I help you today?"
    if intent == "hours":
        return "We're open from 9am to 6pm, Monday through Friday."
    return "I'm not sure I understand. Could you rephrase your question?"


def main() -> None:
    """
    Docstring for main.
    """
    print("Rule-Based Chatbot (type 'goodbye' to exit)")
    while True:
        user_input = input("You: ")
        response = generate_response(user_input)
        if response is None:
            print("Bot: Goodbye!")
            break
        print(f"Bot: {response}")


if __name__ == "__main__":
    main()
