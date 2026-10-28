import os
import sys

# Ensure repository root is in python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from blender.scripts.validation.validator import validate_glb_binary, validate_gltf_zip

def validate_3d_asset_file(filepath: str, format_hint: str = "glb") -> dict:
    """
    Validates a generated or uploaded 3D model.
    Checks headers, structure, JSON chunks, and non-empty mesh components.
    """
    if not os.path.exists(filepath):
        return {"valid": False, "error": f"Asset file missing: {filepath}"}

    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".glb" or format_hint == "glb":
        return validate_glb_binary(filepath)
    elif ext == ".zip" or format_hint in ("gltf", "gltf_zip"):
        return validate_gltf_zip(filepath)
    else:
        return {"valid": False, "error": f"Unsupported 3D asset file extension: {ext}"}
