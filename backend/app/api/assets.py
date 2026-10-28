import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.models import Asset, ExportJob, User, GenerationJob
from backend.app.schemas.schemas import AssetResponse, AssetUpdateRequest, ExportCreateRequest, ExportJobResponse
from backend.app.security.auth import get_current_user, verify_ownership
from backend.app.services.storage.storage_service import get_storage_service
from backend.app.workers.job_worker import enqueue_export_job

router = APIRouter()

def _format_asset_response(asset: Asset) -> AssetResponse:
    dims = json.loads(asset.dimensions_json) if asset.dimensions_json else None
    validation = json.loads(asset.validation_report) if asset.validation_report else None
    prompt = asset.source_job.prompt if asset.source_job else None
    mode = asset.source_job.generation_mode if asset.source_job else None

    return AssetResponse(
        id=asset.id,
        owner_id=asset.owner_id,
        project_id=asset.project_id,
        source_job_id=asset.source_job_id,
        prompt=prompt,
        generation_mode=mode,
        mime_type=asset.mime_type,
        file_size=asset.file_size,
        file_checksum=asset.file_checksum,
        file_format=asset.file_format,
        dimensions=dims,
        polygon_count=asset.polygon_count,
        vertex_count=asset.vertex_count,
        validation_status=asset.validation_status,
        validation_report=validation,
        parent_asset_id=asset.parent_asset_id,
        download_url=f"/api/assets/{asset.id}/file",
        created_at=asset.created_at
    )

@router.get("/assets", response_model=List[AssetResponse])
def list_assets(
    project_id: Optional[str] = Query(None, description="Filter assets by project ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists all 3D assets owned by the authenticated user.
    Supports filtering by project.
    """
    query = db.query(Asset).filter(Asset.owner_id == current_user.id)
    if project_id:
        query = query.filter(Asset.project_id == project_id)
    
    assets = query.order_by(Asset.created_at.desc()).all()
    return [_format_asset_response(a) for a in assets]

@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    verify_ownership(asset.owner_id, current_user, "asset")

    return _format_asset_response(asset)

@router.patch("/assets/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: str,
    data: AssetUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates asset metadata, such as assigning or reassigning it to a project.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    verify_ownership(asset.owner_id, current_user, "asset")

    asset.project_id = data.project_id
    db.commit()
    db.refresh(asset)

    return _format_asset_response(asset)

@router.delete("/assets/{asset_id}")
def delete_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes an asset and its physical file from storage.
    Enforces strict ownership check.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    verify_ownership(asset.owner_id, current_user, "asset")

    # Delete storage file
    storage = get_storage_service()
    storage.delete_file(asset.storage_key)

    db.delete(asset)
    db.commit()

    return {"status": "deleted", "asset_id": asset_id}

@router.get("/assets/{asset_id}/file")
def get_asset_file(
    asset_id: str,
    db: Session = Depends(get_db)
):
    """
    Publicly serve the 3D asset file for interactive 3D WebGL viewers.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")

    storage = get_storage_service()
    try:
        local_path = storage.retrieve_file_path(asset.storage_key)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset file missing from storage.")

    media_type = "model/gltf-binary" if asset.file_format == "glb" else "application/zip"
    filename = f"model.{asset.file_format}"

    return FileResponse(
        path=local_path,
        media_type=media_type,
        filename=filename,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600"
        }
    )

@router.post("/assets/{asset_id}/exports", response_model=ExportJobResponse)
def request_export(
    asset_id: str,
    req: ExportCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    verify_ownership(asset.owner_id, current_user, "asset")

    export_job = ExportJob(
        owner_id=current_user.id,
        asset_id=asset.id,
        requested_format=req.requested_format,
        status="queued"
    )
    db.add(export_job)
    db.commit()
    db.refresh(export_job)

    enqueue_export_job(export_job.id)

    return ExportJobResponse(
        id=export_job.id,
        asset_id=export_job.asset_id,
        requested_format=export_job.requested_format,
        status=export_job.status,
        download_url=None,
        validation_report=None,
        error_message=None,
        created_at=export_job.created_at,
        completed_at=None
    )
