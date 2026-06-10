"""
超像素分割服务
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from skimage.segmentation import slic

from app.utils.image_io import imread_color, imwrite


class SuperpixelService:
    def run_slic(self, image_path: str, n_segments: int, compactness: float) -> np.ndarray:
        img_bgr = imread_color(image_path)
        if img_bgr is None:
            raise FileNotFoundError(f"Image not found: {image_path}")
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        segments = slic(
            img_rgb,
            n_segments=max(50, int(n_segments)),
            compactness=float(compactness),
            sigma=1.0,
            start_label=0,
            enforce_connectivity=True,
        )
        return segments.astype(np.int32)

    def save_segments(self, segments: np.ndarray, labels_npy_path: str, labels_png_path: str) -> None:
        labels_npy = Path(labels_npy_path)
        labels_png = Path(labels_png_path)
        labels_npy.parent.mkdir(parents=True, exist_ok=True)
        labels_png.parent.mkdir(parents=True, exist_ok=True)

        np.save(labels_npy, segments)

        viz = np.zeros((*segments.shape, 3), dtype=np.uint8)
        uniq = np.unique(segments)
        for i, seg_id in enumerate(uniq):
            viz[segments == seg_id] = np.array(
                [(i * 37) % 256, (i * 73) % 256, (i * 109) % 256],
                dtype=np.uint8,
            )
        imwrite(str(labels_png), cv2.cvtColor(viz, cv2.COLOR_RGB2BGR))
