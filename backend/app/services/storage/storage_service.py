import os
import shutil
import hashlib
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from backend.app.core.config import settings

class BaseStorageService(ABC):
    @abstractmethod
    def store_file(self, source_path_or_bytes, extension: str, prefix: str = "assets") -> Tuple[str, int, str]:
        """
        Stores file and returns (storage_key, file_size_bytes, sha256_checksum).
        """
        pass

    @abstractmethod
    def retrieve_file_path(self, storage_key: str) -> str:
        """
        Returns a local filesystem path to the file (downloading if remote).
        """
        pass

    @abstractmethod
    def delete_file(self, storage_key: str) -> bool:
        pass

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        pass

class LocalStorageAdapter(BaseStorageService):
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_safe_path(self, storage_key: str) -> str:
        # Prevent directory traversal attacks
        normalized_key = os.path.normpath(storage_key).lstrip("\\/.")
        safe_path = os.path.abspath(os.path.join(self.base_dir, normalized_key))
        if not safe_path.startswith(self.base_dir):
            raise ValueError(f"Illegal path traversal detected: {storage_key}")
        return safe_path

    def store_file(self, source_path_or_bytes, extension: str, prefix: str = "assets") -> Tuple[str, int, str]:
        clean_ext = extension.lstrip(".")
        random_name = f"{uuid.uuid4().hex}.{clean_ext}"
        storage_key = f"{prefix}/{random_name}"
        dest_path = self._resolve_safe_path(storage_key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        hasher = hashlib.sha256()

        if isinstance(source_path_or_bytes, (bytes, bytearray)):
            hasher.update(source_path_or_bytes)
            with open(dest_path, "wb") as f:
                f.write(source_path_or_bytes)
            file_size = len(source_path_or_bytes)
        else:
            with open(source_path_or_bytes, "rb") as src, open(dest_path, "wb") as dst:
                while chunk := src.read(65536):
                    hasher.update(chunk)
                    dst.write(chunk)
            file_size = os.path.getsize(dest_path)

        return storage_key, file_size, hasher.hexdigest()

    def retrieve_file_path(self, storage_key: str) -> str:
        path = self._resolve_safe_path(storage_key)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Storage key not found: {storage_key}")
        return path

    def delete_file(self, storage_key: str) -> bool:
        try:
            path = self._resolve_safe_path(storage_key)
            if os.path.exists(path):
                os.remove(path)
                return True
            return False
        except Exception:
            return False

    def exists(self, storage_key: str) -> bool:
        try:
            path = self._resolve_safe_path(storage_key)
            return os.path.exists(path)
        except Exception:
            return False

class S3StorageAdapter(BaseStorageService):
    def __init__(self):
        # Stub for S3 compatibility when configured
        self.bucket = settings.S3_BUCKET_NAME
        self.local_fallback = LocalStorageAdapter(settings.LOCAL_STORAGE_DIR)

    def store_file(self, source_path_or_bytes, extension: str, prefix: str = "assets") -> Tuple[str, int, str]:
        # If boto3/s3 is not configured in local environment, fallback safely
        return self.local_fallback.store_file(source_path_or_bytes, extension, prefix)

    def retrieve_file_path(self, storage_key: str) -> str:
        return self.local_fallback.retrieve_file_path(storage_key)

    def delete_file(self, storage_key: str) -> bool:
        return self.local_fallback.delete_file(storage_key)

    def exists(self, storage_key: str) -> bool:
        return self.local_fallback.exists(storage_key)

_storage_instance: Optional[BaseStorageService] = None

def get_storage_service() -> BaseStorageService:
    global _storage_instance
    if _storage_instance is None:
        if settings.STORAGE_TYPE == "s3" and settings.S3_BUCKET_NAME:
            _storage_instance = S3StorageAdapter()
        else:
            _storage_instance = LocalStorageAdapter(settings.LOCAL_STORAGE_DIR)
    return _storage_instance
