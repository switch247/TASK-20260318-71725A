from datetime import UTC, datetime, timedelta


def test_dashboard_metrics(client) -> None:  # type: ignore[no-untyped-def]
    now = datetime.now(UTC)
    response = client.post(
        "/api/v1/analytics/dashboard",
        json={
            "from_time": (now - timedelta(days=1)).isoformat(),
            "to_time": now.isoformat(),
            "metric_codes": ["activity"],
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] >= 1
    assert response.json()["items"][0]["kpi_type"] in {
        "activity",
        "message_reach",
        "attendance_anomaly",
        "work_order_sla",
        "custom",
    }


def test_dashboard_known_kpi_types_resolve(client) -> None:  # type: ignore[no-untyped-def]
    now = datetime.now(UTC)
    response = client.post(
        "/api/v1/analytics/dashboard",
        json={
            "from_time": (now - timedelta(days=1)).isoformat(),
            "to_time": now.isoformat(),
            "metric_codes": [
                "activity",
                "message_reach",
                "attendance_anomaly",
                "work_order_sla",
            ],
        },
    )
    assert response.status_code == 200
    kpi_types = {item["kpi_type"] for item in response.json()["items"]}
    assert "activity" in kpi_types
    assert "message_reach" in kpi_types
    assert "attendance_anomaly" in kpi_types
    assert "work_order_sla" in kpi_types


def test_create_report(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/analytics/reports",
        json={
            "name": "Ops Report",
            "resource": "appointments",
            "filters_json": '{"status":"scheduled"}',
            "selected_fields_json": '["id","status"]',
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Ops Report"


def test_create_export_task(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/analytics/exports",
        json={
            "resource": "appointments",
            "field_whitelist_json": '["id","status"]',
            "desensitization_policy_json": '{"phone":"phone"}',
            "query_filters_json": '{"status":"scheduled"}',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "pending"
    assert payload["trace_code"].startswith("EXP-")


def test_execute_export_task_generates_result_file(client) -> None:  # type: ignore[no-untyped-def]
    created = client.post(
        "/api/v1/analytics/exports",
        json={
            "resource": "appointments",
            "field_whitelist_json": '["id","status"]',
            "desensitization_policy_json": '{"status":"name"}',
            "query_filters_json": '{"status":"scheduled"}',
        },
    )
    assert created.status_code == 200
    task_id = created.json()["task_id"]

    execute = client.post(f"/api/v1/analytics/exports/{task_id}/execute")
    assert execute.status_code == 200
    payload = execute.json()
    assert payload["status"] == "succeeded"
    assert payload["result_path"].endswith(".json")
    assert payload["count"] >= 1


def test_export_preview_applies_whitelist_and_desensitization(  # type: ignore[no-untyped-def]
    role_client_factory, seeded_data
) -> None:
    client = role_client_factory(seeded_data["reviewer_user_id"])
    with client:
        response = client.post(
            "/api/v1/analytics/exports/preview",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
            json={
                "field_whitelist_json": '["phone","name"]',
                "desensitization_policy_json": '{"phone":"phone"}',
                "rows": [
                    {
                        "values": {
                            "phone": "13812345678",
                            "name": "Alice",
                            "id_number": "110101199001011234",
                        }
                    }
                ],
            },
        )

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["phone"] == "138****5678"
    assert "id_number" not in items[0]


def test_advanced_operations_search_doctors(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/operations/search",
        json={
            "resource": "doctors",
            "keyword": "Doctor",
            "department": "Cardiology",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["resource"] == "doctors"
    assert payload["count"] >= 1
