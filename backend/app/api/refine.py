import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.models import Asset, GenerationJob, User
from backend.app.schemas.schemas import RefineRequest, GenerationJobResponse
from backend.app.security.auth import get_current_user, verify_ownership
from backend.app.workers.job_worker import enqueue_generation_job

router = APIRouter()

@router.post("/refine/{asset_id}", response_model=GenerationJobResponse)
def refine_asset(
    asset_id: str,
    req: RefineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    verify_ownership(asset.owner_id, current_user, "asset")

    source_job = db.query(GenerationJob).filter(GenerationJob.id == asset.source_job_id).first()
    if not source_job:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Asset has no recorded generation job.")

    prev_params = json.loads(source_job.raw_parameters or "{}")

    # Update params
    category = req.category or prev_params.get("category", "table")
    builder_params = prev_params.get("builder_params", {})

    if req.dimensions:
        if req.dimensions.width is not None:
            builder_params["width"] = req.dimensions.width
        if req.dimensions.depth is not None:
            builder_params["depth"] = req.dimensions.depth
        if req.dimensions.height is not None:
            builder_params["height"] = req.dimensions.height

    if req.material_preferences:
        if req.material_preferences.preset:
            builder_params["material"] = req.material_preferences.preset
        if req.material_preferences.color_hex:
            builder_params["color_hex"] = req.material_preferences.color_hex

    if req.style:
        builder_params["style"] = req.style

    new_prompt = req.prompt or f"Refined {source_job.prompt}"

    new_params_payload = {
        "category": category,
        "builder_params": builder_params,
        "export_format": prev_params.get("export_format", "glb"),
        "parent_asset_id": asset.id
    }

    new_job = GenerationJob(
        owner_id=current_user.id,
        project_id=asset.project_id,
        generation_mode=source_job.generation_mode,
        provider=source_job.provider,
        prompt=new_prompt,
        status="queued",
        progress=0,
        raw_parameters=json.dumps(new_params_payload)
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    enqueue_generation_job(new_job.id)

    return GenerationJobResponse(
        id=new_job.id,
        owner_id=new_job.owner_id,
        project_id=new_job.project_id,
        generation_mode=new_job.generation_mode,
        provider=new_job.provider,
        prompt=new_job.prompt,
        status=new_job.status,
        progress=0,
        provider_task_id=None,
        error_code=None,
        safe_error_message=f"Refinement of asset {asset.id[:8]} started.",
        asset_id=None,
        asset_download_url=None,
        validation_report=None,
        created_at=new_job.created_at,
        completed_at=None
    )
