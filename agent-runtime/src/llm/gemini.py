"""Gemini API Client for Jarvis Agent Runtime."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Explicitly load .env from agent-runtime directory or parent
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_gemini_client(
    model: str | None = None,
    temperature: float = 0.7,
) -> ChatGoogleGenerativeAI:
    """Initialize and return a ChatGoogleGenerativeAI client.

    Reads API key securely from environment variables.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "Gemini API key not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY in .env file."
        )

    model_name = model or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=api_key,
    )


def ask_gemini(prompt: str) -> str:
    """Send a simple text prompt to Gemini and return the response text."""
    llm = get_gemini_client()
    response = llm.invoke(prompt)
    if isinstance(response.content, str):
        return response.content
    if isinstance(response.content, list):
        text_parts = []
        for part in response.content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
        return "".join(text_parts)
    return str(response.content)


if __name__ == "__main__":
    test_prompt = "chào"
    print(f"Sending prompt to Gemini: '{test_prompt}'...")
    reply = ask_gemini(test_prompt)
    print("Gemini response:")
    print(reply)
