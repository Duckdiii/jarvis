# Agent Runtime (Process 2)

Lõi xử lý Agent thông minh của Jarvis, xây dựng trên nền tảng **LangGraph** và Python 3.11+.

## Cấu trúc thư mục
```
agent-runtime/
├── src/
│   ├── graph/         # LangGraph state graph và tool-call loop
│   ├── tools/         # File I/O, Shell Exec, App Automation, Browser Control
│   ├── redaction/     # Bộ lọc Presidio Data Redaction Filter
│   ├── llm/           # Client kết nối Gemini API & Ollama local SLM
│   └── main.py        # Entry point khởi chạy Agent Runtime & WebSocket client
├── pyproject.toml
└── CLAUDE.md
```

## Các nguyên tắc bất di bất dịch
1. **Redaction Filter**: Bắt buộc lọc dữ liệu nhạy cảm qua Presidio trước khi đưa vào context gửi LLM bên ngoài.
2. **Human-in-the-loop**: Bắt buộc yêu cầu xác nhận trước khi gọi tool có side-effect ghi/xóa/sửa.
3. **Model Partitioning**: Ollama chỉ phân loại ý định (Intent Routing); Gemini phụ trách reasoning và tool call phức tạp.
