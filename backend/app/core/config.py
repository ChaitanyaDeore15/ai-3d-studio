import os
from pydantic import BaseModel
from typing import Optional, Literal

class Settings(BaseModel):
    PROJECT_NAME: str = "AI 3D Studio"
    API_V1_STR: str = "/api"
    ENV: str = os.getenv("ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-development-key-change-in-prod-xyz123456")
    
    # Database
    # Default to sqlite:///./ai_3d_studio.db for simple local dev, overridden by DATABASE_URL for Postgres
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ai_3d_studio.db")
    
    # Redis / Queue
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Blender executable path
    BLENDER_PATH: str = os.getenv(
        "BLENDER_PATH", 
        r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
    )
    BLENDER_TIMEOUT_SECONDS: int = int(os.getenv("BLENDER_TIMEOUT_SECONDS", "60"))
    
    # Storage
    STORAGE_TYPE: Literal["local", "s3"] = os.getenv("STORAGE_TYPE", "local") # type: ignore
    LOCAL_STORAGE_DIR: str = os.getenv("LOCAL_STORAGE_DIR", os.path.abspath("./storage_data"))
    S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME")
    S3_ENDPOINT_URL: Optional[str] = os.getenv("S3_ENDPOINT_URL")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    # AI Providers
    AI_3D_PROVIDER: Literal["meshy", "tripo", "none"] = os.getenv("AI_3D_PROVIDER", "meshy") # type: ignore
    MESHY_API_KEY: Optional[str] = os.getenv("MESHY_API_KEY")
    TRIPO_API_KEY: Optional[str] = os.getenv("TRIPO_API_KEY")
    AI_PROVIDER_TIMEOUT_SECONDS: int = int(os.getenv("AI_PROVIDER_TIMEOUT_SECONDS", "300"))
    AI_MAX_CONCURRENT_JOBS: int = int(os.getenv("AI_MAX_CONCURRENT_JOBS", "3"))
    
    # Rate Limits & Quotas
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024 # 15 MB
    MAX_PROMPT_LENGTH: int = 1000
    DAILY_BUDGET_LIMIT_USD: float = float(os.getenv("DAILY_BUDGET_LIMIT_USD", "25.00"))

settings = Settings()
