import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.models import ExportJob, User
from backend.app.schemas.schemas import ExportJobResponse
from backend.app.security.auth import get_current_user, verify_ownership
from backend.app.services.storage.storage_service import get_storage_service

router = APIRouter()

@router.get("/exports/{export_id}", response_model=ExportJobResponse)
def get_export_status(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exp = db.query(ExportJob).filter(ExportJob.id == export_id).first()
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export job not found.")
    verify_ownership(exp.owner_id, current_user, "export job")

    report = json.loads(exp.validation_report) if exp.validation_report else None
    download_url = f"/api/exports/{exp.id}/download" if exp.status == "completed" else None

    return ExportJobResponse(
        id=exp.id,
        asset_id=exp.asset_id,
        requested_format=exp.requested_format,
        status=exp.status,
        download_url=download_url,
        validation_report=report,
        error_message=exp.error_message,
        created_at=exp.created_at,
        completed_at=exp.completed_at
    )

@router.get("/exports/{export_id}/download")
def download_exported_file(
    export_id: str,
    db: Session = Depends(get_db)
):
    exp = db.query(ExportJob).filter(ExportJob.id == export_id).first()
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export job not found.")

    if exp.status != "completed" or not exp.output_storage_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export is not ready for download.")

    storage = get_storage_service()
    try:
        local_path = storage.retrieve_file_path(exp.output_storage_key)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exported asset file missing.")

    ext = "zip" if exp.requested_format in ("gltf", "gltf_zip") else "glb"
    media_type = "application/zip" if ext == "zip" else "model/gltf-binary"

    return FileResponse(
        path=local_path,
        media_type=media_type,
        filename=f"exported_model_{exp.id[:8]}.{ext}",
        headers={"Content-Disposition": f"attachment; filename=model_{exp.id[:8]}.{ext}"}
    )
