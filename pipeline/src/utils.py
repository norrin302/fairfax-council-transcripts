from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any


def hhmmss(seconds: float) -> str:
    s = max(0, int(math.floor(float(seconds or 0))))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"


def norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

