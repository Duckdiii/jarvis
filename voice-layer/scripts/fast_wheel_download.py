import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def download_chunk_to_part(url: str, start_byte: int, end_byte: int, part_path: Path) -> int:
    target_len = end_byte - start_byte + 1

    # Nếu file part đã tồn tại và đủ dung lượng thì bỏ qua
    if part_path.exists() and part_path.stat().st_size == target_len:
        print(f"  [Cached] {part_path.name} đã đủ dung lượng.", flush=True)
        return target_len

    for attempt in range(15):
        current_len = part_path.stat().st_size if part_path.exists() else 0
        if current_len == target_len:
            return target_len

        cur_start = start_byte + current_len
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Range": f"bytes={cur_start}-{end_byte}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                with open(part_path, "ab") as f:
                    while chunk := resp.read(1024 * 512):
                        f.write(chunk)

            if part_path.stat().st_size == target_len:
                return target_len
        except Exception as e:
            print(f"  [Retry {attempt+1}/15] {part_path.name} ({e}), tiếp tục từ offset {part_path.stat().st_size if part_path.exists() else 0}...", flush=True)
            time.sleep(1)

    raise RuntimeError(f"Thất bại khi tải {part_path.name} sau 15 lần thử")


def download_url(url: str, final_file: Path, num_threads: int = 8) -> None:
    final_file.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = final_file.parent / f".tmp_{final_file.stem}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}, method="HEAD")
    with urllib.request.urlopen(req, timeout=15) as resp:
        content_length = int(resp.headers.get("Content-Length", 0))

    print(f"Bắt đầu tải {final_file.name} ({content_length / (1024*1024):.1f} MB) bằng {num_threads} luồng...", flush=True)
    chunk_size = (content_length + num_threads - 1) // num_threads

    chunks = []
    for i in range(num_threads):
        start = i * chunk_size
        end = min(start + chunk_size - 1, content_length - 1)
        if start <= end:
            part_path = temp_dir / f"chunk_{i:03d}.part"
            chunks.append((i, start, end, part_path))

    t0 = time.time()
    downloaded_bytes = 0

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {
            executor.submit(download_chunk_to_part, url, start, end, part_path): (i, part_path)
            for (i, start, end, part_path) in chunks
        }
        for future in as_completed(futures):
            downloaded_bytes += future.result()
            elapsed = time.time() - t0
            speed = (downloaded_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
            pct = (downloaded_bytes / content_length) * 100
            print(f"  [{pct:.1f}%] {downloaded_bytes / (1024*1024):.1f}/{content_length / (1024*1024):.1f} MB ({speed:.2f} MB/s)", flush=True)

    print("Đang ghép các phần tải về...", flush=True)
    with open(final_file, "wb") as outfile:
        for (i, start, end, part_path) in chunks:
            with open(part_path, "rb") as infile:
                while chunk := infile.read(1024 * 1024 * 8):
                    outfile.write(chunk)
            part_path.unlink()

    temp_dir.rmdir()
    total_time = time.time() - t0
    avg_speed = (content_length / (1024 * 1024)) / total_time
    print(f"[Xong] Đã tải hoàn chỉnh {final_file.name} trong {total_time:.1f}s ({avg_speed:.2f} MB/s)!", flush=True)


if __name__ == "__main__":
    url = sys.argv[1]
    out = Path(sys.argv[2])
    download_url(url, out, num_threads=12)
