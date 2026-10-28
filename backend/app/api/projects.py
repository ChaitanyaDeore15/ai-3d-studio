from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.db.session import get_db
from backend.app.models.models import Project, Asset, User
from backend.app.schemas.schemas import ProjectCreate, ProjectResponse
from backend.app.security.auth import get_current_user, verify_ownership
from backend.app.services.storage.storage_service import get_storage_service

router = APIRouter()

@router.get("/projects", response_model=List[ProjectResponse])
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    projects = db.query(Project).filter(Project.owner_id == current_user.id).order_by(Project.created_at.desc()).all()
    res = []
    for p in projects:
        asset_count = db.query(Asset).filter(Asset.project_id == p.id).count()
        res.append(ProjectResponse(
            id=p.id,
            owner_id=p.owner_id,
            name=p.name,
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at,
            asset_count=asset_count
        ))
    return res

@router.post("/projects", response_model=ProjectResponse)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proj = Project(
        owner_id=current_user.id,
        name=data.name,
        description=data.description
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return ProjectResponse(
        id=proj.id,
        owner_id=proj.owner_id,
        name=proj.name,
        description=proj.description,
        created_at=proj.created_at,
        updated_at=proj.updated_at,
        asset_count=0
    )

@router.get("/projects/{project_id}")
def get_project_details(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    verify_ownership(proj.owner_id, current_user, "project")

    assets = db.query(Asset).filter(Asset.project_id == proj.id).order_by(Asset.created_at.desc()).all()
    return {
        "project": {
            "id": proj.id,
            "name": proj.name,
            "description": proj.description,
            "created_at": proj.created_at,
            "updated_at": proj.updated_at
        },
        "assets": [
            {
                "id": a.id,
                "file_format": a.file_format,
                "file_size": a.file_size,
                "polygon_count": a.polygon_count,
                "vertex_count": a.vertex_count,
                "validation_status": a.validation_status,
                "download_url": f"/api/assets/{a.id}/file",
                "created_at": a.created_at
            }
            for a in assets
        ]
    }

@router.delete("/projects/{project_id}")
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    verify_ownership(proj.owner_id, current_user, "project")

    # Clean stored files
    storage = get_storage_service()
    assets = db.query(Asset).filter(Asset.project_id == proj.id).all()
    for a in assets:
        storage.delete_file(a.storage_key)

    db.delete(proj)
    db.commit()
    return {"status": "deleted", "project_id": project_id}
