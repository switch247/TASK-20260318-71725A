import json

from sqlalchemy import select

from src.models.enums import JobStatus
from src.models.governance import DataSnapshot, SchedulerJobRecord


def test_snapshot_rollback_materializes_new_snapshot(client, db_session) -> None:  # type: ignore[no-untyped-def]
    created = client.post(
        "/api/v1/governance/snapshots",
        json={
            "domain": "metrics",
            "version": 1,
            "snapshot_payload_json": '{"value":10}',
            "lineage_from_snapshot_id": None,
        },
    )
    assert created.status_code == 200
    snapshot_id = created.json()["snapshot_id"]

    rollback = client.post(
        "/api/v1/governance/snapshots/rollback",
        json={"snapshot_id": snapshot_id},
    )
    assert rollback.status_code == 200

    stmt = select(DataSnapshot).where(DataSnapshot.lineage_from_snapshot_id == snapshot_id)
    derived = list(db_session.scalars(stmt))
    assert len(derived) == 1
    assert json.loads(derived[0].snapshot_payload_json)["value"] == 10


def test_execute_due_jobs_marks_success(client, db_session) -> None:  # type: ignore[no-untyped-def]
    bootstrap = client.post("/api/v1/governance/jobs/bootstrap")
    assert bootstrap.status_code == 200

    for job in db_session.scalars(select(SchedulerJobRecord)):
        job.next_run_at = job.created_at
    db_session.commit()

    execute = client.post("/api/v1/governance/jobs/execute")
    assert execute.status_code == 200
    payload = execute.json()
    assert payload["succeeded"] >= 1

    jobs = list(db_session.scalars(select(SchedulerJobRecord)))
    assert any(job.status == JobStatus.SUCCEEDED for job in jobs)


def test_archive_job_materializes_archive_snapshot(client, db_session) -> None:  # type: ignore[no-untyped-def]
    bootstrap = client.post("/api/v1/governance/jobs/bootstrap")
    assert bootstrap.status_code == 200

    for job in db_session.scalars(select(SchedulerJobRecord)):
        job.next_run_at = job.created_at
    db_session.commit()

    execute = client.post("/api/v1/governance/jobs/execute")
    assert execute.status_code == 200

    snapshots = list(
        db_session.scalars(
            select(DataSnapshot).where(DataSnapshot.domain.in_(["system_backup", "archive_summary"]))
        )
    )
    domains = {snapshot.domain for snapshot in snapshots}
    assert "system_backup" in domains
    assert "archive_summary" in domains
