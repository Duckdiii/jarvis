"""Jarvis Agent Runtime - Root CLI Entry Point."""

import sys
from pathlib import Path

# Thêm thư mục hiện tại vào sys.path để import src thuận tiện
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from src.main import main

if __name__ == "__main__":
    main()
