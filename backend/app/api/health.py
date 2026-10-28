from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import datetime
from backend.app.db.session import get_db
from backend.app.services.blender.blender_runner import BlenderRunner

router = APIRouter()

@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    runner = BlenderRunner()
    blender_ok = runner.is_available()
    blender_ver = runner.get_version() if blender_ok else None

    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "database_connected": db_ok,
        "blender_available": blender_ok,
        "blender_version": blender_ver
    }
