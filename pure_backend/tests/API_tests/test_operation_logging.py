from sqlalchemy import select

from src.models.security import ImmutableAuditLog, OperationLog


def test_mutating_auth_path_writes_operation_log(client, db_session) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/register",
        headers={"X-Trace-Id": "trace-auth-001"},
        json={
            "username": "oplog_user",
            "password": "Password123",
            "display_name": "Operation Log User",
            "email": "oplog@local.test",
        },
    )
    assert response.status_code == 200

    stmt = select(OperationLog).where(OperationLog.trace_id == "trace-auth-001")
    db_session.expire_all()
    logs = list(db_session.scalars(stmt))
    assert len(logs) >= 1
    assert any(log.operation == "create" and log.resource_type == "user" for log in logs)


def test_mutating_process_path_writes_operation_log(client, seeded_data, db_session) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/process/instances",
        headers={"X-Trace-Id": "trace-process-001"},
        json={
            "process_definition_id": seeded_data["process_definition_id"],
            "business_number": "OPLOG-BIZ-01",
            "idempotency_key": "oplog-idem-01",
            "payload_json": '{"amount":45}',
        },
    )
    assert response.status_code == 200

    stmt = select(OperationLog).where(OperationLog.trace_id == "trace-process-001")
    db_session.expire_all()
    logs = list(db_session.scalars(stmt))
    assert len(logs) >= 1
    assert any(
        log.resource_type == "process_instance" and log.operation == "create" for log in logs
    )


def test_mutating_path_appends_immutable_chain(client, seeded_data, db_session) -> None:  # type: ignore[no-untyped-def]
    before_count = len(list(db_session.scalars(select(ImmutableAuditLog))))

    response = client.post(
        "/api/v1/process/instances",
        headers={"X-Trace-Id": "trace-immutable-001"},
        json={
            "process_definition_id": seeded_data["process_definition_id"],
            "business_number": "IMM-BIZ-01",
            "idempotency_key": "imm-idem-01",
            "payload_json": '{"amount":46}',
        },
    )
    assert response.status_code == 200

    db_session.expire_all()
    after_count = len(list(db_session.scalars(select(ImmutableAuditLog))))
    assert after_count > before_count


def test_analytics_mutations_write_operation_log(client, db_session) -> None:  # type: ignore[no-untyped-def]
    report = client.post(
        "/api/v1/analytics/reports",
        headers={"X-Trace-Id": "trace-analytics-001"},
        json={
            "name": "Trace Report",
            "resource": "appointments",
            "filters_json": '{"status":"scheduled"}',
            "selected_fields_json": '["id"]',
        },
    )
    assert report.status_code == 200

    db_session.expire_all()
    logs = list(
        db_session.scalars(
            select(OperationLog).where(OperationLog.trace_id == "trace-analytics-001")
        )
    )
    assert any(
        log.resource_type == "report_definition" and log.operation == "create" for log in logs
    )
