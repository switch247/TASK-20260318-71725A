def test_admin_can_create_process_definition(role_client_factory, seeded_data) -> None:  # type: ignore[no-untyped-def]
    client = role_client_factory(seeded_data["admin_user_id"])
    with client:
        response = client.post(
            "/api/v1/process/definitions",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
            json={
                "name": "Admin Workflow",
                "workflow_type": "credit_change",
                "definition_json": '{"nodes":[{"key":"n1"}]}',
            },
        )
    assert response.status_code == 200


def test_general_user_cannot_create_process_definition(role_client_factory, seeded_data) -> None:  # type: ignore[no-untyped-def]
    client = role_client_factory(seeded_data["general_user_id"])
    with client:
        response = client.post(
            "/api/v1/process/definitions",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
            json={
                "name": "Denied Workflow",
                "workflow_type": "credit_change",
                "definition_json": '{"nodes":[{"key":"n1"}]}',
            },
        )
    assert response.status_code == 403


def test_reviewer_can_list_pending_tasks(role_client_factory, seeded_data) -> None:  # type: ignore[no-untyped-def]
    client = role_client_factory(seeded_data["reviewer_user_id"])
    with client:
        response = client.get(
            "/api/v1/process/tasks/pending",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
        )
    assert response.status_code == 200


def test_auditor_cannot_submit_process_instance(role_client_factory, seeded_data) -> None:  # type: ignore[no-untyped-def]
    client = role_client_factory(seeded_data["auditor_user_id"])
    with client:
        response = client.post(
            "/api/v1/process/instances",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
            json={
                "process_definition_id": seeded_data["process_definition_id"],
                "business_number": "RBAC-BIZ-01",
                "idempotency_key": "rbac-idem-0001",
                "payload_json": '{"amount":99}',
            },
        )
    assert response.status_code == 403


def test_user_from_other_org_denied_by_membership(role_client_factory, seeded_data) -> None:  # type: ignore[no-untyped-def]
    client = role_client_factory(seeded_data["outsider_user_id"])
    with client:
        response = client.post(
            "/api/v1/process/instances",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
            json={
                "process_definition_id": seeded_data["process_definition_id"],
                "business_number": "RBAC-BIZ-02",
                "idempotency_key": "rbac-idem-0002",
                "payload_json": '{"amount":88}',
            },
        )
    assert response.status_code == 403


def test_auditor_cannot_append_audit(role_client_factory, seeded_data) -> None:  # type: ignore[no-untyped-def]
    client = role_client_factory(seeded_data["auditor_user_id"])
    with client:
        response = client.post(
            "/api/v1/security/audit/append",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
            json={
                "event_type": "system_event",
                "event_payload_json": '{"action": "test"}',
            },
        )
    assert response.status_code == 403


def test_admin_can_append_audit(role_client_factory, seeded_data) -> None:  # type: ignore[no-untyped-def]
    client = role_client_factory(seeded_data["admin_user_id"])
    with client:
        response = client.post(
            "/api/v1/security/audit/append",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
            json={
                "event_type": "custom_audit_event",
                "event_payload_json": '{"action": "test_append"}',
            },
        )
    assert response.status_code == 200
