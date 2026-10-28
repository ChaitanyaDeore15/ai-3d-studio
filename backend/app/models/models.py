import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    auth_provider_id = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    account_status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    generation_jobs = relationship("GenerationJob", back_populates="owner", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="owner", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    owner_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="projects")
    generation_jobs = relationship("GenerationJob", back_populates="project", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    owner_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), index=True, nullable=True)
    generation_mode = Column(String(50), nullable=False) # procedural, ai_text, ai_image, auto
    provider = Column(String(50), nullable=False) # blender, meshy, tripo
    prompt = Column(Text, nullable=False)
    status = Column(String(50), default="queued", index=True, nullable=False) # queued, running, completed, failed, cancelled
    progress = Column(Integer, default=0) # 0 to 100
    provider_task_id = Column(String(255), nullable=True, index=True)
    error_code = Column(String(100), nullable=True)
    safe_error_message = Column(Text, nullable=True)
    raw_parameters = Column(Text, nullable=True) # JSON representation of validated specs
    estimated_cost_usd = Column(Float, default=0.0)
    actual_cost_usd = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="generation_jobs")
    project = relationship("Project", back_populates="generation_jobs")
    assets = relationship("Asset", back_populates="source_job")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    owner_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), index=True, nullable=True)
    source_job_id = Column(String(36), ForeignKey("generation_jobs.id"), nullable=True)
    storage_key = Column(String(512), nullable=False)
    mime_type = Column(String(100), default="model/gltf-binary", nullable=False)
    file_size = Column(Integer, nullable=False)
    file_checksum = Column(String(64), nullable=False)
    file_format = Column(String(20), default="glb", nullable=False) # glb, gltf_zip
    dimensions_json = Column(Text, nullable=True) # JSON with x, y, z
    polygon_count = Column(Integer, default=0)
    vertex_count = Column(Integer, default=0)
    validation_status = Column(String(50), default="pending") # pending, valid, failed
    validation_report = Column(Text, nullable=True) # JSON
    parent_asset_id = Column(String(36), ForeignKey("assets.id"), nullable=True) # for versioning
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="assets")
    project = relationship("Project", back_populates="assets")
    source_job = relationship("GenerationJob", back_populates="assets")
    export_jobs = relationship("ExportJob", back_populates="asset", cascade="all, delete-orphan")

class ExportJob(Base):
    __tablename__ = "export_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    owner_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    asset_id = Column(String(36), ForeignKey("assets.id"), index=True, nullable=False)
    requested_format = Column(String(20), nullable=False) # glb, gltf_zip
    status = Column(String(50), default="queued", nullable=False) # queued, running, completed, failed
    output_storage_key = Column(String(512), nullable=True)
    validation_report = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    asset = relationship("Asset", back_populates="export_jobs")

class UsageLedger(Base):
    __tablename__ = "usage_ledger"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    owner_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    job_id = Column(String(36), ForeignKey("generation_jobs.id"), nullable=True)
    operation_type = Column(String(50), nullable=False) # procedural_gen, ai_text_to_3d, ai_image_to_3d, export
    usage_units = Column(Float, default=1.0)
    cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
