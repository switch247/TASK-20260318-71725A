from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main import unhandled_exception_handler


def test_global_exception_handler_returns_json() -> None:
    app = FastAPI(debug=False)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.get("/boom")
    def boom() -> dict[str, str]:
        raise RuntimeError("boom")

    local_client = TestClient(app, raise_server_exceptions=False)
    response = local_client.get("/boom")
    assert response.status_code == 500
    payload = response.json()
    assert payload["code"] == 500
    assert payload["message"] == "Internal server error"
    assert payload["details"] == {}


def test_global_exception_handler_does_not_echo_secret_in_body() -> None:
    app = FastAPI(debug=False)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    @app.get("/boom-secret")
    def boom_secret() -> dict[str, str]:
        raise RuntimeError("password=SuperSecret123")

    local_client = TestClient(app, raise_server_exceptions=False)
    response = local_client.get("/boom-secret")
    assert response.status_code == 500
    payload = response.json()
    serialized = str(payload)
    assert "SuperSecret123" not in serialized
    assert "password" not in serialized.lower()
