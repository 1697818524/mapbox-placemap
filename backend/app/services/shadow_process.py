"""
去阴影/光照增强服务
"""
from __future__ import annotations

from pathlib import Path
import subprocess

from app.config import settings


class ShadowProcessService:
    def __init__(self) -> None:
        self.python_exe = settings.PIPELINE_PYTHON_EXE
        self.script_path = settings.SHADOW_SCRIPT_PATH

    def process_to_path(self, input_path: str, output_path: str) -> str:
        """
        调用 code.py 中的 process_image_to_path 处理单图。
        返回所选参数档位（weak/medium/strong）。
        """
        input_abs = str(Path(input_path).resolve())
        output = Path(output_path).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        command = [
            self.python_exe,
            "-c",
            (
                "import importlib.util;"
                f"spec=importlib.util.spec_from_file_location('shadow_code', r'{self.script_path}');"
                "m=importlib.util.module_from_spec(spec);"
                "spec.loader.exec_module(m);"
                f"print(m.process_image_to_path(r'{input_abs}', r'{str(output)}'))"
            ),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=str(Path(self.script_path).resolve().parent))
        if result.returncode != 0:
            raise RuntimeError(
                f"Shadow process failed for {input_abs} (code={result.returncode}): {result.stderr or result.stdout}"
            )
        # 最后一行通常是 level
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return lines[-1] if lines else "unknown"
