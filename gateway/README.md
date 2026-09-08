# Gateway Service (Process 1)

Service Gateway viết bằng Java / Spring Boot đảm nhận việc điều hướng lưu lượng và quản lý tác vụ hẹn giờ.

## Vai trò chính
1. **WebSocket Proxy/Router**:
   - Nhận audio transcript/event từ Voice Layer và Desktop App.
   - Định tuyến bản tin tới Agent Runtime (`agent-runtime/`).
   - Chuyển tiếp phản hồi kết quả và yêu cầu xác nhận (`Confirmation`) về UI / Voice.
2. **Scheduler (Quartz)**:
   - Lưu trữ và kích hoạt `ScheduledTask`.
   - `SIMPLE_REMINDER`: Xử lý cục bộ.
   - `AGENT_TASK`: Forward sang Agent Runtime.

## Cấu trúc thư mục
```
gateway/
├── src/main/java/com/duy/jarvis/gateway/
│   ├── websocket/     # Core router & handler cho kết nối WebSocket
│   ├── scheduler/     # Quartz job definitions & scheduled task entities
│   └── GatewayApplication.java
└── src/main/resources/
    └── application.yml
```
