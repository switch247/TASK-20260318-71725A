"""Validate real bearer-token auth paths without dependency override shortcuts."""

from fastapi.testclient import TestClient

from src.main import app


def test_real_bearer_auth_and_org_header_flow() -> None:
    with TestClient(app) as client:
        register = client.post(
            "/api/v1/auth/register",
            json={
                "username": "real_auth_user",
                "password": "Password123",
                "display_name": "Real Auth User",
                "email": "real@local.test",
            },
        )
        assert register.status_code == 200

        login = client.post(
            "/api/v1/auth/login",
            json={"username": "real_auth_user", "password": "Password123"},
        )
        assert login.status_code == 200
        access_token = login.json()["access_token"]

        create_org = client.post(
            "/api/v1/organizations",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"code": "REAL-ORG", "name": "Real Org"},
        )
        assert create_org.status_code == 200
        org_id = create_org.json()["id"]

        me_without_org = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_without_org.status_code in {401, 403}

        me_with_org = client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Organization-Id": org_id,
            },
        )
        assert me_with_org.status_code == 200
        assert me_with_org.json()["username"] == "real_auth_user"
