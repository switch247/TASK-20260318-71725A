"""Verify masking behavior for non-admin sensitive response paths beyond export preview."""


def test_me_masks_email_for_non_admin(role_client_factory, seeded_data) -> None:  # type: ignore[no-untyped-def]
    client = role_client_factory(seeded_data["reviewer_user_id"])
    with client:
        response = client.get(
            "/api/v1/auth/me",
            headers={"X-Organization-Id": seeded_data["organization_id"]},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["role_name"] == "reviewer"
    assert payload["email"] is not None
    assert "***" in payload["email"]
