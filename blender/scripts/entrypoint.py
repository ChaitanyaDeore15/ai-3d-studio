"""
Blender CLI Automation Entrypoint
Accepts CLI arguments passed after '--':
  <input_spec_json> <output_model_path> <output_report_json>
"""
import sys
import os
import json

# Ensure blender/scripts is in sys.path so relative imports work
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from procedural.builder import BUILDER_REGISTRY
from export.exporter import export_glb, export_gltf_package, calculate_mesh_statistics

def main():
    # Arguments after '--'
    try:
        idx = sys.argv.index("--")
        cli_args = sys.argv[idx + 1:]
    except ValueError:
        cli_args = []

    if len(cli_args) < 3:
        print("Usage: blender --background --python entrypoint.py -- <spec_json> <output_model> <report_json>", file=sys.stderr)
        sys.exit(1)

    spec_path = cli_args[0]
    out_path = cli_args[1]
    report_path = cli_args[2]

    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            spec = json.load(f)

        category = spec.get("object_category", "").lower().strip()
        builder_fn = BUILDER_REGISTRY.get(category)
        if not builder_fn:
            raise ValueError(f"Unsupported procedural category: '{category}'. Supported categories: {list(BUILDER_REGISTRY.keys())}")

        # Build mesh
        builder_fn(spec.get("parameters", {}))

        # Check export format
        export_fmt = spec.get("export_format", "glb").lower()
        if export_fmt in ("glb", "model.glb") or out_path.endswith(".glb"):
            stats = export_glb(out_path)
        elif export_fmt in ("gltf", "gltf_zip", "zip") or out_path.endswith(".zip"):
            stats = export_gltf_package(out_path)
        else:
            stats = export_glb(out_path)

        report = {
            "success": True,
            "category": category,
            "statistics": stats,
            "output_path": out_path,
            "error": None
        }

    except Exception as e:
        import traceback
        report = {
            "success": False,
            "category": spec.get("object_category") if 'spec' in locals() else None,
            "statistics": None,
            "output_path": None,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(f"Blender Execution Error: {e}", file=sys.stderr)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    if not report["success"]:
        sys.exit(2)

if __name__ == "__main__":
    main()
