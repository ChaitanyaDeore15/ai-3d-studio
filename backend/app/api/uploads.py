import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from backend.app.core.config import settings
from backend.app.services.storage.storage_service import get_storage_service
from backend.app.models.models import User
from backend.app.security.auth import get_current_user

router = APIRouter()

ALLOWED_MIMES = {
    "image/jpeg": [b"\xFF\xD8\xFF"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"]
}

@router.post("/uploads")
async def upload_reference_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Safely stores user uploaded reference image for image-to-3D workflows.
    Validates MIME type, magic bytes, and file size.
    """
    if file.content_type not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type '{file.content_type}'. Allowed types: JPEG, PNG, WEBP."
        )

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB."
        )

    # Magic byte check
    expected_magic = ALLOWED_MIMES[file.content_type]
    valid_magic = any(content.startswith(magic) for magic in expected_magic)
    if not valid_magic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match reported image format header."
        )

    # Determine extension
    ext = "jpg" if "jpeg" in file.content_type else ("png" if "png" in file.content_type else "webp")
    storage = get_storage_service()
    storage_key, size, checksum = storage.store_file(content, ext, prefix=f"uploads/{current_user.id}")

    return {
        "upload_id": storage_key,
        "filename": os.path.basename(storage_key),
        "file_size": size,
        "content_type": file.content_type,
        "checksum": checksum
    }
