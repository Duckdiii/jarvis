# Voice Layer — Guidelines & Conventions

Module `voice-layer` đóng vai trò là Process 3 trong hệ thống Jarvis.

## Phạm vi trách nhiệm
- **Wake-word**: openWakeWord (phát hiện từ khóa kích hoạt "Jarvis").
- **Voice Activity Detection (VAD) & Barge-in**: Silero VAD (ngắt lời bot khi người dùng bắt đầu nói).
- **Speech-to-Text (STT)**: Wrapper cho PhoWhisper (PhoWhisper-small vs LoRA code-switching sẽ được benchmark trên RTX 3050 6GB VRAM ở Phase 1).
- **Text-to-Speech (TTS)**: Wrapper cho Piper TTS (độ trễ thấp, chạy local).
- Giao tiếp với Gateway qua WebSocket trên `127.0.0.1`.

## Quy chuẩn kỹ thuật
- Python 3.10+ / 3.11+, tối ưu hóa GPU CUDA / ONNX Runtime.
- Ưu tiên stream audio theo chunk nhỏ (streaming audio processing) để giảm latency.
- Xử lý mượt mà sự kiện ngắt lời (barge-in interruption).
