from src.services.demo_seed_service import seed_demo_dataset


def test_demo_seed_service_creates_dataset(unit_db_session) -> None:  # type: ignore[no-untyped-def]
    result = seed_demo_dataset(unit_db_session)

    assert "organization_id" in result
    assert "admin_user_id" in result
    assert "process_definition_id" in result
