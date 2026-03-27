from fastapi.testclient import TestClient

from src.main import app
from src.models.enums import UserStatus
from src.schemas.auth import RegisterRequest
from src.services.auth_service import AuthService


def test_register_success(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "new_user",
            "password": "Password123",
            "display_name": "New User",
            "email": "new@local.test",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "new_user"
    assert payload["display_name"] == "New User"


def test_register_rejects_weak_password(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "weak_user",
            "password": "password",
            "display_name": "Weak User",
            "email": "weak@local.test",
        },
    )

    assert response.status_code == 400
    assert response.json()["message"].startswith("Password must be")


def test_register_accepts_empty_email(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "empty_email_user",
            "password": "Password123",
            "display_name": "Empty Email",
            "email": "",
        },
    )

    assert response.status_code == 200


def test_register_rejects_invalid_email(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "invalid_email_user",
            "password": "Password123",
            "display_name": "Invalid Email",
            "email": "not-an-email",
        },
    )

    assert response.status_code == 422


def test_login_success(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_test", "password": "Admin1234"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert "access_token" in payload
    assert "refresh_token" in payload


def test_login_invalid_password(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_test", "password": "WrongPass123"},
    )

    assert response.status_code == 401


def test_password_recovery_token_flow(client) -> None:  # type: ignore[no-untyped-def]
    start = client.post(
        "/api/v1/auth/password/recovery/start",
        json={"username": "admin_test"},
    )
    assert start.status_code == 200
    token = start.json()["recovery_token"]
    assert start.json()["challenge_type"] == "signed_token"

    confirm = client.post(
        "/api/v1/auth/password/recovery/confirm",
        json={
            "username": "admin_test",
            "recovery_token": token,
            "new_password": "Recovered123",
        },
    )
    assert confirm.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_test", "password": "Recovered123"},
    )
    assert login.status_code == 200


def test_password_recovery_alias_endpoints(client) -> None:  # type: ignore[no-untyped-def]
    start = client.post(
        "/api/v1/auth/recovery/challenge",
        json={"username": "admin_test"},
    )
    assert start.status_code == 200
    token = start.json()["recovery_token"]

    reset = client.post(
        "/api/v1/auth/recovery/reset",
        json={
            "username": "admin_test",
            "recovery_token": token,
            "new_password": "Recovered456",
        },
    )
    assert reset.status_code == 200


def test_auth_me_accessible_without_org_header(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "admin_test"
    assert payload["role_name"] is None


def test_login_rejects_disabled_user(client, db_session) -> None:  # type: ignore[no-untyped-def]
    service = AuthService(db_session)
    service.register_user(
        request=RegisterRequest(
            username="disabled_user",
            password="Disabled123",
            display_name="Disabled User",
            email=None,
        )
    )

    user = service.repository.get_user_by_username("disabled_user")
    assert user is not None
    user.status = UserStatus.DISABLED
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "disabled_user", "password": "Disabled123"},
    )
    assert response.status_code == 401
    assert response.json()["message"] == "Account is disabled"


def test_password_reset_requires_recovery_token(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/password/reset",
        json={
            "username": "admin_test",
            "new_password": "Recovered999",
        },
    )
    assert response.status_code == 422


def test_password_reset_with_recovery_token_flow(client) -> None:  # type: ignore[no-untyped-def]
    start = client.post(
        "/api/v1/auth/password/recovery/start",
        json={"username": "admin_test"},
    )
    assert start.status_code == 200
    token = start.json()["recovery_token"]

    reset = client.post(
        "/api/v1/auth/password/reset",
        json={
            "username": "admin_test",
            "recovery_token": token,
            "new_password": "ResetFlow123",
        },
    )
    assert reset.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_test", "password": "ResetFlow123"},
    )
    assert login.status_code == 200


def test_refresh_rotates_token(client) -> None:  # type: ignore[no-untyped-def]
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_test", "password": "ResetFlow123"},
    )
    if login.status_code != 200:
        login = client.post(
            "/api/v1/auth/login",
            json={"username": "admin_test", "password": "Admin1234"},
        )
    assert login.status_code == 200
    original_refresh_token = login.json()["refresh_token"]

    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )
    assert refresh.status_code == 200
    rotated_refresh_token = refresh.json()["refresh_token"]

    replay = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )
    assert replay.status_code == 401

    second_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rotated_refresh_token},
    )
    assert second_refresh.status_code == 200


def test_logout_revokes_token(client) -> None:  # type: ignore[no-untyped-def]
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "reviewer_test", "password": "Review1234"},
    )
    assert login.status_code == 200
    refresh_token = login.json()["refresh_token"]

    logout = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout.status_code == 200

    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh.status_code == 401


def test_protected_route_requires_bearer_token() -> None:  # type: ignore[no-untyped-def]
    with TestClient(app) as local_client:
        response = local_client.post(
            "/api/v1/process/definitions",
            headers={"X-Organization-Id": "org-missing-auth"},
            json={
                "name": "Auth Required",
                "workflow_type": "credit_change",
                "definition_json": "{\"nodes\":[{\"key\":\"n1\"}]}",
            },
        )
    assert response.status_code == 401
