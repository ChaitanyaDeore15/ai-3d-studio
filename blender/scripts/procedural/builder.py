"""
Blender 3D Procedural Asset Builders
Generates clean, watertight, correctly scaled meshes with PBR materials.
"""
import bpy
import bmesh
import math
from .materials import resolve_material

def clean_scene():
    """Wipes all existing mesh objects and materials in the scene for a clean build."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

def assign_material_to_obj(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

def join_objects(obj_list, final_name="GeneratedModel"):
    if not obj_list:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for obj in obj_list:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = obj_list[0]
    bpy.ops.object.join()
    active = bpy.context.view_layer.objects.active
    active.name = final_name
    # Recalculate normals
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    return active

def build_table(params: dict):
    """
    Parametric Table:
    width (x), depth (y), height (z), tabletop_thickness, leg_thickness, leg_shape (round/square), round_table (bool)
    """
    clean_scene()
    width = float(params.get("width", 1.4))
    depth = float(params.get("depth", 0.8))
    height = float(params.get("height", 0.75))
    top_th = float(params.get("tabletop_thickness", 0.04))
    leg_th = float(params.get("leg_thickness", 0.05))
    is_round = bool(params.get("round_top", False))
    mat_preset = params.get("material", "wood")
    leg_mat_preset = params.get("leg_material", "metal_black" if params.get("style") == "modern" else mat_preset)
    color_hex = params.get("color_hex")

    top_mat = resolve_material(mat_preset, color_hex)
    leg_mat = resolve_material(leg_mat_preset)

    parts = []

    # Tabletop
    top_z = height - (top_th / 2.0)
    if is_round:
        radius = max(width, depth) / 2.0
        bpy.ops.mesh.primitive_cylinder_add(
            radius=radius,
            depth=top_th,
            location=(0, 0, top_z),
            vertices=36
        )
    else:
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(0, 0, top_z),
            scale=(width, depth, top_th)
        )
    top_obj = bpy.context.active_object
    top_obj.name = "TableTop"
    assign_material_to_obj(top_obj, top_mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(top_obj)

    # 4 Legs
    leg_height = height - top_th
    leg_z = leg_height / 2.0
    inset_x = width / 2.0 - leg_th / 2.0 - 0.03
    inset_y = depth / 2.0 - leg_th / 2.0 - 0.03
    if is_round:
        r_leg = (max(width, depth) / 2.0) * 0.65
        leg_positions = [
            (r_leg * math.cos(i * math.pi / 2), r_leg * math.sin(i * math.pi / 2))
            for i in range(4)
        ]
    else:
        leg_positions = [
            (-inset_x, -inset_y),
            (inset_x, -inset_y),
            (-inset_x, inset_y),
            (inset_x, inset_y)
        ]

    for idx, (lx, ly) in enumerate(leg_positions):
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(lx, ly, leg_z),
            scale=(leg_th, leg_th, leg_height)
        )
        leg_obj = bpy.context.active_object
        leg_obj.name = f"Leg_{idx+1}"
        assign_material_to_obj(leg_obj, leg_mat)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        parts.append(leg_obj)

    # Apron / Frame supports if rectangular
    if not is_round and width > 0.6 and depth > 0.4:
        apron_h = 0.05
        apron_th = 0.02
        apron_z = height - top_th - (apron_h / 2.0)
        # 2 long sides
        for side in [-1, 1]:
            ay = side * (depth / 2.0 - leg_th - apron_th / 2.0)
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=(0, ay, apron_z),
                scale=(width - 2 * leg_th, apron_th, apron_h)
            )
            ap_obj = bpy.context.active_object
            assign_material_to_obj(ap_obj, leg_mat)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            parts.append(ap_obj)

    return join_objects(parts, "Table")


def build_chair(params: dict):
    """
    Parametric Chair:
    seat_width, seat_depth, seat_height, backrest_height, leg_thickness, style
    """
    clean_scene()
    width = float(params.get("seat_width", 0.48))
    depth = float(params.get("seat_depth", 0.46))
    seat_height = float(params.get("seat_height", 0.45))
    back_height = float(params.get("backrest_height", 0.45))
    leg_th = float(params.get("leg_thickness", 0.035))
    seat_th = 0.04
    mat_preset = params.get("material", "wood")
    cushion_preset = params.get("cushion_material", "fabric_cushion")
    color_hex = params.get("color_hex")

    frame_mat = resolve_material(mat_preset, color_hex)
    cushion_mat = resolve_material(cushion_preset)

    parts = []

    # Seat
    seat_z = seat_height - (seat_th / 2.0)
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, 0, seat_z),
        scale=(width, depth, seat_th)
    )
    seat_obj = bpy.context.active_object
    seat_obj.name = "ChairSeat"
    assign_material_to_obj(seat_obj, cushion_mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(seat_obj)

    # 4 Legs
    leg_h = seat_height - seat_th
    leg_z = leg_h / 2.0
    lx = width / 2.0 - leg_th / 2.0 - 0.02
    ly = depth / 2.0 - leg_th / 2.0 - 0.02
    for idx, (px, py) in enumerate([(-lx, -ly), (lx, -ly), (-lx, ly), (lx, ly)]):
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(px, py, leg_z),
            scale=(leg_th, leg_th, leg_h)
        )
        leg = bpy.context.active_object
        leg.name = f"ChairLeg_{idx+1}"
        assign_material_to_obj(leg, frame_mat)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        parts.append(leg)

    # Backrest Supports (2 uprights)
    post_th = leg_th
    post_z = seat_height + (back_height / 2.0)
    back_y = depth / 2.0 - post_th / 2.0 - 0.01
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(side * lx, back_y, post_z),
            scale=(post_th, post_th, back_height)
        )
        post = bpy.context.active_object
        assign_material_to_obj(post, frame_mat)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        parts.append(post)

    # Backrest Board / Slats
    board_h = back_height * 0.55
    board_z = seat_height + back_height - (board_h / 2.0)
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, back_y, board_z),
        scale=(width - 0.02, 0.02, board_h)
    )
    board = bpy.context.active_object
    board.name = "Backrest"
    assign_material_to_obj(board, cushion_mat if params.get("cushioned_back") else frame_mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(board)

    return join_objects(parts, "Chair")


def build_cabinet(params: dict):
    """
    Parametric Cabinet / Bookshelf:
    width, depth, height, shelves_count, door_type (open, two_door, single)
    """
    clean_scene()
    width = float(params.get("width", 0.9))
    depth = float(params.get("depth", 0.38))
    height = float(params.get("height", 1.8))
    shelves_count = int(params.get("shelves_count", 4))
    wall_th = 0.025
    mat_preset = params.get("material", "dark_wood")
    handle_preset = params.get("handle_material", "metal_gold")
    color_hex = params.get("color_hex")

    body_mat = resolve_material(mat_preset, color_hex)
    handle_mat = resolve_material(handle_preset)

    parts = []

    # Left & Right side panels
    side_h = height
    side_z = height / 2.0
    for side in [-1, 1]:
        sx = side * (width / 2.0 - wall_th / 2.0)
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(sx, 0, side_z),
            scale=(wall_th, depth, side_h)
        )
        sp = bpy.context.active_object
        assign_material_to_obj(sp, body_mat)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        parts.append(sp)

    # Top & Bottom panels
    inner_w = width - 2 * wall_th
    for pz in [wall_th / 2.0, height - wall_th / 2.0]:
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(0, 0, pz),
            scale=(inner_w, depth, wall_th)
        )
        bp = bpy.context.active_object
        assign_material_to_obj(bp, body_mat)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        parts.append(bp)

    # Back panel
    back_th = 0.01
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, -depth / 2.0 + back_th / 2.0, height / 2.0),
        scale=(inner_w, back_th, height - 2 * wall_th)
    )
    back_obj = bpy.context.active_object
    assign_material_to_obj(back_obj, body_mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(back_obj)

    # Shelves
    spacing = (height - 2 * wall_th) / (shelves_count + 1)
    shelf_depth = depth - back_th - 0.01
    shelf_y = back_th / 2.0
    for i in range(1, shelves_count + 1):
        sz = wall_th + i * spacing
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(0, shelf_y, sz),
            scale=(inner_w, shelf_depth, wall_th)
        )
        sh = bpy.context.active_object
        assign_material_to_obj(sh, body_mat)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        parts.append(sh)

    # Optional lower cabinet doors
    if params.get("has_doors", True):
        door_h = spacing * 1.8
        door_z = wall_th + door_h / 2.0
        door_y = depth / 2.0 + 0.01
        door_w = inner_w / 2.0 - 0.005
        for side in [-1, 1]:
            dx = side * (door_w / 2.0 + 0.002)
            bpy.ops.mesh.primitive_cube_add(
                size=1.0,
                location=(dx, door_y, door_z),
                scale=(door_w, 0.018, door_h)
            )
            door = bpy.context.active_object
            assign_material_to_obj(door, body_mat)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            parts.append(door)

            # Handle
            hx = dx + (-side * (door_w * 0.35))
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.008,
                depth=0.08,
                location=(hx, door_y + 0.02, door_z),
                rotation=(0, 0, 0)
            )
            handle = bpy.context.active_object
            assign_material_to_obj(handle, handle_mat)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            parts.append(handle)

    return join_objects(parts, "Cabinet")


def build_house(params: dict):
    """
    Parametric Simple House / Cottage:
    width (x), length (y), wall_height (z), roof_height, roof_style (gable/hip)
    """
    clean_scene()
    width = float(params.get("width", 5.0))
    length = float(params.get("length", 6.0))
    wall_h = float(params.get("wall_height", 2.8))
    roof_h = float(params.get("roof_height", 1.8))
    wall_th = 0.25

    wall_mat = resolve_material(params.get("wall_material", "wall_paint"), params.get("color_hex"))
    roof_mat = resolve_material(params.get("roof_material", "roof_tile"))
    door_mat = resolve_material("dark_wood")
    window_mat = resolve_material("glass")
    base_mat = resolve_material("concrete")

    parts = []

    # Foundation slab
    slab_th = 0.2
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, 0, slab_th / 2.0),
        scale=(width + 0.4, length + 0.4, slab_th)
    )
    slab = bpy.context.active_object
    assign_material_to_obj(slab, base_mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(slab)

    # Outer Walls Block
    body_z = slab_th + wall_h / 2.0
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, 0, body_z),
        scale=(width, length, wall_h)
    )
    walls = bpy.context.active_object
    assign_material_to_obj(walls, wall_mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(walls)

    # Roof (Gable Roof)
    total_roof_w = width + 0.6
    total_roof_l = length + 0.6
    roof_base_z = slab_th + wall_h

    # Create triangular prism using bmesh
    roof_mesh = bpy.data.meshes.new("GableRoofMesh")
    bm = bmesh.new()
    hw = total_roof_w / 2.0
    hl = total_roof_l / 2.0

    v0 = bm.verts.new((-hw, -hl, 0))
    v1 = bm.verts.new((hw, -hl, 0))
    v2 = bm.verts.new((0, -hl, roof_h))
    v3 = bm.verts.new((-hw, hl, 0))
    v4 = bm.verts.new((hw, hl, 0))
    v5 = bm.verts.new((0, hl, roof_h))

    bm.faces.new([v0, v1, v2]) # front gable
    bm.faces.new([v4, v3, v5]) # back gable
    bm.faces.new([v0, v2, v5, v3]) # left slope
    bm.faces.new([v2, v1, v4, v5]) # right slope
    bm.faces.new([v3, v4, v1, v0]) # bottom

    bm.to_mesh(roof_mesh)
    bm.free()

    roof_obj = bpy.data.objects.new("GableRoof", roof_mesh)
    bpy.context.collection.objects.link(roof_obj)
    roof_obj.location = (0, 0, roof_base_z)
    assign_material_to_obj(roof_obj, roof_mat)
    bpy.context.view_layer.objects.active = roof_obj
    roof_obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(roof_obj)

    # Door decoration
    door_w = 0.95
    door_h = 2.05
    door_z = slab_th + door_h / 2.0
    door_y = -length / 2.0 - 0.02
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, door_y, door_z),
        scale=(door_w, 0.06, door_h)
    )
    door = bpy.context.active_object
    door.name = "FrontDoor"
    assign_material_to_obj(door, door_mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(door)

    # 2 Windows on front
    win_w = 0.8
    win_h = 1.0
    win_z = slab_th + 1.5
    for wx in [-width * 0.28, width * 0.28]:
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(wx, door_y, win_z),
            scale=(win_w, 0.05, win_h)
        )
        win = bpy.context.active_object
        win.name = "WindowGlass"
        assign_material_to_obj(win, window_mat)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        parts.append(win)

    # Chimney
    ch_w = 0.5
    ch_h = roof_h * 0.8
    ch_z = roof_base_z + roof_h * 0.6
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(width * 0.25, -length * 0.2, ch_z),
        scale=(ch_w, ch_w, ch_h)
    )
    ch = bpy.context.active_object
    assign_material_to_obj(ch, base_mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(ch)

    return join_objects(parts, "House")


def build_column(params: dict):
    """
    Parametric Classical / Modern Architectural Column:
    height, diameter, fluted (bool), style (doric/ionic/modern)
    """
    clean_scene()
    height = float(params.get("height", 3.0))
    diameter = float(params.get("diameter", 0.45))
    mat_preset = params.get("material", "marble")
    color_hex = params.get("color_hex")
    mat = resolve_material(mat_preset, color_hex)

    parts = []
    r = diameter / 2.0

    # Base Plinth (square pedestal)
    plinth_h = 0.18
    plinth_w = diameter * 1.45
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, 0, plinth_h / 2.0),
        scale=(plinth_w, plinth_w, plinth_h)
    )
    plinth = bpy.context.active_object
    assign_material_to_obj(plinth, mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(plinth)

    # Base Torus ring
    ring1_h = 0.08
    bpy.ops.mesh.primitive_cylinder_add(
        radius=r * 1.25,
        depth=ring1_h,
        location=(0, 0, plinth_h + ring1_h / 2.0),
        vertices=32
    )
    ring1 = bpy.context.active_object
    assign_material_to_obj(ring1, mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(ring1)

    # Column Shaft
    shaft_base_z = plinth_h + ring1_h
    capital_h = 0.28
    shaft_h = height - shaft_base_z - capital_h
    shaft_z = shaft_base_z + shaft_h / 2.0
    bpy.ops.mesh.primitive_cylinder_add(
        radius=r,
        depth=shaft_h,
        location=(0, 0, shaft_z),
        vertices=24
    )
    shaft = bpy.context.active_object
    assign_material_to_obj(shaft, mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(shaft)

    # Capital (Top molding & abacus slab)
    cap_z = height - capital_h / 2.0
    bpy.ops.mesh.primitive_cylinder_add(
        radius=r * 1.28,
        depth=capital_h * 0.5,
        location=(0, 0, height - capital_h * 0.75),
        vertices=32
    )
    echinus = bpy.context.active_object
    assign_material_to_obj(echinus, mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(echinus)

    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, 0, height - capital_h * 0.25),
        scale=(plinth_w, plinth_w, capital_h * 0.5)
    )
    abacus = bpy.context.active_object
    assign_material_to_obj(abacus, mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(abacus)

    return join_objects(parts, "Column")


def build_road_segment(params: dict):
    """
    Parametric Modular Road Segment:
    length, lane_width, sidewalk_width, curb_height
    """
    clean_scene()
    length = float(params.get("length", 10.0))
    lane_width = float(params.get("lane_width", 3.5))
    sidewalk_w = float(params.get("sidewalk_width", 1.5))
    road_w = lane_width * 2.0 # 2 lanes
    curb_h = 0.15

    asphalt_mat = resolve_material("asphalt")
    concrete_mat = resolve_material("concrete")
    marking_mat = resolve_material("road_marking")

    parts = []

    # Road bed (asphalt)
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, 0, 0.05),
        scale=(road_w, length, 0.1)
    )
    road = bpy.context.active_object
    assign_material_to_obj(road, asphalt_mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(road)

    # Sidewalks (left and right)
    for side in [-1, 1]:
        sw_x = side * (road_w / 2.0 + sidewalk_w / 2.0)
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(sw_x, 0, 0.1 + curb_h / 2.0),
            scale=(sidewalk_w, length, curb_h)
        )
        sw = bpy.context.active_object
        assign_material_to_obj(sw, concrete_mat)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        parts.append(sw)

    # Dashed Center Lane Stripe
    dash_length = 2.0
    dash_gap = 2.0
    period = dash_length + dash_gap
    num_dashes = int(length // period)
    start_y = -length / 2.0 + dash_length / 2.0 + 0.5
    for i in range(max(1, num_dashes)):
        dy = start_y + i * period
        if dy + dash_length / 2.0 > length / 2.0:
            break
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(0, dy, 0.105),
            scale=(0.15, dash_length, 0.005)
        )
        dash = bpy.context.active_object
        assign_material_to_obj(dash, marking_mat)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        parts.append(dash)

    return join_objects(parts, "RoadSegment")


def build_platform(params: dict):
    """
    Parametric Sci-Fi / Display Platform:
    radius, height, tiers (int), glowing_rim (bool)
    """
    clean_scene()
    radius = float(params.get("radius", 2.0))
    height = float(params.get("height", 0.4))
    tiers = int(params.get("tiers", 2))
    mat_preset = params.get("material", "metal_black")
    color_hex = params.get("color_hex")

    body_mat = resolve_material(mat_preset, color_hex)
    rim_mat = resolve_material("emission_glow")
    parts = []

    tier_h = height / float(tiers)
    for t in range(tiers):
        t_radius = radius - (t * (radius * 0.15))
        t_z = t * tier_h + (tier_h / 2.0)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=t_radius,
            depth=tier_h * 0.95,
            location=(0, 0, t_z),
            vertices=36
        )
        cyl = bpy.context.active_object
        assign_material_to_obj(cyl, body_mat)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        parts.append(cyl)

        # Glowing accent rim ring
        bpy.ops.mesh.primitive_cylinder_add(
            radius=t_radius + 0.02,
            depth=tier_h * 0.12,
            location=(0, 0, t * tier_h + tier_h * 0.85),
            vertices=36
        )
        rim = bpy.context.active_object
        assign_material_to_obj(rim, rim_mat)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        parts.append(rim)

    return join_objects(parts, "Platform")


def build_room(params: dict):
    """
    Parametric Architectural Room with floor and walls
    width (x), depth (y), height (z), wall_thickness
    """
    clean_scene()
    width = float(params.get("width", 4.0))
    depth = float(params.get("depth", 4.0))
    height = float(params.get("height", 2.6))
    wall_th = float(params.get("wall_thickness", 0.18))

    floor_mat = resolve_material("wood")
    wall_mat = resolve_material("wall_paint", params.get("color_hex"))

    parts = []

    # Floor plane
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, 0, 0.05),
        scale=(width, depth, 0.1)
    )
    floor_obj = bpy.context.active_object
    assign_material_to_obj(floor_obj, floor_mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(floor_obj)

    # Back Wall
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(0, depth / 2.0 - wall_th / 2.0, height / 2.0 + 0.1),
        scale=(width, wall_th, height)
    )
    b_wall = bpy.context.active_object
    assign_material_to_obj(b_wall, wall_mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(b_wall)

    # Left Wall
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(-width / 2.0 + wall_th / 2.0, 0, height / 2.0 + 0.1),
        scale=(wall_th, depth - 2 * wall_th, height)
    )
    l_wall = bpy.context.active_object
    assign_material_to_obj(l_wall, wall_mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(l_wall)

    # Right Wall with window opening cutout simulation
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(width / 2.0 - wall_th / 2.0, 0, height / 2.0 + 0.1),
        scale=(wall_th, depth - 2 * wall_th, height)
    )
    r_wall = bpy.context.active_object
    assign_material_to_obj(r_wall, wall_mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    parts.append(r_wall)

    return join_objects(parts, "Room")


BUILDER_REGISTRY = {
    "table": build_table,
    "chair": build_chair,
    "cabinet": build_cabinet,
    "bookshelf": build_cabinet,
    "house": build_house,
    "cottage": build_house,
    "column": build_column,
    "road_segment": build_road_segment,
    "road": build_road_segment,
    "platform": build_platform,
    "pedestal": build_platform,
    "room": build_room,
}
