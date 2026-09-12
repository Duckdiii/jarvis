"""Fast multi-threaded downloader for HuggingFace models."""

import os
import sys
import time
import urllib.request
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def download_chunk(url: str, start_byte: int, end_byte: int, filepath: Path) -> int:
    """Tải một byte range và ghi trực tiếp vào file tại offset tương ứng."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Range": f"bytes={start_byte}-{end_byte}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    
    with open(filepath, "r+b") as f:
        f.seek(start_byte)
        f.write(data)
    return len(data)


def download_file_multithread(url: str, dest_path: Path, max_workers: int = 8, chunk_size: int = 8 * 1024 * 1024) -> None:
    """Tải 1 file lớn bằng nhiều luồng HTTP Range requests."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Lấy content length và direct url nếu redirect
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        direct_url = resp.geturl()
        content_length = int(resp.headers.get("Content-Length", 0))
    
    if content_length == 0:
        print(f"[Warn] File {dest_path.name} không có Content-Length, tải đơn luồng...")
        with urllib.request.urlopen(direct_url, timeout=60) as resp, open(dest_path, "wb") as f:
            f.write(resp.read())
        return

    # Nếu file đã tồn tại và đúng kích thước thì bỏ qua
    if dest_path.exists() and dest_path.stat().st_size == content_length:
        print(f"[OK] {dest_path.name} ({content_length / (1024*1024):.1f} MB) đã tồn tại đầy đủ.")
        return

    print(f"Bắt đầu tải {dest_path.name} ({content_length / (1024*1024):.1f} MB) bằng {max_workers} luồng...")
    
    # Tạo pre-allocated file
    with open(dest_path, "wb") as f:
        f.truncate(content_length)

    ranges = []
    for start in range(0, content_length, chunk_size):
        end = min(start + chunk_size - 1, content_length - 1)
        ranges.append((start, end))

    total_downloaded = 0
    t0 = time.time()
    last_print = t0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_chunk, direct_url, r[0], r[1], dest_path) for r in ranges]
        for f in as_completed(futures):
            downloaded = f.result()
            total_downloaded += downloaded
            now = time.time()
            if now - last_print > 2.0 or total_downloaded == content_length:
                elapsed = now - t0
                speed_mb = (total_downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                pct = (total_downloaded / content_length) * 100
                print(f"  -> {pct:.1f}% ({total_downloaded / (1024*1024):.1f}/{content_length / (1024*1024):.1f} MB) - {speed_mb:.2f} MB/s", flush=True)
                last_print = now

    total_time = time.time() - t0
    avg_speed = (content_length / (1024 * 1024)) / total_time if total_time > 0 else 0
    print(f"[Thành công] Đã tải {dest_path.name} trong {total_time:.1f}s (Trung bình: {avg_speed:.2f} MB/s)\n")


def download_hf_repo(repo_id: str, target_dir: Path, max_workers: int = 8) -> None:
    """Tải toàn bộ model repo từ HuggingFace."""
    target_dir.mkdir(parents=True, exist_ok=True)
    api_url = f"https://huggingface.co/api/models/{repo_id}"
    req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    siblings = data.get("siblings", [])
    print(f"=== Đang tải repo HuggingFace: {repo_id} ({len(siblings)} files) ===")
    for s in siblings:
        rfilename = s["rfilename"]
        if rfilename.startswith(".") or rfilename.endswith(".md"):
            continue
        file_url = f"https://huggingface.co/{repo_id}/resolve/main/{rfilename}"
        dest_path = target_dir / rfilename
        download_file_multithread(file_url, dest_path, max_workers=max_workers)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        repo = sys.argv[1]
        out_dir = Path(sys.argv[2])
        download_hf_repo(repo, out_dir)
    else:
        print("Usage: python fast_download.py <repo_id> <output_dir>")
