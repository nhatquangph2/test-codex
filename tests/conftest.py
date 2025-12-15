import sys
from pathlib import Path

# Đảm bảo thư mục gốc nằm trong PYTHONPATH khi chạy pytest
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
