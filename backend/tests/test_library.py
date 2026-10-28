import pytest
import uuid
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.blender.blender_runner import BlenderRunner

client = TestClient(app)

def test_asset_and_project_management_lifecycle():
    runner = BlenderRunner()
    if not runner.is_available():
        pytest.skip("Blender not available for asset generation lifecycle test")

    suffix = uuid.uuid4().hex[:6]
    reg_resp = client.post("/api/auth/register", json={
        "email": f"designer_{suffix}@test.com",
        "username": f"designer_{suffix}",
        "password": "StudioPassword123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a project
    proj_resp = client.post("/api/projects", json={
        "name": "Modern Interior Pack",
        "description": "Furniture models for living room"
    }, headers=headers)
    assert proj_resp.status_code == 200
    project_id = proj_resp.json()["id"]

    # 2. Generate a procedural table inside this project
    gen_resp = client.post("/api/generations", json={
        "prompt": "coffee table 1m wide",
        "generation_mode": "procedural",
        "object_category": "table",
        "project_id": project_id,
        "export_format": "glb"
    }, headers=headers)
    assert gen_resp.status_code == 200
    job_id = gen_resp.json()["id"]

    # Poll until completed
    import time
    start = time.time()
    asset_id = None
    while time.time() - start < 25:
        poll = client.get(f"/api/generations/{job_id}", headers=headers).json()
        if poll["status"] == "completed" and poll["asset_id"]:
            asset_id = poll["asset_id"]
            break
        time.sleep(1.0)

    assert asset_id is not None, "Asset was not generated within time"

    # 3. List assets for user
    assets_resp = client.get("/api/assets", headers=headers)
    assert assets_resp.status_code == 200
    assets_list = assets_resp.json()
    assert len(assets_list) >= 1
    found = any(a["id"] == asset_id for a in assets_list)
    assert found is True

    # 4. Filter assets by project
    proj_assets = client.get(f"/api/assets?project_id={project_id}", headers=headers).json()
    assert len(proj_assets) >= 1
    assert proj_assets[0]["project_id"] == project_id

    # 5. Move asset out of project (unassign)
    patch_resp = client.patch(f"/api/assets/{asset_id}", json={"project_id": None}, headers=headers)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["project_id"] is None

    # 6. Delete individual asset
    del_resp = client.delete(f"/api/assets/{asset_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"

    # Verify asset is deleted
    get_del = client.get(f"/api/assets/{asset_id}", headers=headers)
    assert get_del.status_code == 404
