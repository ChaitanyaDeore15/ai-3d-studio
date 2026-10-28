import httpx
from typing import Dict, Any, Optional
from backend.app.core.config import settings
from .base import BaseAI3DProvider

class TripoProvider(BaseAI3DProvider):
    BASE_URL = "https://api.tripo3d.ai/v2/openapi"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TRIPO_API_KEY

    def get_provider_name(self) -> str:
        return "tripo"

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "name": "Tripo 3D",
            "text_to_3d": True,
            "image_to_3d": True,
            "supported_formats": ["glb"],
            "configured": self.is_configured(),
            "docs_url": "https://platform.tripo3d.ai/docs",
            "pricing_summary": "Draft: 10 credits (~$0.10). Detailed: 25 credits (~$0.25)."
        }

    def _get_headers(self) -> Dict[str, str]:
        if not self.is_configured():
            raise ValueError("Tripo API key is not configured. Please set TRIPO_API_KEY environment variable.")
        return {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json"
        }

    def create_text_to_3d_task(self, prompt: str, style: Optional[str] = None) -> str:
        url = f"{self.BASE_URL}/task"
        payload = {
            "type": "text_to_model",
            "prompt": prompt
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=self._get_headers())
            if resp.status_code != 200:
                raise RuntimeError(f"Tripo task creation failed [{resp.status_code}]: {resp.text}")
            data = resp.json()
            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                raise RuntimeError(f"Tripo response did not contain task_id: {data}")
            return task_id

    def create_image_to_3d_task(self, image_url: str, prompt: Optional[str] = None) -> str:
        url = f"{self.BASE_URL}/task"
        payload = {
            "type": "image_to_model",
            "file": {
                "type": "jpg",
                "url": image_url
            }
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=self._get_headers())
            if resp.status_code != 200:
                raise RuntimeError(f"Tripo image task creation failed [{resp.status_code}]: {resp.text}")
            data = resp.json()
            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                raise RuntimeError(f"Tripo response did not contain task_id: {data}")
            return task_id

    def get_task_status(self, provider_task_id: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/task/{provider_task_id}"
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=self._get_headers())
            if resp.status_code != 200:
                return {
                    "status": "failed",
                    "progress": 0,
                    "model_url": None,
                    "error": f"Failed to poll Tripo status [{resp.status_code}]: {resp.text}"
                }
            data = resp.json().get("data", {})
            raw_status = data.get("status", "").lower()
            progress = data.get("progress", 0)

            if raw_status == "success":
                model_url = data.get("output", {}).get("model")
                return {
                    "status": "completed",
                    "progress": 100,
                    "model_url": model_url,
                    "error": None
                }
            elif raw_status in ("failed", "cancelled", "unknown"):
                return {
                    "status": "failed",
                    "progress": progress,
                    "model_url": None,
                    "error": data.get("message", "Tripo task failed")
                }
            elif raw_status == "running":
                return {
                    "status": "running",
                    "progress": progress,
                    "model_url": None,
                    "error": None
                }
            else:
                return {
                    "status": "queued",
                    "progress": progress,
                    "model_url": None,
                    "error": None
                }

    def retrieve_completed_asset(self, model_url: str) -> bytes:
        with httpx.Client(timeout=120.0) as client:
            resp = client.get(model_url)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to download asset from Tripo [{resp.status_code}]")
            return resp.content

    def cancel_task(self, provider_task_id: str) -> bool:
        return False

    def get_usage_information(self) -> Dict[str, Any]:
        return {
            "provider": "tripo",
            "active": self.is_configured(),
            "cost_per_draft_usd": 0.10
        }
