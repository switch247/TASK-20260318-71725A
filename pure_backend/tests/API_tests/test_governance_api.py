def test_import_batch_with_quality_errors(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/governance/imports",
        json={
            "source_file_path": "imports/test.json",
            "rows": [
                {"row_number": 1, "payload_json": '{"value": 100}'},
                {"row_number": 2, "payload_json": '{"value": 100}'},
                {"row_number": 3, "payload_json": '{"value": -1}'},
                {"row_number": 4, "payload_json": ""},
                {"row_number": 5, "payload_json": '{"malformed": "json"'},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_rows"] == 5
    assert payload["failed_rows"] >= 1


def test_snapshot_create_and_rollback(client) -> None:  # type: ignore[no-untyped-def]
    create = client.post(
        "/api/v1/governance/snapshots",
        json={
            "domain": "metrics",
            "version": 1,
            "snapshot_payload_json": '{"kpi":"value"}',
            "lineage_from_snapshot_id": None,
        },
    )
    assert create.status_code == 200
    snapshot_id = create.json()["snapshot_id"]

    rollback = client.post(
        "/api/v1/governance/snapshots/rollback",
        json={"snapshot_id": snapshot_id},
    )
    assert rollback.status_code == 200
    assert rollback.json()["status"] == "rolled_back"


def test_bootstrap_jobs(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post("/api/v1/governance/jobs/bootstrap")

    assert response.status_code == 200
    jobs = response.json()["jobs"]
    assert len(jobs) == 2
    assert all(job["max_retries"] == 3 for job in jobs)
