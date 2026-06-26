"""Unicode-safe OpenCV image IO helpers for Windows paths."""
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


def imread_color(path: str) -> Optional[np.ndarray]:
    raw = np.fromfile(path, dtype=np.uint8)
    if raw.size == 0:
        return None
    return cv2.imdecode(raw, cv2.IMREAD_COLOR)


def imwrite(path: str, img: np.ndarray) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    ext = out.suffix or ".png"
    ok, encoded = cv2.imencode(ext, img)
    if not ok:
        raise RuntimeError(f"Cannot encode image: {path}")
    encoded.tofile(str(out))
