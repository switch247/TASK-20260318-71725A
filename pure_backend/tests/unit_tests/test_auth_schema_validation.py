import pytest
from pydantic import ValidationError

from src.schemas.auth import RegisterRequest

VALID_PASSWORD = "Password123"


def test_register_accepts_empty_email() -> None:
    payload = RegisterRequest(
        username="valid_user",
        password=VALID_PASSWORD,
        display_name="Valid User",
        email="",
    )
    assert payload.email == ""


def test_register_accepts_valid_email() -> None:
    payload = RegisterRequest(
        username="valid_user2",
        password=VALID_PASSWORD,
        display_name="Valid User 2",
        email="user@example.com",
    )
    assert payload.email == "user@example.com"


def test_register_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            username="invalid_email",
            password=VALID_PASSWORD,
            display_name="Invalid Email",
            email="invalid-email",
        )
