import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.https import HttpsEnforcementMiddleware


def test_https_enforced_when_enabled() -> None:
    app = FastAPI()
    app.add_middleware(HttpsEnforcementMiddleware)

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 400
    assert response.json()["message"] == "HTTPS is required"


def test_https_allows_forwarded_proto_https() -> None:
    app = FastAPI()
    app.add_middleware(HttpsEnforcementMiddleware)

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get(
        "/api/v1/health",
        headers={"X-Forwarded-Proto": "https"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.fixture(autouse=True)
def restore_https_setting() -> None:
    yield
    os.environ["ENFORCE_HTTPS"] = "false"
