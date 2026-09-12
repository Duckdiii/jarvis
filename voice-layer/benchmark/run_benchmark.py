"""STT Benchmark script for Jarvis Voice Layer (Phase 1 - Subtask 1.5).

Benchmarks 2 model configurations (PhoWhisper-small vs Faster-Whisper-tiny / PhoWhisper-large)
on real hardware (RTX 3050, 6GB VRAM) across:
- Group A: Pure Vietnamese (Thuần Việt)
- Group B: Code-switching (Việt - Anh kỹ thuật)

Measures and logs:
- Peak VRAM allocation (MB)
- Execution time per sentence (ms)
- Recognized text vs ground truth
Outputs results to console and writes to benchmark/results.csv.
"""

import argparse
import csv
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Thêm voice-layer root vào sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def get_gpu_vram_mb() -> float:
    """Lấy lượng VRAM GPU Nvidia đang sử dụng qua torch hoặc nvidia-smi (MB)."""
    try:
        import torch

        if torch.cuda.is_available():
            return torch.cuda.max_memory_allocated() / (1024 * 1024)
    except Exception:
        pass

    # Fallback qua nvidia-smi
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,nounits,noheader"],
            encoding="utf-8",
        )
        return float(output.strip().split("\n")[0])
    except Exception:
        return 0.0


def parse_sentences(file_path: Path) -> List[Dict[str, str]]:
    """Đọc và phân loại các câu test từ sentences.txt."""
    sentences = []
    current_group = "A"

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "NHÓM A" in line:
                current_group = "A"
                continue
            if "NHÓM B" in line:
                current_group = "B"
                continue
            if line.startswith("#"):
                continue

            if ":" in line:
                sid, text = line.split(":", 1)
                sentences.append({
                    "id": sid.strip(),
                    "group": "Thuần Việt" if current_group == "A" else "Code-switching",
                    "text": text.strip(),
                })
    return sentences


def run_benchmark(
    sentences_file: Path,
    output_csv: Path,
    model1_path: str = "mad1999/pho-whisper-small-ct2",
    model2_path: str = "tiny",
    device: str = "cuda",
    audio_dir: Path | None = None,
) -> None:
    """Chạy benchmark lần lượt 2 model STT và ghi kết quả."""
    from src.stt.engine import STTEngine

    sentences = parse_sentences(sentences_file)
    print(f"Đã tải {len(sentences)} câu test từ {sentences_file}.")

    configs = [
        {"name": "PhoWhisper-small", "path": model1_path},
        {"name": "Faster-Whisper-tiny (Baseline)", "path": model2_path},
    ]

    results: List[Dict[str, str]] = []

    print("\n" + "=" * 80)
    print(f" BẮT ĐẦU BENCHMARK STT TRÊN THIẾT BỊ: {device.upper()}")
    print("=" * 80)

    for cfg in configs:
        model_name = cfg["name"]
        model_path = cfg["path"]
        print(f"\n>>> Đang khởi tạo cấu hình: {model_name} (path: {model_path}) <<<")

        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
        except Exception:
            pass

        try:
            engine = STTEngine(model_path=model_path, device=device)
        except Exception as e:
            print(f"[Lỗi] Không thể nạp model {model_name}: {e}")
            print(f"-> Vui lòng kiểm tra lại file weights/đường dẫn của {model_name}.\n")
            continue

        print(f"\n--- Tiến hành nhận dạng {len(sentences)} câu cho {model_name} ---")
        for item in sentences:
            sid = item["id"]
            group = item["group"]
            original_text = item["text"]

            audio_input = None
            if audio_dir:
                audio_file = audio_dir / f"{sid}.wav"
                if not audio_file.exists():
                    audio_file = audio_dir / f"{sid}.mp3"
                if audio_file.exists():
                    audio_input = str(audio_file)

            if audio_input is None:
                import numpy as np
                audio_input = np.zeros(16000 * 2, dtype=np.float32)

            recognized_text, latency_ms = engine.transcribe_with_timing(audio_input)
            vram_mb = get_gpu_vram_mb()

            results.append({
                "model": model_name,
                "group": group,
                "id": sid,
                "cau_goc": original_text,
                "text_nhan_duoc": recognized_text,
                "thoi_gian_ms": f"{latency_ms:.1f}",
                "vram_mb": f"{vram_mb:.1f}",
            })

            print(f"[{sid}] ({group})")
            print(f"  Gốc : {original_text}")
            print(f"  STT : {recognized_text}")
            print(f"  Chỉ số: {latency_ms:.1f}ms | VRAM peak: {vram_mb:.1f} MB\n")

    # Ghi kết quả ra CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as csvfile:
        fieldnames = ["model", "group", "id", "cau_goc", "text_nhan_duoc", "thoi_gian_ms", "vram_mb"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print("\n" + "=" * 80)
    print(f" BENCHMARK HOÀN TẤT. KẾT QUẢ ĐÃ ĐƯỢC GHI VÀO: {output_csv}")
    print("=" * 80)


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    default_audio_dir = base_dir / "audio"

    parser = argparse.ArgumentParser(description="Chạy benchmark so sánh các model STT")
    parser.add_argument("--model1", default="mad1999/pho-whisper-small-ct2", help="Đường dẫn hoặc tên model 1")
    parser.add_argument("--model2", default="tiny", help="Đường dẫn hoặc tên model 2")
    parser.add_argument("--device", default="cuda", help="cuda hoặc cpu")
    parser.add_argument("--audio-dir", default=str(default_audio_dir) if default_audio_dir.exists() else None,
                        help="Thư mục chứa file audio (A01.mp3/wav...)")
    args = parser.parse_args()

    sent_file = base_dir / "sentences.txt"
    csv_file = base_dir / "results.csv"

    run_benchmark(
        sentences_file=sent_file,
        output_csv=csv_file,
        model1_path=args.model1,
        model2_path=args.model2,
        device=args.device,
        audio_dir=Path(args.audio_dir) if args.audio_dir else None,
    )
