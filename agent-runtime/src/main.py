"""Jarvis Agent Runtime - CLI Entry Point (Phase 0b Standalone).

Allows interactive text input from terminal, executes the LangGraph tool-calling loop,
and prints the final response.
"""

import sys
from typing import Any
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from src.graph.state import AgentState
from src.graph.workflow import app

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def extract_text(content: Any) -> str:
    """Trích xuất text hiển thị từ nội dung tin nhắn."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "".join(parts)
    return str(content)


def process_query(query: str, history: list[BaseMessage] | None = None) -> list[BaseMessage]:
    """Gửi câu hỏi vào LangGraph và in tiến trình thực thi."""
    current_messages = list(history) if history else []
    current_messages.append(HumanMessage(content=query))

    state: AgentState = {
        "messages": current_messages,
        "iteration_count": 0,
    }

    # Chạy graph
    result = app.invoke(state)
    all_messages = result["messages"]

    # In các bước thực thi tool trung gian (nếu có) để người dùng dễ theo dõi
    for msg in all_messages[len(current_messages) - 1 :]:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"  [Tool Call] -> {tc['name']}({tc.get('args', {})})")
        elif isinstance(msg, ToolMessage):
            print(f"  [Tool Result] <- {msg.content}")

    # Lấy tin nhắn cuối cùng (kết quả trả lời hoàn chỉnh)
    final_message = all_messages[-1]
    final_text = extract_text(final_message.content)
    print(f"\nJarvis: {final_text}")

    return all_messages


def main() -> None:
    """Khởi chạy CLI cho Jarvis Agent."""
    print("=" * 60)
    print(" Jarvis Agent Runtime CLI (Standalone - Phase 0b)")
    print(" Gõ câu hỏi của bạn và nhấn Enter.")
    print(" Nhập 'exit', 'quit' hoặc 'q' để thoát.")
    print("=" * 60)

    # Chế độ nhận tham số dòng lệnh một lần (cho kiểm thử hoặc script)
    if len(sys.argv) > 1:
        single_query = " ".join(sys.argv[1:]).strip()
        if single_query:
            print(f"\nUser: {single_query}")
            process_query(single_query)
            return

    history: list[BaseMessage] = []

    while True:
        try:
            print("\n" + "-" * 40)
            user_input = input("User: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("Tạm biệt bạn!")
                break

            history = process_query(user_input, history)

        except (KeyboardInterrupt, EOFError):
            print("\nĐã nhận tín hiệu dừng. Tạm biệt bạn!")
            break
        except Exception as e:
            print(f"\n[Lỗi]: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
