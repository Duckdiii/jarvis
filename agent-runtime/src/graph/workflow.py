"""LangGraph workflow definition and state graph builder for Jarvis Agent Runtime.

Includes infinite loop guard (max_iterations) to prevent runaway tool-calling loops.
"""

import sys
from typing import Literal, Sequence
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .nodes import create_agent_node, create_tool_node
from .state import AgentState

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Giới hạn số vòng lặp tối đa cho tool-calling theo Edge Cases specification
DEFAULT_MAX_ITERATIONS: int = 5


def create_should_continue(max_iterations: int = DEFAULT_MAX_ITERATIONS):
    """Tạo hàm kiểm tra điều kiện rẽ nhánh kèm guard giới hạn số vòng lặp tối đa."""

    def should_continue(state: AgentState) -> Literal["tools", "max_iterations_reached", "__end__"]:
        messages: Sequence[BaseMessage] = state.get("messages", [])
        if not messages:
            return END

        last_message = messages[-1]
        tool_calls = getattr(last_message, "tool_calls", None) or []
        if not tool_calls:
            return END

        iteration_count = state.get("iteration_count") or 0
        if iteration_count >= max_iterations:
            return "max_iterations_reached"

        return "tools"

    return should_continue


def create_max_iterations_node(max_iterations: int = DEFAULT_MAX_ITERATIONS):
    """Tạo node xử lý khi vòng lặp vượt ngưỡng max_iterations."""

    def max_iterations_node(state: AgentState) -> dict:
        iteration_count = state.get("iteration_count") or max_iterations
        error_msg = AIMessage(
            content=(
                f"Lỗi: Đã vượt quá số lần gọi tool tối đa cho phép (max_iterations={max_iterations}, hiện tại={iteration_count}). "
                "Vòng lặp tool-calling không hội tụ (edge case đã phát hiện), hệ thống dừng để bảo vệ tài nguyên."
            )
        )
        return {"messages": [error_msg]}

    return max_iterations_node


# Function mặc định cho trường hợp dùng ngoài
should_continue = create_should_continue(DEFAULT_MAX_ITERATIONS)


def build_graph(
    tools: Sequence[BaseTool] | None = None,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    checkpointer=None,
    agent_func_override=None,
) -> CompiledStateGraph:
    """Xây dựng và compile StateGraph cho Jarvis Agent.

    Luồng hoạt động:
        START -> agent -> (conditional edge)
                            ├── có tool_call (và < max_iterations) -> tools -> quay lại agent
                            ├── có tool_call (nhưng >= max_iterations) -> max_iterations_reached -> END
                            └── không có tool_call -> END
    """
    agent_func = agent_func_override or create_agent_node(tools)
    tool_func = create_tool_node(tools)
    cond_edge_func = create_should_continue(max_iterations)
    max_iter_node_func = create_max_iterations_node(max_iterations)

    workflow = StateGraph(AgentState)

    # 1. Thêm các node
    workflow.add_node("agent", agent_func)
    workflow.add_node("tools", tool_func)
    workflow.add_node("max_iterations_reached", max_iter_node_func)

    # 2. Cấu hình luồng đi (edges)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        cond_edge_func,
        {
            "tools": "tools",
            "max_iterations_reached": "max_iterations_reached",
            END: END,
        },
    )
    workflow.add_edge("tools", "agent")
    workflow.add_edge("max_iterations_reached", END)

    # 3. Biên dịch graph
    return workflow.compile(checkpointer=checkpointer)


# Compiled graph instance mặc định
app = build_graph()


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage
    from langchain_core.tools import tool

    print("=== TEST MINI-DOD 0b.7 & 0b.8 ===")

    # 1. Test 0b.7: Kiểm tra compile & vẽ graph
    print("\n[Test 0b.7]: Compile & vẽ sơ đồ graph")
    print(app.get_graph().draw_mermaid())
    print("-> Compile & vẽ graph thành công!")

    # 2. Test 0b.8 (mini-DoD 0b.8): Giả lập 1 tool luôn trả lỗi / lặp không dừng
    print("\n[Test 0b.8]: Giả lập tool luôn trả lỗi -> Kiểm tra guard dừng đúng ngưỡng")

    call_counter = 0

    @tool
    def failing_tool() -> str:
        """Tool luôn luôn trả về lỗi."""
        global call_counter
        call_counter += 1
        return f"Error: Database connection refused (Thất bại lần {call_counter})"

    # Mock agent liên tục đòi gọi failing_tool khi nhận kết quả
    def persistent_failing_agent(state: AgentState) -> dict:
        return {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[{
                        "name": "failing_tool",
                        "args": {},
                        "id": f"call_{state.get('iteration_count', 0)}",
                        "type": "tool_call",
                    }]
                )
            ]
        }

    TEST_MAX_ITER = 3
    test_guard_graph = build_graph(
        tools=[failing_tool],
        max_iterations=TEST_MAX_ITER,
        agent_func_override=persistent_failing_agent,
    )

    initial_state: AgentState = {
        "messages": [HumanMessage(content="Thực hiện truy vấn dữ liệu")],
        "iteration_count": 0,
    }

    print(f"Bắt đầu chạy graph với max_iterations = {TEST_MAX_ITER}...")
    final_output = test_guard_graph.invoke(initial_state)

    print(f"\nSố lần failing_tool thực sự chạy: {call_counter}")
    final_message = final_output["messages"][-1]
    print(f"Tin nhắn cuối cùng từ graph: [{final_message.__class__.__name__}]")
    print(f"Nội dung: {final_message.content}")

    assert call_counter == TEST_MAX_ITER, f"Kỳ vọng tool chạy đúng {TEST_MAX_ITER} lần nhưng chạy {call_counter} lần"
    assert "max_iterations" in final_message.content, "Kỳ vọng thông báo lỗi chứa thông tin max_iterations"
    print("\n-> mini-DoD 0b.8 PASSED: Graph dừng đúng ngưỡng an toàn, không chạy vô hạn!")
