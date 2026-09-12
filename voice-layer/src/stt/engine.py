import sys
import time
from pathlib import Path
from typing import Tuple, Union
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


class STTEngine:
    """Speech-to-Text Engine bọc quanh thư viện faster-whisper.

    Bắt buộc tham số hóa model_path và device để phục vụ benchmark đổi qua lại
    mà không cần sửa code gọi.
    """

    def __init__(
        self,
        model_path: str,
        device: str = "cuda",
        compute_type: str | None = None,
        language: str = "vi",
    ) -> None:
        """Khởi tạo STT Engine.

        Args:
            model_path: Đường dẫn tới model CTranslate2 (hoặc tên repo HuggingFace / size như 'small', 'large-v3').
            device: 'cuda' (GPU) hoặc 'cpu'.
            compute_type: Kiểu tính toán (vd 'float16', 'int8_float16', 'int8', 'float32').
                          Nếu None, tự động chọn 'float16' cho CUDA và 'int8' cho CPU.
            language: Ngôn ngữ mặc định (mặc định 'vi' cho tiếng Việt).
        """
        from faster_whisper import WhisperModel

        self.model_path = model_path
        self.device = device
        self.language = language

        if compute_type is None:
            self.compute_type = "float16" if device == "cuda" else "int8"
        else:
            self.compute_type = compute_type

        print(
            f"[STTEngine] Đang nạp model STT từ '{model_path}' trên device='{self.device}' (compute_type='{self.compute_type}')..."
        )
        start_load = time.perf_counter()
        self.model = WhisperModel(
            self.model_path,
            device=self.device,
            compute_type=self.compute_type,
        )
        load_duration = (time.perf_counter() - start_load) * 1000
        print(f"[STTEngine] Nạp model thành công trong {load_duration:.1f}ms.")

    def transcribe(
        self,
        audio: Union[np.ndarray, str, Path],
        beam_size: int = 5,
        vad_filter: bool = True,
    ) -> str:
        """Chuyển đổi âm thanh (mảng numpy hoặc đường dẫn file WAV) thành văn bản.

        Args:
            audio: Mảng float32 16kHz mono hoặc đường dẫn file âm thanh.
            beam_size: Beam search width (mặc định 5).
            vad_filter: Lọc khoảng lặng bằng VAD tích hợp của faster-whisper.

        Returns:
            str: Đoạn văn bản đã nhận dạng.
        """
        text, _ = self.transcribe_with_timing(audio, beam_size=beam_size, vad_filter=vad_filter)
        return text

    def transcribe_with_timing(
        self,
        audio: Union[np.ndarray, str, Path],
        beam_size: int = 5,
        vad_filter: bool = True,
    ) -> Tuple[str, float]:
        """Chuyển đổi âm thanh và đo đạc chính xác thời gian xử lý (latency ms).

        Returns:
            Tuple[str, float]: (văn_bản_nhận_dạng, thời_gian_xử_lý_ms).
        """
        if isinstance(audio, Path):
            audio = str(audio)

        start_time = time.perf_counter()
        segments, info = self.model.transcribe(
            audio,
            beam_size=beam_size,
            language=self.language,
            vad_filter=vad_filter,
        )
        # Nối toàn bộ các segment văn bản
        text = " ".join([segment.text.strip() for segment in segments]).strip()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return text, elapsed_ms


if __name__ == "__main__":
    print("STTEngine module definition ready.")
