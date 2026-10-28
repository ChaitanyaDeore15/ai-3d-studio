from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import datetime
from backend.app.db.session import get_db
from backend.app.core.config import settings
from backend.app.services.blender.blender_runner import BlenderRunner
from backend.app.services.providers import get_ai_provider
from backend.app.services.generation.router import PROCEDURAL_CATEGORIES
from backend.app.models.models import UsageLedger

router = APIRouter()

@router.get("/capabilities")
def get_system_capabilities(db: Session = Depends(get_db)):
    runner = BlenderRunner()
    blender_ok = runner.is_available()
    blender_ver = runner.get_version() if blender_ok else None

    ai_prov = get_ai_provider()
    ai_caps = ai_prov.capabilities()

    # Calculate today's usage
    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    daily_spend = db.query(func.coalesce(func.sum(UsageLedger.cost_usd), 0.0)).filter(
        UsageLedger.created_at >= today_start
    ).scalar() or 0.0

    return {
        "blender_available": blender_ok,
        "blender_version": blender_ver,
        "supported_procedural_categories": list(PROCEDURAL_CATEGORIES.keys()),
        "ai_provider": ai_prov.get_provider_name(),
        "ai_configured": ai_prov.is_configured(),
        "ai_capabilities": ai_caps,
        "max_upload_size_bytes": settings.MAX_UPLOAD_SIZE_BYTES,
        "daily_budget_limit_usd": settings.DAILY_BUDGET_LIMIT_USD,
        "current_daily_spend_usd": round(float(daily_spend), 3)
    }
