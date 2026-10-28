import pytest
import os
import json
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.blender.blender_runner import BlenderRunner
from backend.app.services.generation.router import detect_procedural_category, extract_dimensions_from_prompt

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["database_connected"] is True
    assert "blender_available" in data

def test_capabilities_endpoint():
    response = client.get("/api/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "supported_procedural_categories" in data
    assert "table" in data["supported_procedural_categories"]
    assert "chair" in data["supported_procedural_categories"]
    assert "house" in data["supported_procedural_categories"]

def test_router_category_detection():
    assert detect_procedural_category("modern wooden dining table with black legs") == "table"
    assert detect_procedural_category("an ergonomic office chair with cushion") == "chair"
    assert detect_procedural_category("a cozy cottage house with red roof") == "house"
    assert detect_procedural_category("classical marble column with fluting") == "column"
    assert detect_procedural_category("asphalt two-lane road segment") == "road_segment"
    assert detect_procedural_category("cyberpunk glowing platform base") == "platform"

def test_router_dimension_extraction():
    dims = extract_dimensions_from_prompt("table 2.5m wide and 1.2m deep and 0.8m high")
    assert dims.get("width") == 2.5
    assert dims.get("depth") == 1.2
    assert dims.get("height") == 0.8

def test_procedural_generation_and_export_flow():
    runner = BlenderRunner()
    if not runner.is_available():
        pytest.skip("Blender executable not available in this test environment")

    # 1. Submit procedural generation job
    req_payload = {
        "prompt": "rustic oak dining table 1.8m wide",
        "generation_mode": "procedural",
        "object_category": "table",
        "style": "rustic",
        "export_format": "glb"
    }
    create_resp = client.post("/api/generations", json=req_payload)
    assert create_resp.status_code == 200
    job_data = create_resp.json()
    job_id = job_data["id"]
    assert job_data["status"] in ("queued", "running")

    # 2. Wait briefly for worker thread to complete
    import time
    max_wait = 25
    start = time.time()
    final_job = None
    while time.time() - start < max_wait:
        poll_resp = client.get(f"/api/generations/{job_id}")
        assert poll_resp.status_code == 200
        final_job = poll_resp.json()
        if final_job["status"] in ("completed", "failed"):
            break
        time.sleep(1.0)

    assert final_job is not None
    assert final_job["status"] == "completed", f"Job failed: {final_job.get('safe_error_message')}"
    assert final_job["asset_id"] is not None
    asset_id = final_job["asset_id"]

    # 3. Retrieve Asset metadata
    asset_resp = client.get(f"/api/assets/{asset_id}")
    assert asset_resp.status_code == 200
    asset_data = asset_resp.json()
    assert asset_data["file_format"] == "glb"
    assert asset_data["file_size"] > 0
    assert asset_data["validation_status"] == "valid"
    assert asset_data["polygon_count"] > 0

    # 4. Fetch the real 3D model file
    file_resp = client.get(f"/api/assets/{asset_id}/file")
    assert file_resp.status_code == 200
    assert len(file_resp.content) == asset_data["file_size"]
    assert file_resp.content.startswith(b"glTF") # Valid glTF 2.0 binary header
