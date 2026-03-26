"""Define auth request/response schemas including tokenized password recovery flow."""

from pydantic import BaseModel, Field, field_validator


def _looks_like_email(value: str) -> bool:
    if "@" not in value:
        return False
    local, domain = value.rsplit("@", 1)
    return local != "" and "." in domain and not domain.startswith(".") and not domain.endswith(".")


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email_or_empty(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        if not _looks_like_email(value):
            raise ValueError("Email must be empty or a valid email address")
        return value


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class PasswordResetRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    new_password: str = Field(min_length=8, max_length=128)


class PasswordRecoveryStartRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)


class PasswordRecoveryConfirmRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    recovery_token: str = Field(min_length=20)
    new_password: str = Field(min_length=8, max_length=128)


class PasswordRecoveryChallengeResponse(BaseModel):
    recovery_token: str
    challenge_type: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
