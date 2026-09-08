# Agent Runtime — Guidelines & Conventions

Module `agent-runtime` đóng vai trò là Process 2 trong hệ thống Jarvis, chịu trách nhiệm về trí thông minh, điều phối state graph và thực thi tool.

## Phạm vi trách nhiệm
- **LangGraph State Graph**: Quản lý tool-call loop, context assembly, hội thoại và bộ nhớ phiên.
- **LLM Routing**:
  - `Ollama (Phi-4-mini/Qwen2.5-3B)`: CHỈ dùng làm Intent Router / câu hỏi đơn giản không side-effect. Tuyệt đối không giao tool-calling nguy hiểm.
  - `Gemini API`: Định tuyến cho mọi tác vụ reasoning phức tạp và tool-calling có side-effect.
- **Tool Layer**:
  - `file_io.py`: Đọc/ghi/tìm kiếm file trên máy.
  - `shell_exec.py`: Thực thi lệnh bash/powershell trong Docker sandbox container pool.
  - `app_automation.py`: Tự động hóa ứng dụng desktop.
  - `browser_control.py`: Điều khiển trình duyệt (MCP Playwright / script).
- **Data Redaction (Presidio)**: Mọi kết quả từ Tool (đặc biệt File I/O) BẮT BUỘC lọc qua Presidio trước khi nạp vào prompt gửi LLM.
- **Human-in-the-loop**: Mọi tool có side-effect không hoàn tác phải chờ `Confirmation` từ Gateway/Desktop app. Timeout = mặc định hủy.

## Quy chuẩn code & Tool Schema
- Python 3.11+, quản lý dependency bằng `pyproject.toml` (hỗ trợ uv / poetry).
- Linter/Formatter: Ruff.
- Type hints đầy đủ (mypy-compatible).
- Tool definitions sử dụng Pydantic models cho input args schema rõ ràng.
