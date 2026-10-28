from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAI3DProvider(ABC):
    @abstractmethod
    def get_provider_name(self) -> str:
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    def capabilities(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_text_to_3d_task(self, prompt: str, style: Optional[str] = None) -> str:
        """Submits real text-to-3D task and returns provider task ID."""
        pass

    @abstractmethod
    def create_image_to_3d_task(self, image_url: str, prompt: Optional[str] = None) -> str:
        """Submits real image-to-3D task and returns provider task ID."""
        pass

    @abstractmethod
    def get_task_status(self, provider_task_id: str) -> Dict[str, Any]:
        """
        Polls task status. Returns:
        {
          "status": "queued" | "running" | "completed" | "failed",
          "progress": int (0-100),
          "model_url": Optional[str],
          "error": Optional[str]
        }
        """
        pass

    @abstractmethod
    def retrieve_completed_asset(self, model_url: str) -> bytes:
        """Downloads actual generated model file before provider retention expires."""
        pass

    @abstractmethod
    def cancel_task(self, provider_task_id: str) -> bool:
        pass

    @abstractmethod
    def get_usage_information(self) -> Dict[str, Any]:
        pass
