"""Semantic segmentation service with a local fallback."""
from __future__ import annotations

from pathlib import Path
import subprocess

import cv2
import numpy as np

from app.config import settings
from app.utils.image_io import imread_color, imwrite


CITYSCAPES_ROAD = np.array([128, 64, 128], dtype=np.uint8)
CITYSCAPES_BUILDING = np.array([70, 70, 70], dtype=np.uint8)
CITYSCAPES_POLE = np.array([153, 153, 153], dtype=np.uint8)
CITYSCAPES_VEGETATION = np.array([107, 142, 35], dtype=np.uint8)
CITYSCAPES_SKY = np.array([70, 130, 180], dtype=np.uint8)


class SemanticSegmentService:
    def __init__(self) -> None:
        self.python_exe = settings.PIPELINE_PYTHON_EXE
        self.script_path = settings.ONEFORMER_SCRIPT_PATH
        self.model_dir = settings.ONEFORMER_MODEL_DIR
        self.local_files_only = settings.ONEFORMER_LOCAL_FILES_ONLY
        self.device = settings.ONEFORMER_DEVICE

    def run_on_image(self, input_path: str, output_path: str) -> None:
        """
        Prefer the OneFormer script when it exists.

        If the cloned OneFormer script is missing on this machine, write a fast
        Cityscapes-colored heuristic segmentation so the sample pipeline can
        still finish and produce palettes.
        """
        input_abs = str(Path(input_path).resolve())
        output = Path(output_path).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        script = Path(self.script_path).resolve()
        if not script.is_file():
            self._run_fallback(input_abs, str(output))
            return

        command = [
            self.python_exe,
            str(script),
            "--image",
            input_abs,
            "--output",
            str(output),
            "--device",
            self.device,
            "--model-dir",
            self.model_dir,
        ]
        if self.local_files_only:
            command.append("--local-files-only")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                cwd=str(script.parent),
            )
        except FileNotFoundError:
            self._run_fallback(input_abs, str(output))
            return

        if result.returncode != 0:
            raise RuntimeError(
                f"Semantic segmentation failed for {input_abs} "
                f"(code={result.returncode}): {result.stderr or result.stdout}"
            )

    def _run_fallback(self, input_path: str, output_path: str) -> None:
        img_bgr = imread_color(input_path)
        if img_bgr is None:
            raise FileNotFoundError(f"Image not found: {input_path}")

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        h, w = img_rgb.shape[:2]
        yy = np.arange(h)[:, None]

        out = np.zeros_like(img_rgb, dtype=np.uint8)
        out[:] = CITYSCAPES_BUILDING

        hue = hsv[:, :, 0]
        sat = hsv[:, :, 1]
        val = hsv[:, :, 2]

        green = (hue >= 35) & (hue <= 95) & (sat > 45) & (val > 45)
        blue = (hue >= 90) & (hue <= 135) & (sat > 35) & (val > 45)
        lower = yy > int(h * 0.58)
        road = lower & (sat < 70) & (val > 45) & (val < 215)
        landmark = (sat > 80) & (val > 110) & ~(green | blue)

        out[road] = CITYSCAPES_ROAD
        out[green] = CITYSCAPES_VEGETATION
        out[blue] = CITYSCAPES_SKY
        out[landmark] = CITYSCAPES_POLE

        imwrite(output_path, cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
