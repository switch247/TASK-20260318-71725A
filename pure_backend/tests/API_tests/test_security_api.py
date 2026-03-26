import base64
import json

import pytest

from src.core.constants import MAX_LOGIN_ATTEMPTS
from src.core.errors import UnauthorizedError
from src.schemas.auth import LoginRequest, RegisterRequest
from src.services.auth_service import AuthService


def test_attachment_accepts_exact_20mb_limit(client) -> None:  # type: ignore[no-untyped-def]
    size = 20 * 1024 * 1024
    content = b"a" * size
    encoded = base64.b64encode(content).decode("utf-8")

    response = client.post(
        "/api/v1/security/attachments",
        json={
            "process_instance_id": None,
            "business_number": None,
            "file_name": "exact_20mb.txt",
            "mime_type": "text/plain",
            "file_size_bytes": size,
            "file_content_base64": encoded,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["deduplicated"] == "false"
    assert "attachment_id" in payload


def test_attachment_rejects_over_20mb_limit(client) -> None:  # type: ignore[no-untyped-def]
    size = 20 * 1024 * 1024 + 1
    content = b"b" * size
    encoded = base64.b64encode(content).decode("utf-8")

    response = client.post(
        "/api/v1/security/attachments",
        json={
            "process_instance_id": None,
            "business_number": None,
            "file_name": "over_20mb.txt",
            "mime_type": "text/plain",
            "file_size_bytes": size,
            "file_content_base64": encoded,
        },
    )

    assert response.status_code == 400
    assert response.json()["message"] == "File exceeds maximum allowed size"


def test_attachment_rejects_declared_size_mismatch(client) -> None:  # type: ignore[no-untyped-def]
    content = b"1234567890"
    encoded = base64.b64encode(content).decode("utf-8")

    response = client.post(
        "/api/v1/security/attachments",
        json={
            "process_instance_id": None,
            "business_number": None,
            "file_name": "mismatch.txt",
            "mime_type": "text/plain",
            "file_size_bytes": 1,
            "file_content_base64": encoded,
        },
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Declared file size does not match uploaded payload"


def test_attachment_deduplicates_same_fingerprint(client) -> None:  # type: ignore[no-untyped-def]
    content = b"deduplicate-content"
    encoded = base64.b64encode(content).decode("utf-8")
    size = len(content)

    first = client.post(
        "/api/v1/security/attachments",
        json={
            "process_instance_id": None,
            "business_number": None,
            "file_name": "dup1.txt",
            "mime_type": "text/plain",
            "file_size_bytes": size,
            "file_content_base64": encoded,
        },
    )
    second = client.post(
        "/api/v1/security/attachments",
        json={
            "process_instance_id": None,
            "business_number": None,
            "file_name": "dup2.txt",
            "mime_type": "text/plain",
            "file_size_bytes": size,
            "file_content_base64": encoded,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["deduplicated"] == "true"
    assert first.json()["attachment_id"] == second.json()["attachment_id"]


def test_attachment_dedup_is_organization_scoped(  # type: ignore[no-untyped-def]
    role_client_factory, seeded_data
) -> None:
    content = b"org-scoped-dedup-content"
    encoded = base64.b64encode(content).decode("utf-8")
    size = len(content)

    admin_client = role_client_factory(seeded_data["admin_user_id"])
    with admin_client:
        first = admin_client.post(
            "/api/v1/security/attachments",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
            json={
                "process_instance_id": None,
                "business_number": None,
                "file_name": "org1.txt",
                "mime_type": "text/plain",
                "file_size_bytes": size,
                "file_content_base64": encoded,
            },
        )
    assert first.status_code == 200
    assert first.json()["deduplicated"] == "false"

    outsider_client = role_client_factory(seeded_data["outsider_user_id"])
    with outsider_client:
        second = outsider_client.post(
            "/api/v1/security/attachments",
            headers={"X-Organization-Id": seeded_data["organization_two_id"]},
            json={
                "process_instance_id": None,
                "business_number": None,
                "file_name": "org2.txt",
                "mime_type": "text/plain",
                "file_size_bytes": size,
                "file_content_base64": encoded,
            },
        )
    assert second.status_code == 200
    assert second.json()["deduplicated"] == "false"
    assert first.json()["attachment_id"] != second.json()["attachment_id"]


def test_get_attachment_not_found(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get(
        "/api/v1/security/attachments/non-existent-id?business_number=BIZ-UNKNOWN",
    )

    assert response.status_code == 404


def test_append_immutable_audit(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/security/audit/append",
        json={
            "event_type": "manual_audit",
            "event_payload_json": json.dumps({"key": "value"}),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "audit_id" in payload
    assert len(payload["current_hash"]) == 64


def test_attachment_requires_matching_business_context(client, seeded_data) -> None:  # type: ignore[no-untyped-def]
    submit = client.post(
        "/api/v1/process/instances",
        json={
            "process_definition_id": seeded_data["process_definition_id"],
            "business_number": "ATTACH-BIZ-01",
            "idempotency_key": "attach-idem-01",
            "payload_json": '{"amount":123}',
        },
    )
    assert submit.status_code == 200

    content = b"attachment-business-context"
    encoded = base64.b64encode(content).decode("utf-8")

    create_attachment = client.post(
        "/api/v1/security/attachments",
        json={
            "process_instance_id": submit.json()["id"],
            "business_number": "ATTACH-BIZ-01",
            "file_name": "biz.txt",
            "mime_type": "text/plain",
            "file_size_bytes": len(content),
            "file_content_base64": encoded,
        },
    )
    assert create_attachment.status_code == 200
    attachment_id = create_attachment.json()["attachment_id"]

    wrong_context_read = client.get(
        f"/api/v1/security/attachments/{attachment_id}?business_number=ATTACH-BIZ-OTHER",
    )
    assert wrong_context_read.status_code == 403

    right_context_read = client.get(
        f"/api/v1/security/attachments/{attachment_id}?business_number=ATTACH-BIZ-01",
    )
    assert right_context_read.status_code == 200


def test_attachment_storage_path_masked_for_non_admin(  # type: ignore[no-untyped-def]
    role_client_factory, seeded_data
) -> None:
    admin_client = role_client_factory(seeded_data["admin_user_id"])
    with admin_client:
        submit = admin_client.post(
            "/api/v1/process/instances",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
            json={
                "process_definition_id": seeded_data["process_definition_id"],
                "business_number": "MASK-BIZ-01",
                "idempotency_key": "mask-idem-01",
                "payload_json": '{"amount":100}',
            },
        )
        assert submit.status_code == 200

        content = b"mask-path"
        encoded = base64.b64encode(content).decode("utf-8")
        create_attachment = admin_client.post(
            "/api/v1/security/attachments",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
            json={
                "process_instance_id": submit.json()["id"],
                "business_number": "MASK-BIZ-01",
                "file_name": "mask.txt",
                "mime_type": "text/plain",
                "file_size_bytes": len(content),
                "file_content_base64": encoded,
            },
        )
        assert create_attachment.status_code == 200
        attachment_id = create_attachment.json()["attachment_id"]

    reviewer_client = role_client_factory(seeded_data["reviewer_user_id"])
    with reviewer_client:
        read_attachment = reviewer_client.get(
            f"/api/v1/security/attachments/{attachment_id}?business_number=MASK-BIZ-01",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
        )
        assert read_attachment.status_code == 200
        assert read_attachment.json()["storage_path"].startswith(".../")


def test_attachment_create_rejects_wrong_business_context_early(  # type: ignore[no-untyped-def]
    client, seeded_data
) -> None:
    submit = client.post(
        "/api/v1/process/instances",
        json={
            "process_definition_id": seeded_data["process_definition_id"],
            "business_number": "ATTACH-BIZ-02",
            "idempotency_key": "attach-idem-02",
            "payload_json": '{"amount":321}',
        },
    )
    assert submit.status_code == 200

    content = b"invalid-business-context"
    encoded = base64.b64encode(content).decode("utf-8")

    create_attachment = client.post(
        "/api/v1/security/attachments",
        json={
            "process_instance_id": submit.json()["id"],
            "business_number": "ATTACH-BIZ-WRONG",
            "file_name": "wrong-biz.txt",
            "mime_type": "text/plain",
            "file_size_bytes": len(content),
            "file_content_base64": encoded,
        },
    )
    assert create_attachment.status_code == 403


def test_login_lockout_after_repeated_failures(db_session) -> None:  # type: ignore[no-untyped-def]
    good_password = "Lockout123"
    bad_password = "Wrong12345"

    service = AuthService(db_session)
    service.register_user(
        request=RegisterRequest(
            username="lockout_user",
            password=good_password,
            display_name="Lockout User",
            email=None,
        )
    )

    for _ in range(MAX_LOGIN_ATTEMPTS):
        with pytest.raises(UnauthorizedError):
            service.login_user(
                request=LoginRequest(username="lockout_user", password=bad_password),
                user_agent=None,
                ip_address=None,
            )

    user = service.repository.get_user_by_username("lockout_user")
    assert user is not None
    assert user.locked_until is not None
