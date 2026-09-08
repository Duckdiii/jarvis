# Voice Layer (Process 3)

Xử lý âm thanh, phát hiện giọng nói, chuyển đổi giọng nói thành văn bản và ngược lại.

## Cấu trúc thư mục
```
voice-layer/
├── src/
│   ├── stt/          # PhoWhisper wrapper (benchmark ở Phase 1)
│   ├── tts/          # Piper TTS wrapper
│   ├── vad/          # Silero VAD & barge-in
│   └── wakeword/     # openWakeWord
├── pyproject.toml
└── CLAUDE.md
```
