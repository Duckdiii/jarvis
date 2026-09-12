"""LangGraph nodes for Jarvis Agent Runtime."""

import sys
from typing import Any, Callable, Sequence
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool

from ..llm.gemini import get_gemini_client
from ..tools.system_tools import echo_tool, get_current_time, get_system_info
from .state import AgentState

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Khởi tạo danh sách tools mặc định cho Phase 0b
DEFAULT_TOOLS: list[BaseTool] = [get_current_time, get_system_info, echo_tool]


def create_agent_node(tools: Sequence[BaseTool] | None = None) -> Callable[[AgentState], dict[str, Any]]:
    """Tạo hàm agent_node với model đã được bind tools."""
    bound_tools = tools if tools is not None else DEFAULT_TOOLS
    llm = get_gemini_client()
    model_with_tools = llm.bind_tools(bound_tools)

    def agent_node(state: AgentState) -> dict[str, Any]:
        """Node gọi Gemini, tiếp nhận state hiện tại và trả về message phản hồi.

        Phản hồi (AIMessage) có thể là text thông thường hoặc chứa tool_calls
        nếu model quyết định cần gọi tool.
        """
        messages: Sequence[BaseMessage] = state["messages"]
        response: AIMessage = model_with_tools.invoke(messages)
        return {"messages": [response]}

    return agent_node


def validate_tool_arguments(tool: BaseTool, args: dict[str, Any]) -> tuple[bool, str | None]:
    """Kiểm tra tham số Gemini truyền vào có khớp schema của tool hay không (0b.9).

    Phát hiện các lỗi:
    - Thiếu tham số bắt buộc.
    - Sai kiểu dữ liệu (data type mismatch).
    - Vi phạm ràng buộc schema của Pydantic model.
    """
    schema = getattr(tool, "args_schema", None)
    if schema is None and hasattr(tool, "get_input_schema"):
        try:
            schema = tool.get_input_schema()
        except Exception:
            schema = None

    if schema is not None:
        try:
            if hasattr(schema, "model_validate"):
                schema.model_validate(args)
            elif callable(schema):
                schema(**args)
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    return True, None


class ToolNode:
    """Node thực thi Tool trong LangGraph state graph.

    Tiếp nhận state hiện tại, tìm các tool_call trong message cuối cùng,
    validate tham số trước khi thực thi, và sinh ra các ToolMessage chứa kết quả.
    """

    def __init__(self, tools: Sequence[BaseTool]):
        self.tools_by_name: dict[str, BaseTool] = {tool.name: tool for tool in tools}

    def __call__(self, state: AgentState) -> dict[str, Any]:
        return self.invoke(state)

    def invoke(self, state: AgentState | dict[str, Any]) -> dict[str, Any]:
        """Thực thi các tool_calls có trong message gần nhất của state."""
        messages: Sequence[BaseMessage] = state.get("messages", [])
        if not messages:
            return {"messages": []}

        last_message = messages[-1]
        tool_calls = getattr(last_message, "tool_calls", None) or []
        if not tool_calls:
            return {"messages": []}

        tool_messages: list[ToolMessage] = []
        for call in tool_calls:
            tool_name = call.get("name", "")
            tool_args = call.get("args", {})
            call_id = call.get("id", "")

            if tool_name not in self.tools_by_name:
                result = f"Error: Tool '{tool_name}' not found."
            else:
                tool = self.tools_by_name[tool_name]
                # Validate tham số trước khi chạy tool (Edge case phòng chống sai schema)
                is_valid, val_err = validate_tool_arguments(tool, tool_args)
                if not is_valid:
                    result = (
                        f"ToolCall Rejected: Tham số không đúng schema của tool '{tool_name}'. "
                        f"Chi tiết: {val_err}. Vui lòng cung cấp đúng tham số yêu cầu."
                    )
                else:
                    try:
                        result = tool.invoke(tool_args)
                    except Exception as e:
                        result = f"Error executing tool '{tool_name}': {str(e)}"

            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    name=tool_name,
                    tool_call_id=call_id,
                )
            )

        current_iterations = state.get("iteration_count") or 0
        return {
            "messages": tool_messages,
            "iteration_count": current_iterations + 1,
        }


