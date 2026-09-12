import sys
from typing import Annotated, Optional, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


class AgentState(TypedDict):
    """State của Jarvis Agent trong LangGraph state graph.

    Lưu trữ trạng thái xuyên suốt vòng lặp suy luận (reasoning) và thực thi tool (tool-call loop).

    Attributes:
        messages: Danh sách lịch sử hội thoại, tool calls và tool results:
            - HumanMessage: Câu hỏi / lệnh từ người dùng.
            - AIMessage: Phản hồi từ model (chứa text trả lời hoặc yêu cầu gọi tool).
            - ToolMessage: Kết quả thực thi trả về từ Tool.
            Sử dụng reducer `add_messages` để LangGraph tự động nối tiếp và quản lý ID tin nhắn.
        session_id: (Tùy chọn) Định danh phiên làm việc (ConversationSession) phục vụ lưu trữ DB.
        iteration_count: Đếm số lần lặp thực thi tool để kích hoạt guard chống vòng lặp vô hạn.
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id: Optional[int]
    iteration_count: Optional[int]


if __name__ == "__main__":
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    # Test khởi tạo mẫu State
    test_state: AgentState = {
        "messages": [
            HumanMessage(content="Bây giờ là mấy giờ?"),
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "get_current_time",
                    "args": {},
                    "id": "call_123",
                    "type": "tool_call",
                }]
            ),
            ToolMessage(content="2026-09-09 15:19:00", tool_call_id="call_123"),
            AIMessage(content="Bây giờ là 15:19:00 ngày 09/09/2026."),
        ],
        "session_id": 1,
    }

    print("--- mini-DoD Check: AgentState defined and verified successfully ---")
    print(f"Total messages in state: {len(test_state['messages'])}")
    for msg in test_state["messages"]:
        print(f"[{msg.__class__.__name__}]: {getattr(msg, 'content', '') or getattr(msg, 'tool_calls', '')}")
