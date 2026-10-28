"""
Blender 3D Procedural Material Generator
Creates standard PBR Principled BSDF materials with configurable properties.
"""
import bpy

def get_or_create_material(name: str, base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.5, metallic=0.0, emission_color=None, emission_strength=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                bsdf = node
                break
    if not bsdf:
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        output = nodes.get("Material Output")
        if not output:
            output = nodes.new(type="ShaderNodeOutputMaterial")
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # In Blender 4.0+, Base Color is inputs[0] or inputs['Base Color']
    if "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = base_color
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = roughness
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = metallic

    if emission_color and emission_strength > 0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_color
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = emission_color
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission_strength

    return mat

PRESETS = {
    "wood": {"base_color": (0.55, 0.35, 0.20, 1.0), "roughness": 0.65, "metallic": 0.0},
    "dark_wood": {"base_color": (0.25, 0.15, 0.08, 1.0), "roughness": 0.60, "metallic": 0.0},
    "metal_steel": {"base_color": (0.75, 0.76, 0.78, 1.0), "roughness": 0.30, "metallic": 0.90},
    "metal_gold": {"base_color": (1.0, 0.78, 0.28, 1.0), "roughness": 0.25, "metallic": 0.95},
    "metal_black": {"base_color": (0.1, 0.1, 0.1, 1.0), "roughness": 0.40, "metallic": 0.85},
    "plastic_white": {"base_color": (0.92, 0.92, 0.92, 1.0), "roughness": 0.25, "metallic": 0.0},
    "plastic_blue": {"base_color": (0.12, 0.45, 0.85, 1.0), "roughness": 0.30, "metallic": 0.0},
    "plastic_red": {"base_color": (0.85, 0.15, 0.15, 1.0), "roughness": 0.30, "metallic": 0.0},
    "fabric_cushion": {"base_color": (0.35, 0.42, 0.45, 1.0), "roughness": 0.85, "metallic": 0.0},
    "glass": {"base_color": (0.9, 0.95, 1.0, 1.0), "roughness": 0.05, "metallic": 0.0},
    "concrete": {"base_color": (0.5, 0.5, 0.52, 1.0), "roughness": 0.90, "metallic": 0.0},
    "asphalt": {"base_color": (0.18, 0.18, 0.19, 1.0), "roughness": 0.95, "metallic": 0.0},
    "road_marking": {"base_color": (0.95, 0.85, 0.1, 1.0), "roughness": 0.70, "metallic": 0.0},
    "marble": {"base_color": (0.95, 0.94, 0.92, 1.0), "roughness": 0.15, "metallic": 0.05},
    "roof_tile": {"base_color": (0.65, 0.22, 0.15, 1.0), "roughness": 0.80, "metallic": 0.0},
    "wall_paint": {"base_color": (0.88, 0.86, 0.82, 1.0), "roughness": 0.75, "metallic": 0.0},
    "emission_glow": {"base_color": (0.2, 0.6, 1.0, 1.0), "roughness": 0.2, "metallic": 0.1, "emission_color": (0.2, 0.6, 1.0, 1.0), "emission_strength": 3.0}
}

def resolve_material(preset_name_or_dict, custom_color_hex=None):
    if isinstance(preset_name_or_dict, str) and preset_name_or_dict in PRESETS:
        p = dict(PRESETS[preset_name_or_dict])
    elif isinstance(preset_name_or_dict, dict):
        p = dict(preset_name_or_dict)
    else:
        p = dict(PRESETS["wood"])

    if custom_color_hex and custom_color_hex.startswith("#") and len(custom_color_hex) in (7, 9):
        try:
            r = int(custom_color_hex[1:3], 16) / 255.0
            g = int(custom_color_hex[3:5], 16) / 255.0
            b = int(custom_color_hex[5:7], 16) / 255.0
            p["base_color"] = (r, g, b, 1.0)
        except Exception:
            pass

    mat_name = f"Mat_{preset_name_or_dict if isinstance(preset_name_or_dict, str) else 'custom'}"
    return get_or_create_material(
        name=mat_name,
        base_color=p.get("base_color", (0.8, 0.8, 0.8, 1.0)),
        roughness=p.get("roughness", 0.5),
        metallic=p.get("metallic", 0.0),
        emission_color=p.get("emission_color"),
        emission_strength=p.get("emission_strength", 0.0)
    )
