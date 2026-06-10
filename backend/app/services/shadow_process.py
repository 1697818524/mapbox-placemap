"""Shadow removal / illumination enhancement service."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from app.config import settings


class ShadowProcessService:
    def __init__(self) -> None:
        self.script_path = settings.SHADOW_SCRIPT_PATH

    def process_to_path(self, input_path: str, output_path: str) -> str:
        """
        Run the local enhancement script in-process.

        This avoids brittle hard-coded external Python paths such as E:\\conda\\python.exe.
        Returns the selected enhancement level: weak / medium / strong.
        """
        input_abs = str(Path(input_path).resolve())
        output = Path(output_path).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        script = Path(self.script_path).resolve()
        if not script.is_file():
            raise FileNotFoundError(f"Shadow script not found: {script}")

        spec = importlib.util.spec_from_file_location("shadow_code", script)
        if not spec or not spec.loader:
            raise RuntimeError(f"Unable to load shadow script: {script}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return str(module.process_image_to_path(input_abs, str(output)))
