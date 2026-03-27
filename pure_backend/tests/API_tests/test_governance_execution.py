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
            select(DataSnapshot).where(
                DataSnapshot.domain.in_(["system_backup", "archive_summary"])
            )
        )
    )
    domains = {snapshot.domain for snapshot in snapshots}
    assert "system_backup" in domains
    assert "archive_summary" in domains


def test_execute_due_jobs_fails_after_max_retries(client, db_session) -> None:  # type: ignore[no-untyped-def]
    bootstrap = client.post("/api/v1/governance/jobs/bootstrap")
    assert bootstrap.status_code == 200

    target = None
    for job in db_session.scalars(select(SchedulerJobRecord)):
        if job.job_type == "daily_full_backup":
            job.last_error = "force_failure"
            job.next_run_at = job.created_at
            target = job
            break
    db_session.commit()
    assert target is not None

    for _ in range(3):
        execute = client.post("/api/v1/governance/jobs/execute")
        assert execute.status_code == 200
        db_session.expire_all()
        tracked = db_session.scalar(
            select(SchedulerJobRecord).where(SchedulerJobRecord.id == target.id)
        )
        assert tracked is not None
        tracked.last_error = "force_failure"
        tracked.next_run_at = tracked.created_at
        db_session.commit()

    db_session.expire_all()
    failed = db_session.scalar(select(SchedulerJobRecord).where(SchedulerJobRecord.id == target.id))
    assert failed is not None
    assert failed is not None
    assert failed.status == JobStatus.FAILED
    assert failed.retry_count == failed.max_retries


def test_job_cross_tenant_isolation(client, db_session) -> None:  # type: ignore[no-untyped-def]
    bootstrap = client.post("/api/v1/governance/jobs/bootstrap")
    assert bootstrap.status_code == 200

    for job in db_session.scalars(select(SchedulerJobRecord)):
        job.next_run_at = job.created_at
    db_session.commit()

    execute = client.post("/api/v1/governance/jobs/execute")
    assert execute.status_code == 200

    snapshots = list(db_session.scalars(select(DataSnapshot)))
    assert len(snapshots) > 0
    org_id = snapshots[0].organization_id
    assert all(s.organization_id == org_id for s in snapshots)

def test_backup_job_writes_physical_backup_path(client, db_session) -> None:  # type: ignore[no-untyped-def]
    bootstrap = client.post("/api/v1/governance/jobs/bootstrap")
    assert bootstrap.status_code == 200

    for job in db_session.scalars(select(SchedulerJobRecord)):
        job.next_run_at = job.created_at
    db_session.commit()

    execute = client.post("/api/v1/governance/jobs/execute")
    assert execute.status_code == 200

    backup_snapshot = db_session.scalar(
        select(DataSnapshot).where(DataSnapshot.domain == "system_backup")
    )
    assert backup_snapshot is not None
    payload = json.loads(backup_snapshot.snapshot_payload_json)
    assert payload["physical_backup_path"] != ""


def test_archive_job_marks_physical_archive_mode(client, db_session) -> None:  # type: ignore[no-untyped-def]
    bootstrap = client.post("/api/v1/governance/jobs/bootstrap")
    assert bootstrap.status_code == 200

    for job in db_session.scalars(select(SchedulerJobRecord)):
        job.next_run_at = job.created_at
    db_session.commit()

    execute = client.post("/api/v1/governance/jobs/execute")
    assert execute.status_code == 200

    archive_snapshot = db_session.scalar(
        select(DataSnapshot).where(DataSnapshot.domain == "archive_summary")
    )
    assert archive_snapshot is not None
    payload = json.loads(archive_snapshot.snapshot_payload_json)
    assert payload["mode"] == "physical_archive"
