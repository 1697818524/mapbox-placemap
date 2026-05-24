"""
语义分割服务（调用 OneFormer 脚本）
"""
from __future__ import annotations

from pathlib import Path
import subprocess

from app.config import settings


class SemanticSegmentService:
    def __init__(self) -> None:
        self.python_exe = settings.PIPELINE_PYTHON_EXE
        self.script_path = settings.ONEFORMER_SCRIPT_PATH
        self.model_dir = settings.ONEFORMER_MODEL_DIR
        self.local_files_only = settings.ONEFORMER_LOCAL_FILES_ONLY
        self.device = settings.ONEFORMER_DEVICE

    def run_on_image(self, input_path: str, output_path: str) -> None:
        """
        调用 OneFormer 脚本，输出语义可视化图。
        """
        input_abs = str(Path(input_path).resolve())
        output = Path(output_path).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        script_dir = str(Path(self.script_path).resolve().parent)

        command = [
            self.python_exe,
            self.script_path,
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
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=script_dir)
        if result.returncode != 0:
            raise RuntimeError(
                f"Semantic segmentation failed for {input_abs} (code={result.returncode}): {result.stderr or result.stdout}"
            )
