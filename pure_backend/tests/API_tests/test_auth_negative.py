from fastapi.testclient import TestClient
from src.services.crypto_service import build_access_token


def _override_get_session(test_session_factory):
    def _gen():
        session = test_session_factory()
        try:
            yield session
        finally:
            session.close()

    return _gen


def test_missing_bearer_token_returns_401(test_session_factory, seeded_data):
    from src.main import app
    from src.api.v1.dependencies import get_session

    app.dependency_overrides.clear()
    app.dependency_overrides[get_session] = _override_get_session(test_session_factory)

    with TestClient(app) as client:
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401


def test_invalid_bearer_token_returns_401(test_session_factory, seeded_data):
    from src.main import app
    from src.api.v1.dependencies import get_session

    app.dependency_overrides.clear()
    app.dependency_overrides[get_session] = _override_get_session(test_session_factory)

    with TestClient(app) as client:
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token"})
        assert resp.status_code == 401


def test_missing_org_header_returns_401_for_governance(test_session_factory, seeded_data):
    from src.main import app
    from src.api.v1.dependencies import get_session

    app.dependency_overrides.clear()
    app.dependency_overrides[get_session] = _override_get_session(test_session_factory)

    token, _ = build_access_token(seeded_data["admin_user_id"])
    with TestClient(app) as client:
        resp = client.get("/api/v1/governance/snapshots?domain=system_backup", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
