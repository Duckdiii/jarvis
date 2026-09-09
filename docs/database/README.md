# Jarvis Business Entities & Session DB

Tài liệu chi tiết về 10 Business Entities trong hệ thống Jarvis theo kiến trúc v4.

## Quyền ghi cơ sở dữ liệu (Session DB)
- **Agent Runtime (Python)**: Ghi và quản lý `ConversationSession`, `Message`, `Fact`, `EpisodicMemory`, `ToolCall`.
- **Gateway (Java / Spring Boot)**: Ghi và quản lý `ScheduledTask`, `Confirmation`, `Notification`.
- **Entities chung**: `User`, `UserProfile`.

---

## Chi tiết 10 Entities

| STT | Entity | Bảng DB | Vai trò chính |
| --- | --- | --- | --- |
| 1 | **User** | `users` | Tối giản, chỉ lưu định danh (`id`, `name`, `createdAt`). Mọi tri thức về user nằm ở `UserProfile` / `Fact`. |
| 2 | **UserProfile** | `user_profiles` | Container cho tập hợp mở các `Fact`. Không lưu cứng cột sở thích. |
| 3 | **Fact** | `facts` | Tri thức trích xuất (`key`, `value`, `confidence`, `sourceSessionId`, `updatedAt`). `updatedAt` bắt buộc để xử lý conflict theo thời gian. |
| 4 | **ConversationSession** | `conversation_sessions` | Phiên tương tác (`channel`: VOICE/TEXT, `startedAt`, `endedAt`). `endedAt` null khi đang mở; dùng trigger Extraction Step khi kết thúc. |
| 5 | **Message** | `messages` | Lượt nói trong session (`role`: USER/AGENT/SYSTEM, `content`, `timestamp`). |
| 6 | **EpisodicMemory** | `episodic_memories` | Tóm tắt sự kiện dài hạn (`summary`, `timestamp`, `embeddingRef` trỏ tới Qdrant). `timestamp` là tín hiệu ranking bậc nhất cho recency. |
| 7 | **ToolCall** | `tool_calls` | Lịch sử gọi tool (`parameters` và `result` tách riêng để lọc qua Presidio; `status` chống fail âm thầm). |
| 8 | **Confirmation** | `confirmations` | Xác nhận human-in-the-loop (`status`: PENDING/APPROVED/REJECTED/TIMEOUT_DENIED, `requestedAt`, `respondedAt`). |
| 9 | **ScheduledTask** | `scheduled_tasks` | Quản lý lịch chạy Quartz (`cronExpression`, `taskType`: `SIMPLE_REMINDER` hoặc `AGENT_TASK`). |
| 10 | **Notification** | `notifications` | Bản ghi thông báo gửi tới user (`sentAt` ghi nhận thời điểm gửi thực tế, hỗ trợ catch-up logic khi máy tắt). |
