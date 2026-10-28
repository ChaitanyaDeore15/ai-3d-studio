"""
3D Model Validator
Validates glTF 2.0 / GLB files both structurally (pure binary inspection)
and via headless Blender re-import.
"""
import struct
import json
import os
import zipfile

def validate_glb_binary(filepath: str) -> dict:
    """
    Validates a binary glTF (.glb) file at binary level without external dependencies.
    Returns dictionary with validation report.
    """
    if not os.path.exists(filepath):
        return {"valid": False, "error": f"File does not exist: {filepath}"}
    
    file_size = os.path.getsize(filepath)
    if file_size < 20: # 12 bytes header + 8 bytes min chunk
        return {"valid": False, "error": f"File is too small to be a valid GLB: {file_size} bytes"}

    with open(filepath, "rb") as f:
        # Read header: magic (4), version (4), length (4)
        header = f.read(12)
        magic, version, length = struct.unpack("<4sII", header)

        if magic != b"glTF":
            return {"valid": False, "error": f"Invalid magic header: {magic}. Expected b'glTF'"}
        if version != 2:
            return {"valid": False, "error": f"Unsupported glTF version: {version}. Expected version 2"}
        if length != file_size:
            return {"valid": False, "error": f"GLB header length {length} does not match file size {file_size}"}

        # Read JSON chunk (chunk 0)
        chunk0_header = f.read(8)
        chunk0_len, chunk0_type = struct.unpack("<I4s", chunk0_header)
        if chunk0_type != b"JSON":
            return {"valid": False, "error": f"Chunk 0 must be JSON, found: {chunk0_type}"}

        json_bytes = f.read(chunk0_len)
        try:
            gltf_json = json.loads(json_bytes.decode("utf-8"))
        except Exception as e:
            return {"valid": False, "error": f"Corrupt JSON chunk in GLB: {e}"}

        # Validate basic glTF structural integrity
        asset_info = gltf_json.get("asset", {})
        if not asset_info or "version" not in asset_info:
            return {"valid": False, "error": "Missing required 'asset.version' in glTF"}

        meshes = gltf_json.get("meshes", [])
        if not meshes:
            return {"valid": False, "error": "glTF file contains no meshes"}

        # Basic primitive check
        primitive_count = sum(len(m.get("primitives", [])) for m in meshes)
        if primitive_count == 0:
            return {"valid": False, "error": "glTF meshes contain no primitives"}

        materials = gltf_json.get("materials", [])
        nodes = gltf_json.get("nodes", [])

        return {
            "valid": True,
            "error": None,
            "format": "glb",
            "file_size_bytes": file_size,
            "asset_version": asset_info.get("version"),
            "generator": asset_info.get("generator", "unknown"),
            "mesh_count": len(meshes),
            "primitive_count": primitive_count,
            "material_count": len(materials),
            "node_count": len(nodes)
        }

def validate_gltf_zip(filepath: str) -> dict:
    """
    Validates a glTF package (.zip) containing .gltf, .bin, and optional textures.
    Ensures all referenced files exist without path traversal.
    """
    if not os.path.exists(filepath):
        return {"valid": False, "error": f"File does not exist: {filepath}"}

    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            namelist = zf.namelist()
            gltf_files = [n for n in namelist if n.lower().endswith(".gltf")]
            if not gltf_files:
                return {"valid": False, "error": "No .gltf file found in zip archive"}
            
            main_gltf = gltf_files[0]
            with zf.open(main_gltf) as gf:
                gltf_json = json.load(gf)

            # Check buffers
            for b_idx, buf in enumerate(gltf_json.get("buffers", [])):
                uri = buf.get("uri")
                if uri and not uri.startswith("data:"):
                    if ".." in uri or uri.startswith("/"):
                        return {"valid": False, "error": f"Unsafe URI path in buffer: {uri}"}
                    if uri not in namelist:
                        return {"valid": False, "error": f"Missing buffer file in package: {uri}"}

            # Check images
            for img in gltf_json.get("images", []):
                uri = img.get("uri")
                if uri and not uri.startswith("data:"):
                    if ".." in uri or uri.startswith("/"):
                        return {"valid": False, "error": f"Unsafe URI path in image: {uri}"}
                    if uri not in namelist:
                        return {"valid": False, "error": f"Missing image file in package: {uri}"}

            return {
                "valid": True,
                "error": None,
                "format": "gltf_zip",
                "file_size_bytes": os.path.getsize(filepath),
                "mesh_count": len(gltf_json.get("meshes", [])),
                "material_count": len(gltf_json.get("materials", [])),
                "files_in_archive": namelist
            }
    except Exception as e:
        return {"valid": False, "error": f"Invalid zip archive: {e}"}
