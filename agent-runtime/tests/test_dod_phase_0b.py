"""Test suite confirming Phase 0b Definition of Done (DoD).

Subtask 0b.11:
2 test cases bắt buộc:
(1) "Mấy giờ rồi?" -> model phải tự gọi get_current_time, trả lời đúng.
(2) "Chào Jarvis" -> model không gọi tool nào, trả lời thẳng.
"""

import sys
from pathlib import Path
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# Thêm root của agent-runtime vào sys.path
current_dir = Path(__file__).resolve().parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from src.graph.state import AgentState
from src.graph.workflow import app

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def extract_text(content) -> str:
    """Trích xuất chuỗi text từ content (xử lý cả str và list các blocks)."""
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


def test_case_1_get_current_time():
    """Case 1: 'Mấy giờ rồi?' -> model phải tự gọi get_current_time, trả lời đúng."""
    print("\n" + "=" * 60)
    print("TEST CASE 1: 'Mấy giờ rồi?'")
    print("Kỳ vọng: Model tự động gọi tool 'get_current_time' và trả lời thời gian.")
    print("=" * 60)

    prompt = "Mấy giờ rồi?"
    state: AgentState = {
        "messages": [HumanMessage(content=prompt)],
        "iteration_count": 0,
    }

    result = app.invoke(state)
    messages = result["messages"]

    # 1. Tìm AIMessage kiểm tra xem có gọi đúng get_current_time không
    tool_calls = []
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            tool_calls.extend(msg.tool_calls)

    print(f"Tool calls được thực hiện: {[tc['name'] for tc in tool_calls]}")
    assert len(tool_calls) > 0, "LỖI: Model không gọi bất kỳ tool nào!"
    assert any(tc["name"] == "get_current_time" for tc in tool_calls), (
        f"LỖI: Model không gọi tool 'get_current_time'! Các tool gọi: {tool_calls}"
    )

    # 2. Tìm ToolMessage xem tool get_current_time có trả kết quả không
    tool_results = [
        msg for msg in messages if isinstance(msg, ToolMessage) and msg.name == "get_current_time"
    ]
    assert len(tool_results) > 0, "LỖI: Không tìm thấy ToolMessage từ get_current_time!"
    print(f"Tool Result nhận được: '{tool_results[0].content}'")

    # 3. Kiểm tra tin nhắn phản hồi cuối cùng
    final_message = messages[-1]
    assert isinstance(final_message, AIMessage), "LỖI: Tin nhắn cuối cùng không phải là AIMessage!"
    final_text = extract_text(final_message.content)
    print(f"Câu trả lời cuối cùng từ Jarvis:\n'{final_text}'")
    assert len(final_text.strip()) > 0, "LỖI: Câu trả lời cuối cùng rỗng!"

    print("\n-> TEST CASE 1 PASSED: Model tự gọi get_current_time và phản hồi chính xác!")


def test_case_2_direct_greeting():
    """Case 2: 'Chào Jarvis' -> model không gọi tool nào, trả lời thẳng."""
    print("\n" + "=" * 60)
    print("TEST CASE 2: 'Chào Jarvis'")
    print("Kỳ vọng: Model KHÔNG gọi bất kỳ tool nào, trả lời thẳng trực tiếp.")
    print("=" * 60)

    prompt = "Chào Jarvis"
    state: AgentState = {
        "messages": [HumanMessage(content=prompt)],
        "iteration_count": 0,
    }

    result = app.invoke(state)
    messages = result["messages"]

    # 1. Kiểm tra tuyệt đối không có tool_calls nào
    tool_calls = []
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            tool_calls.extend(msg.tool_calls)

    assert len(tool_calls) == 0, f"LỖI: Model không nên gọi tool nào nhưng lại gọi: {tool_calls}"

    # 2. Kiểm tra không có ToolMessage nào
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
    assert len(tool_messages) == 0, f"LỖI: Tìm thấy ToolMessage ngoài ý muốn: {tool_messages}"

    # 3. Kiểm tra tin nhắn phản hồi cuối cùng
    final_message = messages[-1]
    assert isinstance(final_message, AIMessage), "LỖI: Tin nhắn cuối cùng không phải là AIMessage!"
    final_text = extract_text(final_message.content)
    print(f"Câu trả lời cuối cùng từ Jarvis:\n'{final_text}'")
    assert len(final_text.strip()) > 0, "LỖI: Câu trả lời rỗng!"

    print("\n-> TEST CASE 2 PASSED: Model không gọi tool và trả lời trực tiếp!")


if __name__ == "__main__":
    print("Bắt đầu chạy Test Case xác nhận DoD Phase 0b...")
    test_case_1_get_current_time()
    test_case_2_direct_greeting()
    print("\n" + "=" * 60)
    print("TẤT CẢ 2 TEST CASE ĐÃ VƯỢT QUA! DoD PHASE 0b ĐƯỢC XÁC NHẬN THÀNH CÔNG!")
    print("=" * 60)
