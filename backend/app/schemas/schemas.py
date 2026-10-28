from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List, Dict, Any, Literal
import datetime

# --- Auth Schemas ---
class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$", description="Alphanumeric username")
    password: str = Field(..., min_length=6, max_length=128, description="Password of at least 6 characters")

class UserLoginRequest(BaseModel):
    email_or_username: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: Optional[str] = None
    username: Optional[str] = None
    account_status: str
    created_at: datetime.datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Generation Schemas ---
class DimensionsInput(BaseModel):
    width: Optional[float] = Field(None, ge=0.05, le=100.0, description="Width in meters")
    depth: Optional[float] = Field(None, ge=0.05, le=100.0, description="Depth / Length in meters")
    height: Optional[float] = Field(None, ge=0.05, le=100.0, description="Height in meters")
    units: str = "meters"

class MaterialPreferencesInput(BaseModel):
    preset: Optional[str] = Field("wood", description="Supported preset name")
    color_hex: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$", description="Hex color e.g. #8B5A2B")

class GenerationCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=1000, description="Natural language description of 3D asset")
    generation_mode: Literal["auto", "procedural", "ai_text", "ai_image"] = Field("auto", description="Generation path")
    reference_image_id: Optional[str] = Field(None, description="Optional uploaded image ID")
    object_category: Optional[str] = Field(None, description="Optional category hint: table, chair, cabinet, house, room, column, road_segment, platform")
    style: Optional[str] = Field("modern", description="Style preference: modern, classic, rustic, minimalist, scifi")
    dimensions: Optional[DimensionsInput] = None
    material_preferences: Optional[MaterialPreferencesInput] = None
    target_polygon_count: Optional[int] = Field(None, ge=50, le=500000)
    export_format: Literal["glb", "gltf_zip"] = "glb"
    project_id: Optional[str] = None

class RefineRequest(BaseModel):
    prompt: Optional[str] = Field(None, max_length=1000)
    dimensions: Optional[DimensionsInput] = None
    material_preferences: Optional[MaterialPreferencesInput] = None
    style: Optional[str] = None
    category: Optional[str] = None

class GenerationJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    project_id: Optional[str] = None
    generation_mode: str
    provider: str
    prompt: str
    status: str
    progress: int
    provider_task_id: Optional[str] = None
    error_code: Optional[str] = None
    safe_error_message: Optional[str] = None
    asset_id: Optional[str] = None
    asset_download_url: Optional[str] = None
    validation_report: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None

# --- Asset Schemas ---
class AssetUpdateRequest(BaseModel):
    project_id: Optional[str] = Field(None, description="Project ID to assign this asset to, or None to unassign")

class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    project_id: Optional[str] = None
    source_job_id: Optional[str] = None
    prompt: Optional[str] = None
    generation_mode: Optional[str] = None
    mime_type: str
    file_size: int
    file_checksum: str
    file_format: str
    dimensions: Optional[Dict[str, Any]] = None
    polygon_count: int
    vertex_count: int
    validation_status: str
    validation_report: Optional[Dict[str, Any]] = None
    parent_asset_id: Optional[str] = None
    download_url: str
    created_at: datetime.datetime

# --- Project Schemas ---
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    asset_count: int = 0

# --- Export Schemas ---
class ExportCreateRequest(BaseModel):
    requested_format: Literal["glb", "gltf_zip"] = "glb"

class ExportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    requested_format: str
    status: str
    download_url: Optional[str] = None
    validation_report: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None

# --- Capabilities Schemas ---
class CapabilitiesResponse(BaseModel):
    blender_available: bool
    blender_version: Optional[str] = None
    supported_procedural_categories: List[str]
    ai_provider: str
    ai_configured: bool
    ai_capabilities: Dict[str, Any]
    max_upload_size_bytes: int
    daily_budget_limit_usd: float
    current_daily_spend_usd: float
