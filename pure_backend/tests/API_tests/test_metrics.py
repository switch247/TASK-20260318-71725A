"""Verify lightweight metrics endpoint and counters for operational visibility."""


def test_metrics_endpoint_exposes_counters(client) -> None:  # type: ignore[no-untyped-def]
    _ = client.get("/api/v1/health")
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert "requests_total" in payload
    assert payload["requests_total"] >= 2
