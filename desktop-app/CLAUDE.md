# Desktop App — Guidelines & Conventions

Module `desktop-app` đóng vai trò là Process 5 trong hệ thống Jarvis.

## Phạm vi trách nhiệm
- Giao diện người dùng (UI), System Tray icon.
- Popup yêu cầu xác nhận hành động nguy hiểm (`Confirmation` dialogs).
- Hiển thị trạng thái hoạt động của các tiến trình Jarvis.
- Kết nối tới Gateway qua WebSocket.

## Công nghệ & Quy chuẩn
- **Shell/Runtime**: Tauri v2 (Rust)
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Lệnh thực thi**:
  - `pnpm dev` hoặc `cargo tauri dev`
  - `pnpm build` hoặc `cargo tauri build`
