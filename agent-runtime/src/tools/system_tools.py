"""Simple non-side-effect tools for Jarvis Agent Runtime (Phase 0b).

Contains:
- get_current_time: Lấy ngày và giờ hiện tại của hệ thống local.
- get_system_info: Lấy thông tin cơ bản về hệ điều hành và môi trường máy tính.
- echo_tool: Tool nhận tham số có schema rõ ràng để kiểm thử validation.
"""

from datetime import datetime
import platform
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class EchoInput(BaseModel):
    message: str = Field(..., description="Nội dung chuỗi text cần lặp lại (tham số bắt buộc)")
    repeat_count: int = Field(default=1, ge=1, le=10, description="Số lần lặp lại (1-10, mặc định là 1)")


@tool
def get_current_time() -> str:
    """Lấy ngày và giờ hiện tại của hệ thống máy tính local."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def get_system_info() -> str:
    """Lấy thông tin cơ bản về hệ điều hành và môi trường máy tính local."""
    return (
        f"OS: {platform.system()} {platform.release()} ({platform.version()}), "
        f"Architecture: {platform.machine()}, "
        f"Processor: {platform.processor() or 'Unknown'}, "
        f"Python: {platform.python_version()}"
    )


@tool(args_schema=EchoInput)
def echo_tool(message: str, repeat_count: int = 1) -> str:
    """Lặp lại nội dung text được cung cấp theo số lần yêu cầu."""
    return "\n".join([message] * repeat_count)


if __name__ == "__main__":
    print("--- Testing tools directly (mini-DoD) ---")
    current_time = get_current_time.invoke({})
    print(f"Current Time: {current_time}")
    sys_info = get_system_info.invoke({})
    print(f"System Info: {sys_info}")
    echo_result = echo_tool.invoke({"message": "Hello Jarvis", "repeat_count": 2})
    print(f"Echo Result:\n{echo_result}")
