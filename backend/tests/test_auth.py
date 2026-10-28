import pytest
import uuid
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_registration_and_login_flow():
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"user_{unique_suffix}@example.com"
    username = f"user_{unique_suffix}"
    password = "SecurePassword123!"

    # 1. Register new user
    reg_resp = client.post("/api/auth/register", json={
        "email": email,
        "username": username,
        "password": password
    })
    assert reg_resp.status_code == 200, f"Registration failed: {reg_resp.text}"
    data = reg_resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email
    assert data["user"]["username"] == username
    token = data["access_token"]
    user_id = data["user"]["id"]

    # 2. Reject duplicate email
    dup_email_resp = client.post("/api/auth/register", json={
        "email": email,
        "username": f"other_{unique_suffix}",
        "password": password
    })
    assert dup_email_resp.status_code == 400
    assert "email address already exists" in dup_email_resp.json()["detail"]

    # 3. Reject duplicate username
    dup_user_resp = client.post("/api/auth/register", json={
        "email": f"other_{unique_suffix}@example.com",
        "username": username,
        "password": password
    })
    assert dup_user_resp.status_code == 400
    assert "username is already taken" in dup_user_resp.json()["detail"]

    # 4. Login with email
    login_resp = client.post("/api/auth/login", json={
        "email_or_username": email,
        "password": password
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert login_data["user"]["id"] == user_id

    # 5. Login with username
    login_user_resp = client.post("/api/auth/login", json={
        "email_or_username": username,
        "password": password
    })
    assert login_user_resp.status_code == 200

    # 6. Reject invalid password
    bad_login_resp = client.post("/api/auth/login", json={
        "email_or_username": email,
        "password": "WrongPassword999"
    })
    assert bad_login_resp.status_code == 401

    # 7. Access /api/auth/me using bearer token
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["id"] == user_id
    assert me_data["email"] == email

    # 8. Reject forged/invalid token
    forged_resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.value"})
    assert forged_resp.status_code == 401

def test_multi_tenant_user_isolation():
    # Create User A
    u1_suffix = uuid.uuid4().hex[:6]
    u1_resp = client.post("/api/auth/register", json={
        "email": f"alpha_{u1_suffix}@test.com",
        "username": f"alpha_{u1_suffix}",
        "password": "AlphaPassword123!"
    })
    token_a = u1_resp.json()["access_token"]
    user_a_id = u1_resp.json()["user"]["id"]

    # Create User B
    u2_suffix = uuid.uuid4().hex[:6]
    u2_resp = client.post("/api/auth/register", json={
        "email": f"beta_{u2_suffix}@test.com",
        "username": f"beta_{u2_suffix}",
        "password": "BetaPassword123!"
    })
    token_b = u2_resp.json()["access_token"]

    # User A creates a private project
    proj_resp = client.post(
        "/api/projects",
        json={"name": "Alpha Private Assets", "description": "Confidential designs"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert proj_resp.status_code == 200
    project_id = proj_resp.json()["id"]

    # User B tries to view User A's project -> Expect 403 Forbidden
    unauthorized_get = client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert unauthorized_get.status_code == 403
    assert "Access denied" in unauthorized_get.json()["detail"]

    # User B tries to delete User A's project -> Expect 403 Forbidden
    unauthorized_del = client.delete(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert unauthorized_del.status_code == 403

    # User A CAN access their own project
    authorized_get = client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert authorized_get.status_code == 200
    assert authorized_get.json()["project"]["id"] == project_id
