"""Jarvis Agent Runtime - Entry Point.

Starts the LangGraph agent loop and connects to the Gateway via WebSocket.
"""
import sys


def main() -> None:
    print("Initializing Jarvis Agent Runtime (Process 2)...")
    print("Connecting to Gateway at ws://127.0.0.1:8080...")


if __name__ == "__main__":
    main()
