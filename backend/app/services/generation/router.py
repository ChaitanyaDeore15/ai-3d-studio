import re
from typing import Dict, Any, Tuple, Optional
from backend.app.schemas.schemas import GenerationCreateRequest
from backend.app.services.providers import get_ai_provider
from backend.app.services.blender.blender_runner import BlenderRunner

PROCEDURAL_CATEGORIES = {
    "table": ["table", "desk", "coffee table", "dining table", "workstation"],
    "chair": ["chair", "armchair", "seat", "stool"],
    "cabinet": ["cabinet", "bookshelf", "cupboard", "wardrobe", "bookcase", "shelf"],
    "house": ["house", "cottage", "cabin", "building", "bungalow"],
    "column": ["column", "pillar", "post", "monolith", "plinth"],
    "road_segment": ["road", "street", "highway", "asphalt", "lane", "roadway"],
    "platform": ["platform", "pedestal", "podium", "stand", "display base", "stage"],
    "room": ["room", "interior", "living room", "chamber", "studio space"]
}

COLOR_MAP = {
    "red": "#C0392B",
    "blue": "#2980B9",
    "green": "#27AE60",
    "black": "#1E1E1E",
    "white": "#FAFAFA",
    "gold": "#F1C40F",
    "yellow": "#F39C12",
    "brown": "#795548",
    "wood": "#8D6E63",
    "dark wood": "#3E2723",
    "grey": "#7F8C8D",
    "gray": "#7F8C8D",
    "silver": "#BDC3C7",
    "concrete": "#95A5A6"
}

MATERIAL_MAP = {
    "wood": "wood",
    "wooden": "wood",
    "oak": "wood",
    "pine": "wood",
    "mahogany": "dark_wood",
    "dark wood": "dark_wood",
    "walnut": "dark_wood",
    "steel": "metal_steel",
    "metal": "metal_steel",
    "metallic": "metal_steel",
    "iron": "metal_steel",
    "gold": "metal_gold",
    "golden": "metal_gold",
    "black metal": "metal_black",
    "plastic": "plastic_white",
    "white plastic": "plastic_white",
    "blue plastic": "plastic_blue",
    "red plastic": "plastic_red",
    "fabric": "fabric_cushion",
    "cushioned": "fabric_cushion",
    "glass": "glass",
    "marble": "marble",
    "concrete": "concrete",
    "asphalt": "asphalt"
}

def detect_procedural_category(prompt: str, explicit_category: Optional[str] = None) -> Optional[str]:
    if explicit_category and explicit_category.lower() in PROCEDURAL_CATEGORIES:
        return explicit_category.lower()

    lower_prompt = prompt.lower()
    for cat, keywords in PROCEDURAL_CATEGORIES.items():
        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, lower_prompt):
                return cat
    return None

def extract_color(prompt: str) -> Optional[str]:
    lower = prompt.lower()
    for name, hex_val in COLOR_MAP.items():
        if re.search(r'\b' + re.escape(name) + r'\b', lower):
            return hex_val
    return None

def extract_material(prompt: str) -> str:
    lower = prompt.lower()
    for kw, preset in MATERIAL_MAP.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', lower):
            return preset
    return "wood"

def extract_dimensions_from_prompt(prompt: str) -> Dict[str, float]:
    """
    Extracts metrics like '2m', '1.5 meters wide', '80cm high'
    """
    res = {}
    lower = prompt.lower()

    # Look for patterns like: 2m wide, 1.5m, 80cm
    width_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:m|meters?)\s*(?:wide|width)', lower)
    if width_match:
        res["width"] = float(width_match.group(1))

    height_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:m|meters?)\s*(?:high|height|tall)', lower)
    if height_match:
        res["height"] = float(height_match.group(1))

    depth_match = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:m|meters?)\s*(?:deep|depth|long|length)', lower)
    if depth_match:
        res["depth"] = float(depth_match.group(1))

    return res

