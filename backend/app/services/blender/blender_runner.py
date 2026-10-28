import os
import subprocess
import json
import tempfile
import sys
import shutil
from typing import Dict, Any, Optional
from backend.app.core.config import settings

class BlenderRunner:
    def __init__(self, blender_path: Optional[str] = None):
        self.blender_path = blender_path or settings.BLENDER_PATH
        self.entrypoint_script = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../../blender/scripts/entrypoint.py")
        )

    def _resolve_binary(self) -> Optional[str]:
        if not self.blender_path:
            return None
        if os.path.isfile(self.blender_path):
            return self.blender_path
        return shutil.which(self.blender_path)

    def is_available(self) -> bool:
        return self._resolve_binary() is not None

    def get_version(self) -> Optional[str]:
        binary = self._resolve_binary()
        if not binary:
            return None
        try:
            cmd = [
                binary,
                "--background",
                "--python-expr",
                "import bpy; print('BLENDER_VERSION_OUT:', bpy.app.version_string)"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            for line in res.stdout.splitlines():
                if "BLENDER_VERSION_OUT:" in line:
                    return line.split("BLENDER_VERSION_OUT:")[1].strip()
            return "Blender"
        except Exception:
            return None

    def execute_procedural_generation(
        self,
        category: str,
        parameters: Dict[str, Any],
        export_format: str = "glb"
    ) -> Dict[str, Any]:
        """
        Executes Blender in background mode to build and export a procedural 3D model.
        Returns dictionary containing output_path, statistics, and validation.
        """
        binary = self._resolve_binary()
        if not binary:
            raise RuntimeError(f"Blender executable not found at '{self.blender_path}'")

        if not os.path.isfile(self.entrypoint_script):
            raise RuntimeError(f"Blender entrypoint script missing at '{self.entrypoint_script}'")

        with tempfile.TemporaryDirectory() as tmpdir:
            spec_path = os.path.join(tmpdir, "spec.json")
            out_ext = ".zip" if export_format == "gltf_zip" else ".glb"
            out_model_path = os.path.join(tmpdir, f"model{out_ext}")
            report_path = os.path.join(tmpdir, "report.json")

            spec_content = {
                "object_category": category,
                "export_format": export_format,
                "parameters": parameters
            }

            with open(spec_path, "w", encoding="utf-8") as f:
                json.dump(spec_content, f)

            cmd = [
                binary,
                "--background",
                "--python",
                self.entrypoint_script,
                "--",
                spec_path,
                out_model_path,
                report_path
            ]

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = proc.communicate(timeout=settings.BLENDER_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                proc.kill()
                raise TimeoutError(f"Blender generation timed out after {settings.BLENDER_TIMEOUT_SECONDS}s")

            if not os.path.exists(report_path):
                raise RuntimeError(
                    f"Blender failed to produce execution report. Exit code: {proc.returncode}. Log: {stderr or stdout}"
                )

            with open(report_path, "r", encoding="utf-8") as rf:
                report = json.load(rf)

            if not report.get("success"):
                err_msg = report.get("error", "Unknown Blender generation failure")
                raise RuntimeError(f"Procedural generation failed: {err_msg}")

            if not os.path.exists(out_model_path) or os.path.getsize(out_model_path) == 0:
                raise RuntimeError("Generated model file is missing or zero bytes")

            # Read file bytes to return
            with open(out_model_path, "rb") as mf:
                model_bytes = mf.read()

            return {
                "model_bytes": model_bytes,
                "file_extension": out_ext.lstrip("."),
                "report": report
            }
