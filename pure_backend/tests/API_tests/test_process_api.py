from datetime import datetime, timedelta

from sqlalchemy import select

from src.models.enums import ProcessStatus
from src.models.process import ProcessInstance


def test_create_process_definition_success(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/process/definitions",
        json={
            "name": "Credit Approval",
            "workflow_type": "credit_change",
            "definition_json": '{"nodes":[{"key":"n1"}]}',
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Credit Approval"


def test_submit_process_instance_success(client, seeded_data) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/process/instances",
        json={
            "process_definition_id": seeded_data["process_definition_id"],
            "business_number": "BIZ-001",
            "idempotency_key": "idem-key-001",
            "payload_json": '{"amount":100}',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["business_number"] == "BIZ-001"
    assert payload["status"] == "in_progress"


def test_submit_process_instance_idempotent(client, seeded_data, db_session) -> None:  # type: ignore[no-untyped-def]
    body = {
        "process_definition_id": seeded_data["process_definition_id"],
        "business_number": "BIZ-002",
        "idempotency_key": "idem-key-002",
        "payload_json": '{"amount":200}',
    }
    
    count_before = db_session.query(ProcessInstance).count()
    first = client.post("/api/v1/process/instances", json=body)
    second = client.post("/api/v1/process/instances", json=body)
    count_after = db_session.query(ProcessInstance).count()

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert count_after == count_before + 1


def test_pending_tasks_and_decision_flow(client, seeded_data) -> None:  # type: ignore[no-untyped-def]
    submit = client.post(
        "/api/v1/process/instances",
        json={
            "process_definition_id": seeded_data["process_definition_id"],
            "business_number": "BIZ-003",
            "idempotency_key": "idem-key-003",
            "payload_json": '{"amount":300}',
        },
    )
    assert submit.status_code == 200

    pending = client.get("/api/v1/process/tasks/pending")
    assert pending.status_code == 200
    items = pending.json()["items"]
    assert len(items) >= 1

    task_id = items[0]["id"]
    decide = client.post(
        "/api/v1/process/tasks/decision",
        json={"task_id": task_id, "decision": "approve", "comment": "ok"},
    )
    assert decide.status_code == 200
    assert decide.json()["status"] == "approved"


def test_workflow_branch_and_parallel_nodes_execute(client, seeded_data) -> None:  # type: ignore[no-untyped-def]
    definition_response = client.post(
        "/api/v1/process/definitions",
        json={
            "name": "Branch Parallel Workflow",
            "workflow_type": "credit_change",
            "definition_json": '{"nodes":[{"key":"review-gt","condition":{"field":"amount","operator":"gt","value":100},"is_parallel":true,"is_joint_sign":false},{"key":"review-gte","condition":{"field":"amount","operator":"gte","value":100},"is_parallel":true,"is_joint_sign":true}]}',
        },
    )
    assert definition_response.status_code == 200
    definition_id = definition_response.json()["id"]

    submit = client.post(
        "/api/v1/process/instances",
        json={
            "process_definition_id": definition_id,
            "business_number": "BIZ-BRANCH-01",
            "idempotency_key": "idem-branch-01",
            "payload_json": '{"amount":150}',
        },
    )
    assert submit.status_code == 200

    pending = client.get("/api/v1/process/tasks/pending")
    assert pending.status_code == 200
    items = pending.json()["items"]
    node_keys = {item["task_node_key"] for item in items}
    assert "review-gt" in node_keys
    assert "review-gte" in node_keys


def test_workflow_parallel_and_joint_flags_exposed(client) -> None:  # type: ignore[no-untyped-def]
    definition_response = client.post(
        "/api/v1/process/definitions",
        json={
            "name": "Parallel Joint Workflow",
            "workflow_type": "credit_change",
            "definition_json": '{"nodes":[{"key":"joint-node","is_parallel":true,"is_joint_sign":true}]}',
        },
    )
    assert definition_response.status_code == 200
    definition_id = definition_response.json()["id"]

    submit = client.post(
        "/api/v1/process/instances",
        json={
            "process_definition_id": definition_id,
            "business_number": "BIZ-JOINT-01",
            "idempotency_key": "idem-joint-01",
            "payload_json": '{"amount":50}',
        },
    )
    assert submit.status_code == 200

    pending = client.get("/api/v1/process/tasks/pending")
    assert pending.status_code == 200
    items = pending.json()["items"]
    matching = [item for item in items if item["task_node_key"] == "joint-node"]
    assert len(matching) == 1
    assert matching[0]["is_parallel"] == "true"
    assert matching[0]["is_joint_sign"] == "true"


def test_joint_sign_requires_all_approvals(client) -> None:  # type: ignore[no-untyped-def]
    definition_response = client.post(
        "/api/v1/process/definitions",
        json={
            "name": "Joint Sign Workflow",
            "workflow_type": "credit_change",
            "definition_json": '{"nodes":[{"key":"j1","is_joint_sign":true},{"key":"j2","is_joint_sign":true}]}',
        },
    )
    assert definition_response.status_code == 200
    definition_id = definition_response.json()["id"]

    submit = client.post(
        "/api/v1/process/instances",
        json={
            "process_definition_id": definition_id,
            "business_number": "JOINT-BIZ-01",
            "idempotency_key": "joint-idem-01",
            "payload_json": '{"amount":50}',
        },
    )
    assert submit.status_code == 200

    pending = client.get("/api/v1/process/tasks/pending")
    joint_tasks = [
        item for item in pending.json()["items"] if item["task_node_key"] in {"j1", "j2"}
    ]
    assert len(joint_tasks) >= 2

    first_decision = client.post(
        "/api/v1/process/tasks/decision",
        json={"task_id": joint_tasks[0]["id"], "decision": "approve", "comment": "first"},
    )
    assert first_decision.status_code == 200

    second_decision = client.post(
        "/api/v1/process/tasks/decision",
        json={"task_id": joint_tasks[1]["id"], "decision": "approve", "comment": "second"},
    )
    assert second_decision.status_code == 200


def test_parallel_node_completes_on_first_response(client, seeded_data, db_session) -> None:  # type: ignore[no-untyped-def]
    definition_response = client.post(
        "/api/v1/process/definitions",
        json={
            "name": "Parallel Completion Workflow",
            "workflow_type": "credit_change",
            "definition_json": '{"nodes":[{"key":"p1","is_parallel":true},{"key":"p2","is_parallel":true}]}',
        },
    )
    assert definition_response.status_code == 200
    definition_id = definition_response.json()["id"]

    submit = client.post(
        "/api/v1/process/instances",
        json={
            "process_definition_id": definition_id,
            "business_number": "PARALLEL-BIZ-01",
            "idempotency_key": "parallel-idem-01",
            "payload_json": '{"amount":77}',
        },
    )
    assert submit.status_code == 200
    instance_id = submit.json()["id"]

    pending = client.get("/api/v1/process/tasks/pending")
    assert pending.status_code == 200
    parallel_tasks = [
        item for item in pending.json()["items"] if item["task_node_key"] in {"p1", "p2"}
    ]
    assert len(parallel_tasks) >= 2

    decide = client.post(
        "/api/v1/process/tasks/decision",
        json={"task_id": parallel_tasks[0]["id"], "decision": "approve", "comment": "first"},
    )
    assert decide.status_code == 200

    instance = db_session.scalar(select(ProcessInstance).where(ProcessInstance.id == instance_id))
    assert instance is not None
    assert instance.status == ProcessStatus.APPROVED


def test_dispatch_sla_reminders_once(client, seeded_data, db_session) -> None:  # type: ignore[no-untyped-def]
    create = client.post(
        "/api/v1/process/definitions",
        json={
            "name": "Reminder Flow",
            "workflow_type": "credit_change",
            "definition_json": '{"nodes":[{"key":"n-reminder"}]}',
        },
    )
    assert create.status_code == 200
    definition_id = create.json()["id"]

    submit = client.post(
        "/api/v1/process/instances",
        json={
            "process_definition_id": definition_id,
            "business_number": "REMINDER-BIZ-01",
            "idempotency_key": "idem-reminder-01",
            "payload_json": '{"amount":42}',
        },
    )
    assert submit.status_code == 200

    stmt = select(ProcessInstance).where(ProcessInstance.business_number == "REMINDER-BIZ-01")
    instance = db_session.scalar(stmt)
    assert instance is not None
    instance.due_at = datetime.utcnow() + timedelta(minutes=30)
    db_session.commit()

    first_dispatch = client.post("/api/v1/process/reminders/dispatch")
    assert first_dispatch.status_code == 200
    first_payload = first_dispatch.json()
    assert first_payload["reminded_count"] >= 1

    second_dispatch = client.post("/api/v1/process/reminders/dispatch")
    assert second_dispatch.status_code == 200
    second_payload = second_dispatch.json()
    assert second_payload["reminded_count"] == 0


def test_dispatch_sla_reminders_requires_manage_permission(  # type: ignore[no-untyped-def]
    role_client_factory, seeded_data
) -> None:
    client = role_client_factory(seeded_data["reviewer_user_id"])
    with client:
        response = client.post(
            "/api/v1/process/reminders/dispatch",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
        )
    assert response.status_code == 403