def route_generation_request(request: GenerationCreateRequest) -> Dict[str, Any]:
    """
    Decides routing path between Blender procedural builder and AI providers.
    Returns:
    {
      "chosen_mode": "procedural" | "ai_text" | "ai_image",
      "provider": "blender" | "meshy" | "tripo",
      "category": Optional[str],
      "builder_params": Dict[str, Any],
      "explanation": str,
      "limitations": str
    }
    """
    ai_provider = get_ai_provider()
    blender_available = BlenderRunner().is_available()

    requested_mode = request.generation_mode
    detected_cat = detect_procedural_category(request.prompt, request.object_category)

    # 1. Handle explicit procedural request
    if requested_mode == "procedural":
        if not detected_cat:
            raise ValueError(
                f"Procedural generation requires a supported structured category. "
                f"Supported categories: {list(PROCEDURAL_CATEGORIES.keys())}. "
                f"Please select a category or use 'auto' / 'ai_text'."
            )
        return _build_procedural_route(request, detected_cat, "User explicitly selected Procedural Generation mode.")

    # 2. Handle explicit AI image request
    if requested_mode == "ai_image":
        if not request.reference_image_id:
            raise ValueError("Reference image is required for 'ai_image' generation mode.")
        if not ai_provider.is_configured():
            raise ValueError(
                f"AI generation provider '{ai_provider.get_provider_name()}' is not configured (missing API credentials). "
                f"Please configure {ai_provider.get_provider_name().upper()}_API_KEY or use procedural generation."
            )
        return {
            "chosen_mode": "ai_image",
            "provider": ai_provider.get_provider_name(),
            "category": None,
            "builder_params": {},
            "explanation": f"Routing reference image to {ai_provider.get_provider_name().capitalize()} Image-to-3D pipeline.",
            "limitations": "Free-form AI mesh generation may require 1-3 minutes and post-processing."
        }

    # 3. Handle explicit AI text request
    if requested_mode == "ai_text":
        if not ai_provider.is_configured():
            raise ValueError(
                f"AI generation provider '{ai_provider.get_provider_name()}' is not configured (missing API credentials). "
                f"Please set {ai_provider.get_provider_name().upper()}_API_KEY to enable AI text-to-3D, or use procedural mode."
            )
        return {
            "chosen_mode": "ai_text",
            "provider": ai_provider.get_provider_name(),
            "category": None,
            "builder_params": {},
            "explanation": f"Routing prompt to {ai_provider.get_provider_name().capitalize()} Text-to-3D model.",
            "limitations": "Generates organic/freeform geometry with AI-synthesized textures. Takes 1-3 minutes."
        }

    # 4. Auto mode:
    # If a structured category is detected AND Blender is available, route to procedural for deterministic, fast, precision mesh!
    if detected_cat and blender_available:
        return _build_procedural_route(
            request,
            detected_cat,
            f"Prompt matched structured architectural/furniture category '{detected_cat}'. "
            f"Routing to Blender Procedural Engine for instant, exact, mathematically clean geometry."
        )

    # Otherwise, if AI provider is configured, route to AI text
    if ai_provider.is_configured():
        return {
            "chosen_mode": "ai_text",
            "provider": ai_provider.get_provider_name(),
            "category": None,
            "builder_params": {},
            "explanation": f"Complex or free-form prompt routed to {ai_provider.get_provider_name().capitalize()} AI generator.",
            "limitations": "AI-generated meshes are non-deterministic and take approximately 60-180 seconds."
        }

    # If AI provider is NOT configured, but Blender is available:
    if blender_available:
        # Fallback to closest procedural object if possible or inform user
        fallback_cat = detected_cat or "platform"
        return _build_procedural_route(
            request,
            fallback_cat,
            f"AI provider credentials are not configured, so your request was safely handled by the local Blender Procedural Engine as a '{fallback_cat}'. "
            f"Set MESHY_API_KEY to unlock free-form AI text-to-3D."
        )

    raise ValueError("Neither Blender procedural engine nor AI provider is available on this server.")

def _build_procedural_route(request: GenerationCreateRequest, category: str, explanation: str) -> Dict[str, Any]:
    extracted_dims = extract_dimensions_from_prompt(request.prompt)
    extracted_color = extract_color(request.prompt)
    extracted_mat = extract_material(request.prompt)

    params: Dict[str, Any] = {}
    if request.dimensions:
        if request.dimensions.width is not None:
            params["width"] = request.dimensions.width
        if request.dimensions.depth is not None:
            params["depth"] = request.dimensions.depth
        if request.dimensions.height is not None:
            params["height"] = request.dimensions.height
    for k, v in extracted_dims.items():
        if k not in params:
            params[k] = v

    if request.material_preferences and request.material_preferences.preset:
        params["material"] = request.material_preferences.preset
    else:
        params["material"] = extracted_mat

    if request.material_preferences and request.material_preferences.color_hex:
        params["color_hex"] = request.material_preferences.color_hex
    elif extracted_color:
        params["color_hex"] = extracted_color

    if request.style:
        params["style"] = request.style

    # Category-specific flags
    lower_prompt = request.prompt.lower()
    if category == "table":
        if "round" in lower_prompt or "circular" in lower_prompt:
            params["round_top"] = True
    elif category == "chair":
        if "cushion" in lower_prompt or "padded" in lower_prompt:
            params["cushioned_back"] = True
    elif category == "cabinet":
        if "open" in lower_prompt or "no doors" in lower_prompt:
            params["has_doors"] = False

    return {
        "chosen_mode": "procedural",
        "provider": "blender",
        "category": category,
        "builder_params": params,
        "explanation": explanation,
        "limitations": "Procedural meshes are cleanly defined geometric primitives with PBR shaders. For free-form organic characters or sculpts, select AI generation mode."
    }
