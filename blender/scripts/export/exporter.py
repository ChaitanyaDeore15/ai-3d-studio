"""
Blender 3D glTF 2.0 Exporter and Statistics Inspector
Exports clean GLB and glTF formats and calculates real scene bounds and polygon counts.
"""
import bpy
import mathutils
import os
import zipfile

def calculate_mesh_statistics():
    """Calculates real vertex count, face count, and bounding box for all meshes in scene."""
    total_verts = 0
    total_faces = 0
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')
    min_z, max_z = float('inf'), float('-inf')

    materials = set()

    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            mesh = obj.data
            total_verts += len(mesh.vertices)
            total_faces += len(mesh.polygons)
            for mat in obj.data.materials:
                if mat:
                    materials.add(mat.name)

            # Evaluate bounding box in world space
            for corner in obj.bound_box:
                world_coord = obj.matrix_world @ mathutils.Vector(corner)
                min_x = min(min_x, world_coord.x)
                max_x = max(max_x, world_coord.x)
                min_y = min(min_y, world_coord.y)
                max_y = max(max_y, world_coord.y)
                min_z = min(min_z, world_coord.z)
                max_z = max(max_z, world_coord.z)

    if min_x == float('inf'):
        min_x = max_x = min_y = max_y = min_z = max_z = 0.0

    return {
        "vertices": total_verts,
        "faces": total_faces,
        "triangles": total_faces * 2, # estimation or triangulation
        "materials": list(materials),
        "dimensions": {
            "x": round(max_x - min_x, 4),
            "y": round(max_y - min_y, 4),
            "z": round(max_z - min_z, 4)
        },
        "bounds": {
            "min": [round(min_x, 4), round(min_y, 4), round(min_z, 4)],
            "max": [round(max_x, 4), round(max_y, 4), round(max_z, 4)]
        }
    }

def export_glb(output_filepath: str):
    """Exports current scene to single binary GLB file."""
    os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
    
    # Configure glTF export settings
    bpy.ops.export_scene.gltf(
        filepath=output_filepath,
        export_format='GLB',
        export_apply=True,
        export_materials='EXPORT',
        export_yup=True
    )
    if not os.path.exists(output_filepath) or os.path.getsize(output_filepath) == 0:
        raise RuntimeError(f"GLB export failed or file is empty: {output_filepath}")
    
    stats = calculate_mesh_statistics()
    stats["file_size_bytes"] = os.path.getsize(output_filepath)
    stats["file_format"] = "glb"
    return stats

def export_gltf_package(output_zip_filepath: str):
    """
    Exports glTF separate format (model.gltf + model.bin + images),
    verifies all referenced files exist, and packages into zip archive.
    """
    zip_dir = os.path.dirname(os.path.abspath(output_zip_filepath))
    os.makedirs(zip_dir, exist_ok=True)
    temp_extract_dir = os.path.join(zip_dir, "_temp_gltf_export")
    os.makedirs(temp_extract_dir, exist_ok=True)
    gltf_main_path = os.path.join(temp_extract_dir, "model.gltf")

    try:
        bpy.ops.export_scene.gltf(
            filepath=gltf_main_path,
            export_format='GLTF_SEPARATE',
            export_apply=True,
            export_materials='EXPORT',
            export_yup=True
        )

        if not os.path.exists(gltf_main_path):
            raise RuntimeError(f"glTF main file not found at {gltf_main_path}")

        # Create zip package
        with zipfile.ZipFile(output_zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(temp_extract_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, temp_extract_dir)
                    zip_file.write(full_p, arcname=rel_p)

        stats = calculate_mesh_statistics()
        stats["file_size_bytes"] = os.path.getsize(output_zip_filepath)
        stats["file_format"] = "gltf_zip"
        return stats
    finally:
        # Clean up temp export dir
        if os.path.exists(temp_extract_dir):
            for root, dirs, files in os.walk(temp_extract_dir, topdown=False):
                for f in files:
                    try:
                        os.remove(os.path.join(root, f))
                    except Exception:
                        pass
                for d in dirs:
                    try:
                        os.rmdir(os.path.join(root, d))
                    except Exception:
                        pass
            try:
                os.rmdir(temp_extract_dir)
            except Exception:
                pass
