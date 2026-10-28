import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.api import health, capabilities, uploads, generations, projects, assets, exports, refine, auth

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade AI & Procedural 3D Asset Creation Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Can be locked down to specific domains in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(health.router, prefix="/api", tags=["System"])
app.include_router(capabilities.router, prefix="/api", tags=["Capabilities"])
app.include_router(uploads.router, prefix="/api", tags=["Uploads"])
app.include_router(generations.router, prefix="/api", tags=["Generation"])
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(assets.router, prefix="/api", tags=["Assets"])
app.include_router(exports.router, prefix="/api", tags=["Exports"])
app.include_router(refine.router, prefix="/api", tags=["Refinement"])

@app.get("/")
def read_root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "status": "online"
    }
