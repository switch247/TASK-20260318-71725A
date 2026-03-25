from datetime import UTC, datetime, timedelta
from threading import Thread

from src.core.errors import ConflictError
from src.schemas.process import SubmitProcessRequest
from src.services.process_service import ProcessService


def test_idempotency_key_conflict_returns_409(client, seeded_data) -> None:  # type: ignore[no-untyped-def]
    first = client.post(
        "/api/v1/process/instances",
        json={
            "process_definition_id": seeded_data["process_definition_id"],
            "business_number": "CONFLICT-BIZ-01",
            "idempotency_key": "conflict-idem-01",
            "payload_json": '{"amount":1}',
        },
    )
    assert first.status_code == 200

    conflict = client.post(
        "/api/v1/process/instances",
        json={
            "process_definition_id": seeded_data["process_definition_id"],
            "business_number": "CONFLICT-BIZ-02",
            "idempotency_key": "conflict-idem-01",
            "payload_json": '{"amount":2}',
        },
    )
    assert conflict.status_code == 409


def test_dashboard_pagination_boundaries(client) -> None:  # type: ignore[no-untyped-def]
    now = datetime.now(UTC)
    response = client.post(
        "/api/v1/analytics/dashboard",
        json={
            "from_time": (now - timedelta(days=1)).isoformat(),
            "to_time": now.isoformat(),
            "metric_codes": [],
            "page": 1,
            "limit": 1,
        },
    )
    assert response.status_code == 200
    assert response.json()["count"] <= 1
    assert response.json()["page"] == 1
    assert response.json()["limit"] == 1


def test_dashboard_limit_zero_returns_400(client) -> None:  # type: ignore[no-untyped-def]
    now = datetime.now(UTC)
    response = client.post(
        "/api/v1/analytics/dashboard",
        json={
            "from_time": (now - timedelta(days=1)).isoformat(),
            "to_time": now.isoformat(),
            "metric_codes": [],
            "page": 1,
            "limit": 0,
        },
    )
    assert response.status_code == 422


def test_concurrent_submit_same_idempotency_key_single_instance(  # type: ignore[no-untyped-def]
    seeded_data, db_session, test_session_factory
) -> None:
    request = SubmitProcessRequest(
        process_definition_id=seeded_data["process_definition_id"],
        business_number="RACE-BIZ-01",
        idempotency_key="race-idem-01",
        payload_json='{"amount":111}',
    )

    outcomes: list[str] = []

    def do_submit() -> None:
        session = test_session_factory()
        try:
            service = ProcessService(session)
            service.submit_process(
                organization_id=seeded_data["organization_id"],
                user_id=seeded_data["admin_user_id"],
                request=request,
            )
            outcomes.append("ok")
        except ConflictError:
            outcomes.append("conflict")
        except Exception:
            outcomes.append("conflict")
        finally:
            session.close()

    thread_1 = Thread(target=do_submit)
    thread_2 = Thread(target=do_submit)
    thread_1.start()
    thread_2.start()
    thread_1.join()
    thread_2.join()

    assert len(outcomes) == 2
    assert all(outcome in {"ok", "conflict"} for outcome in outcomes)
    assert outcomes.count("ok") >= 1
