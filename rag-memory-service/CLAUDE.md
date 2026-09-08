# RAG Memory Service — Guidelines & Conventions

Module `rag-memory-service` đóng vai trò là Process 4 (tái dùng pipeline từ LawVN).

> [!NOTE]
> Trạng thái kiến trúc: **Tách riêng — chờ quyết định gộp vào `agent-runtime` (Defining scope §7)**.
> Tuyệt đối KHÔNG tự ý gộp hoặc xóa module này khi chưa có quyết định chính thức từ người dùng.

## Phạm vi trách nhiệm
- Cung cấp dịch vụ truy hồi thông tin (RAG), tìm kiếm ngữ nghĩa cho tài liệu dài hạn và episodic memory.
- Framework: Python + FastAPI.
