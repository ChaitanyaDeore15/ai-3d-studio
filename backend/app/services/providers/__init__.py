from backend.app.core.config import settings
from .base import BaseAI3DProvider
from .meshy_provider import MeshyProvider
from .tripo_provider import TripoProvider

def get_ai_provider() -> BaseAI3DProvider:
    if settings.AI_3D_PROVIDER == "tripo":
        return TripoProvider()
    return MeshyProvider()
