"""Cover process parser and engine units after service split refactor."""

from datetime import datetime, timedelta

import pytest

from src.core.errors import ValidationError
from src.services.process_engine import ProcessEngine
from src.services.process_parser import ProcessParser


def test_process_parser_rejects_invalid_json() -> None:
    parser = ProcessParser()
    with pytest.raises(ValidationError):
        parser.parse_definition_json("not-json")


def test_process_engine_builds_parallel_and_joint_tasks() -> None:
    engine = ProcessEngine()
    tasks = engine.build_initial_tasks(
        organization_id="org-1",
        process_instance_id="proc-1",
        fallback_assignee_user_id="user-1",
        due_at=datetime.utcnow() + timedelta(hours=48),
        definition_json='{"nodes":[{"key":"a","is_parallel":true,"is_joint_sign":true}]}',
        payload_json='{"amount":100}',
    )

    assert len(tasks) == 1
    assert tasks[0].is_parallel is True
    assert tasks[0].is_joint_sign is True
