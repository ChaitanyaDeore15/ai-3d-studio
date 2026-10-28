import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.models import GenerationJob, Asset, User
from backend.app.schemas.schemas import GenerationCreateRequest, GenerationJobResponse
from backend.app.security.auth import get_current_user, verify_ownership
from backend.app.services.generation.router import route_generation_request
from backend.app.workers.job_worker import enqueue_generation_job, cancel_running_job

router = APIRouter()

@router.post("/generations", response_model=GenerationJobResponse)
def create_generation(
    req: GenerationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a new 3D generation request.
    Routes intelligently to Blender procedural builder or AI Provider.
    Dispatches task asynchronously and returns immediately.
    """
    try:
        routing = route_generation_request(req)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    # Persist parameters for background worker execution
    params_payload = {
        "category": routing.get("category"),
        "builder_params": routing.get("builder_params"),
        "export_format": req.export_format,
        "style": req.style,
        "reference_image_id": req.reference_image_id,
        "explanation": routing.get("explanation"),
        "limitations": routing.get("limitations")
    }

    job = GenerationJob(
        owner_id=current_user.id,
        project_id=req.project_id,
        generation_mode=routing["chosen_mode"],
        provider=routing["provider"],
        prompt=req.prompt,
        status="queued",
        progress=0,
        raw_parameters=json.dumps(params_payload)
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue background execution
    enqueue_generation_job(job.id)

    return GenerationJobResponse(
        id=job.id,
        owner_id=job.owner_id,
        project_id=job.project_id,
        generation_mode=job.generation_mode,
        provider=job.provider,
        prompt=job.prompt,
        status=job.status,
        progress=job.progress,
        provider_task_id=job.provider_task_id,
        error_code=job.error_code,
        safe_error_message=routing.get("explanation"),
        asset_id=None,
        asset_download_url=None,
        validation_report=None,
        created_at=job.created_at,
        completed_at=job.completed_at
    )

@router.get("/generations/{job_id}", response_model=GenerationJobResponse)
def get_generation_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation job not found.")

    verify_ownership(job.owner_id, current_user, "generation job")

    asset = db.query(Asset).filter(Asset.source_job_id == job.id).first()
    asset_id = asset.id if asset else None
    download_url = f"/api/assets/{asset.id}/file" if asset else None
    validation = json.loads(asset.validation_report) if (asset and asset.validation_report) else None

    return GenerationJobResponse(
        id=job.id,
        owner_id=job.owner_id,
        project_id=job.project_id,
        generation_mode=job.generation_mode,
        provider=job.provider,
        prompt=job.prompt,
        status=job.status,
        progress=job.progress,
        provider_task_id=job.provider_task_id,
        error_code=job.error_code,
        safe_error_message=job.safe_error_message,
        asset_id=asset_id,
        asset_download_url=download_url,
        validation_report=validation,
        created_at=job.created_at,
        completed_at=job.completed_at
    )

@router.post("/generations/{job_id}/cancel")
def cancel_generation(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation job not found.")

    verify_ownership(job.owner_id, current_user, "generation job")

    if job.status in ("completed", "failed", "cancelled"):
        return {"status": job.status, "message": f"Job is already in terminal state '{job.status}'."}

    cancel_running_job(job.id)
    job.status = "cancelled"
    job.safe_error_message = "Generation cancelled by user."
    db.commit()

    return {"status": "cancelled", "message": "Job cancellation requested."}
