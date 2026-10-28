import httpx
from typing import Dict, Any, Optional
from backend.app.core.config import settings
from .base import BaseAI3DProvider

class MeshyProvider(BaseAI3DProvider):
    BASE_URL = "https://api.meshy.ai"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.MESHY_API_KEY

    def get_provider_name(self) -> str:
        return "meshy"

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "name": "Meshy AI",
            "text_to_3d": True,
            "image_to_3d": True,
            "supported_formats": ["glb"],
            "configured": self.is_configured(),
            "docs_url": "https://docs.meshy.ai",
            "pricing_summary": "Preview: 5 credits (~$0.05). Refine: 20 credits (~$0.20)."
        }

    def _get_headers(self) -> Dict[str, str]:
        if not self.is_configured():
            raise ValueError("Meshy API key is not configured. Please set MESHY_API_KEY environment variable.")
        return {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json"
        }

    def create_text_to_3d_task(self, prompt: str, style: Optional[str] = None) -> str:
        url = f"{self.BASE_URL}/openapi/v2/text-to-3d"
        payload = {
            "mode": "preview",
            "prompt": prompt,
            "art_style": style if style in ["realistic", "sculpture", "pbr"] else "realistic",
            "should_remesh": True
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=self._get_headers())
            if resp.status_code != 200 and resp.status_code != 202:
                raise RuntimeError(f"Meshy task creation failed [{resp.status_code}]: {resp.text}")
            data = resp.json()
            task_id = data.get("result")
            if not task_id:
                raise RuntimeError(f"Meshy response did not contain task id: {data}")
            return task_id

    def create_image_to_3d_task(self, image_url: str, prompt: Optional[str] = None) -> str:
        url = f"{self.BASE_URL}/openapi/v1/image-to-3d"
        payload = {
            "image_url": image_url,
            "enable_pbr": True
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=self._get_headers())
            if resp.status_code not in (200, 202):
                raise RuntimeError(f"Meshy image-to-3d task creation failed [{resp.status_code}]: {resp.text}")
            data = resp.json()
            task_id = data.get("result")
            if not task_id:
                raise RuntimeError(f"Meshy response missing task id: {data}")
            return task_id

    def get_task_status(self, provider_task_id: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/openapi/v2/text-to-3d/{provider_task_id}"
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=self._get_headers())
            if resp.status_code != 200:
                return {
                    "status": "failed",
                    "progress": 0,
                    "model_url": None,
                    "error": f"Failed to poll Meshy status [{resp.status_code}]: {resp.text}"
                }
            data = resp.json()
            raw_status = data.get("status", "").upper()
            progress = data.get("progress", 0)

            if raw_status in ("SUCCEEDED", "FINISHED"):
                model_urls = data.get("model_urls", {})
                glb_url = model_urls.get("glb")
                return {
                    "status": "completed",
                    "progress": 100,
                    "model_url": glb_url,
                    "error": None
                }
            elif raw_status in ("FAILED", "EXPIRED"):
                task_error = data.get("task_error", {}).get("message") or "Meshy task failed or expired"
                return {
                    "status": "failed",
                    "progress": progress,
                    "model_url": None,
                    "error": task_error
                }
            elif raw_status in ("IN_PROGRESS",):
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
                raise RuntimeError(f"Failed to download asset from Meshy [{resp.status_code}]")
            return resp.content

    def cancel_task(self, provider_task_id: str) -> bool:
        # Meshy does not provide a public cancellation endpoint in v2
        return False

    def get_usage_information(self) -> Dict[str, Any]:
        return {
            "provider": "meshy",
            "active": self.is_configured(),
            "cost_per_preview_usd": 0.05,
            "cost_per_refine_usd": 0.20
        }
