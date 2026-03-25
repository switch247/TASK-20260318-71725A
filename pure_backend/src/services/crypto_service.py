import base64
import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from cryptography.fernet import Fernet
from jose import jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext  # type: ignore[import-untyped]

from src.core.config import get_settings
from src.core.constants import ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
settings = get_settings()


def hash_password(password: str) -> str:
    return cast(str, pwd_context.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return cast(bool, pwd_context.verify(plain_password, hashed_password))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_access_token(user_id: str) -> tuple[str, int]:
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": ACCESS_TOKEN_TYPE,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, settings.jwt_access_token_expire_minutes * 60


def build_refresh_token(user_id: str) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": REFRESH_TOKEN_TYPE,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return cast(str, token)


def decode_token(token: str) -> dict[str, object]:
    decoded: dict[str, Any] = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )
    return cast(dict[str, object], decoded)


def build_field_encryptor() -> Fernet:
    key_bytes = hashlib.sha256(settings.encryption_key.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


field_encryptor = build_field_encryptor()


def encrypt_sensitive(raw_text: str) -> str:
    return field_encryptor.encrypt(raw_text.encode("utf-8")).decode("utf-8")


def decrypt_sensitive(encrypted_text: str) -> str:
    return field_encryptor.decrypt(encrypted_text.encode("utf-8")).decode("utf-8")
