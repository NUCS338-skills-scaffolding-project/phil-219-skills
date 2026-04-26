import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = None

MODEL = "gpt-4o"
MAX_TOKENS = 1024
TEMPERATURE = 0.7


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY not set. "
                "Copy .env.example to .env and add your key."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def call_llm(system_prompt, conversation_history):
    """
    Send a conversation to ChatGPT and return the assistant response.

    :param system_prompt: The system-level instruction for this skill.
    :param conversation_history: List of dicts with "role" and "content" keys.
           Roles should be "user" or "assistant" (OpenAI API format).
    :return: The assistant's text response.
    """
    client = _get_client()
    messages = [{"role": "system", "content": system_prompt}] + conversation_history
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        messages=messages,
    )
    return response.choices[0].message.content
