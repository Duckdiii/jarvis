# Gateway — Guidelines & Conventions

Module `gateway` đóng vai trò là Process 1 trong hệ thống Jarvis.

## Phạm vi trách nhiệm
- **Proxy/Router**: Tiếp nhận các kết nối WebSocket từ desktop-app, voice-layer và chuyển tiếp đến `agent-runtime`.
- **Scheduler (Quartz)**: Quản lý các công việc lên lịch (`ScheduledTask`).
  - `ScheduledTask.taskType == SIMPLE_REMINDER`: Gateway tự xử lý (gửi notification/voice trực tiếp).
  - `ScheduledTask.taskType == AGENT_TASK`: Chuyển tiếp (forward) sang `agent-runtime` để kích hoạt workflow.
- **Ranh giới nghiêm ngặt**:
  - **KHÔNG** chứa Agent logic hay LLM orchestration.
  - **KHÔNG** chứa Tool layer.
  - Chỉ bind `127.0.0.1` — tuyệt đối không expose ra mạng ngoài / LAN.

## Công nghệ & Quy chuẩn
- **Ngôn ngữ**: Java 21+
- **Framework**: Spring Boot 3.x
- **Build tool**: Gradle Kotlin DSL (`build.gradle.kts`)
- **Lệnh build & run**:
  - Run app: `./gradlew bootRun`
  - Test: `./gradlew test`
  - Build jar: `./gradlew build`
- **Code Style**: Tuân thủ chuẩn Google Java Format, Clean Architecture cho WebSocket & Scheduler routing.