def create_tool_node(tools: Sequence[BaseTool] | None = None) -> ToolNode:
    """Khởi tạo ToolNode với danh sách công cụ được cấu hình."""
    bound_tools = tools if tools is not None else DEFAULT_TOOLS
    return ToolNode(bound_tools)


# Khởi tạo instance mặc định cho agent_node và tool_node
agent_node = create_agent_node()
tool_node = create_tool_node()


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    print("=== TEST MINI-DOD 0b.5 & 0b.6 ===")

    # Test 0b.5 Case 1: Hỏi giờ hệ thống -> Model trả về tool_call
    print("\n[0b.5 Case 1]: Hỏi giờ hệ thống -> Kiểm tra model sinh tool_call")
    state_tool: AgentState = {
        "messages": [HumanMessage(content="Bây giờ là mấy giờ rồi?")],
        "session_id": 1,
    }
    result_tool = agent_node(state_tool)
    ai_msg: AIMessage = result_tool["messages"][0]
    print(f"Tool calls nhận được: {ai_msg.tool_calls}")

    # Test 0b.6 (mini-DoD 0b.6): Giả lập 1 tool_call thủ công -> node chạy đúng tool, trả đúng kết quả
    print("\n[0b.6 Case 1]: Giả lập tool_call 'get_current_time' -> tool_node thực thi")
    mock_ai_call = AIMessage(
        content="",
        tool_calls=[{
            "name": "get_current_time",
            "args": {},
            "id": "mock_call_time_001",
            "type": "tool_call",
        }]
    )
    mock_state_time: AgentState = {
        "messages": [mock_ai_call],
        "session_id": 1,
    }
    output_time = tool_node.invoke(mock_state_time)
    print("Kết quả tool_node trả về:")
    for msg in output_time["messages"]:
        print(f"[{msg.__class__.__name__}] name={msg.name}, id={msg.tool_call_id}, content='{msg.content}'")

    print("\n[0b.6 Case 2]: Giả lập tool_call 'get_system_info' -> tool_node thực thi")
    mock_ai_call_sys = AIMessage(
        content="",
        tool_calls=[{
            "name": "get_system_info",
            "args": {},
            "id": "mock_call_sys_002",
            "type": "tool_call",
        }]
    )
    mock_state_sys: AgentState = {
        "messages": [mock_ai_call_sys],
        "session_id": 1,
    }
    output_sys = tool_node.invoke(mock_state_sys)
    print("Kết quả tool_node trả về:")
    for msg in output_sys["messages"]:
        print(f"[{msg.__class__.__name__}] name={msg.name}, id={msg.tool_call_id}, content='{msg.content}'")

    # Test 0b.9 (mini-DoD 0b.9): Giả lập tool_call thiếu tham số -> hệ thống reject có kiểm soát, không crash
    print("\n--- Test mini-DoD 0b.9: Validate tool call trước khi thực thi ---")
    print("[0b.9 Test]: Giả lập tool_call 'echo_tool' thiếu tham số bắt buộc 'message'...")
    mock_invalid_tool_call = AIMessage(
        content="",
        tool_calls=[{
            "name": "echo_tool",
            "args": {},  # Thiếu tham số bắt buộc 'message'
            "id": "mock_invalid_echo_003",
            "type": "tool_call",
        }]
    )
    mock_state_invalid: AgentState = {
        "messages": [mock_invalid_tool_call],
        "session_id": 1,
    }

    try:
        output_invalid = tool_node.invoke(mock_state_invalid)
        res_msg = output_invalid["messages"][0]
        print(f"[{res_msg.__class__.__name__}] name={res_msg.name}, id={res_msg.tool_call_id}")
        print(f"Nội dung phản hồi reject: {res_msg.content}")

        assert "ToolCall Rejected" in res_msg.content or "Validation error" in res_msg.content
        assert "message" in res_msg.content  # Báo rõ thiếu tham số message
        print("-> mini-DoD 0b.9 PASSED: Hệ thống reject có kiểm soát, không bị crash!")
    except Exception as e:
        print(f"-> THẤT BẠI: Hệ thống bị crash với ngoại lệ: {e}", file=sys.stderr)
        sys.exit(1)
