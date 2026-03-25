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
