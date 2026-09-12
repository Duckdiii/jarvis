"""Audio capture module with Push-To-Talk support for Jarvis Voice Layer (Phase 1).

Records audio at 16kHz mono, float32, which is the exact format required by Whisper.
"""

import threading
import time
from pathlib import Path
from typing import List
import numpy as np
import sounddevice as sd
import soundfile as sf
from pynput import keyboard


def record_audio(duration: float = 3.0, sample_rate: int = 16000) -> np.ndarray:
    """Ghi âm micro với thời lượng cố định (phục vụ test tự động hoặc headless)."""
    print(f"Bắt đầu ghi âm trong {duration} giây (Sample rate: {sample_rate}Hz)...")
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    print("Hoàn tất ghi âm.")
    return audio_data.flatten()


def record_on_keypress(trigger_key: str = "space", sample_rate: int = 16000) -> np.ndarray:
    """Ghi âm micro theo cơ chế Push-To-Talk (giữ phím để nói, thả phím để dừng).

    Args:
        trigger_key: Tên phím kích hoạt (mặc định 'space').
        sample_rate: Tần số lấy mẫu âm thanh (mặc định 16000Hz mono cho Whisper).

    Returns:
        np.ndarray: Dữ liệu âm thanh 1D float32 chuẩn hóa trong khoảng [-1.0, 1.0].
    """
    audio_chunks: List[np.ndarray] = []
    is_recording = threading.Event()
    stop_event = threading.Event()

    def audio_callback(indata, frames, time_info, status):
        if status:
            print(f"[Warning SoundDevice] {status}")
        if is_recording.is_set():
            audio_chunks.append(indata.copy())

    def match_key(key) -> bool:
        if trigger_key.lower() == "space":
            return key == keyboard.Key.space
        try:
            return hasattr(key, "char") and key.char.lower() == trigger_key.lower()
        except AttributeError:
            return False

    def on_press(key):
        if match_key(key) and not is_recording.is_set():
            print(f"\n[Microphone] Đang giữ phím '{trigger_key}' -> Bắt đầu ghi âm...")
            is_recording.set()

    def on_release(key):
        if match_key(key) and is_recording.is_set():
            print(f"[Microphone] Đã thả phím '{trigger_key}' -> Dừng ghi âm.")
            is_recording.clear()
            stop_event.set()
            return False  # Dừng listener keyboard

    print(f"=== Push-To-Talk Ready: Hãy NHẤN VÀ GIỮ phím '{trigger_key.upper()}' để nói ===")

    # Bắt đầu stream ghi âm
    with sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        callback=audio_callback,
    ):
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

    if not audio_chunks:
        print("[Warning] Không thu được dữ liệu âm thanh nào.")
        return np.array([], dtype=np.float32)

    concatenated = np.concatenate(audio_chunks, axis=0).flatten()
    duration_sec = len(concatenated) / sample_rate
    print(f"Đã ghi âm thành công {duration_sec:.2f}s ({len(concatenated)} samples).")
    return concatenated


def save_wav(audio: np.ndarray, file_path: str | Path, sample_rate: int = 16000) -> Path:
    """Lưu mảng numpy float32 thành file WAV chuẩn 16kHz mono."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio, sample_rate, subtype="PCM_16")
    print(f"Đã lưu file âm thanh: {path}")
    return path


def load_wav(file_path: str | Path, target_sr: int = 16000) -> np.ndarray:
    """Đọc file WAV và trả về mảng numpy float32 16kHz mono."""
    data, sr = sf.read(str(file_path), dtype="float32")
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)  # Chuyển stereo sang mono
    if sr != target_sr:
        # Resample đơn giản nếu tần số mẫu khác 16kHz
        import scipy.signal

        num_samples = int(len(data) * target_sr / sr)
        data = scipy.signal.resample(data, num_samples)
    return data.astype(np.float32)


def play_audio(audio: np.ndarray, sample_rate: int = 16000) -> None:
    """Phát mảng âm thanh ra loa để kiểm tra (playback verification)."""
    print(f"Đang phát lại âm thanh ({len(audio)/sample_rate:.2f}s)...")
    sd.play(audio, samplerate=sample_rate)
    sd.wait()
    print("Phát xong.")


if __name__ == "__main__":
    print("--- Test module audio/capture.py ---")
    recorded = record_audio(duration=2.0)
    print(f"Recorded shape: {recorded.shape}, Max amplitude: {np.max(np.abs(recorded)):.4f}")
    test_wav = Path("test_recording.wav")
    save_wav(recorded, test_wav)
    loaded = load_wav(test_wav)
    print(f"Loaded shape: {loaded.shape}")
    if test_wav.exists():
        test_wav.unlink()
    print("Test capture module hoàn tất.")
