# Docker Sandbox Environment

Thư mục chứa cấu hình Docker sandbox container pool dùng cho công cụ `shell_exec` của `agent-runtime`.

## Yêu cầu bảo mật
- Container pool phải bị cô lập (giới hạn CPU, RAM, Network).
- Mọi lệnh nguy hiểm hoặc có side-effect phải được kiểm soát chặt chẽ và yêu cầu Human-in-the-loop confirmation.
