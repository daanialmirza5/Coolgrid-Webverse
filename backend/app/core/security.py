from datetime import datetime, timedelta, timezone
from enum import Enum

import jwt
from passlib.context import CryptContext

from .config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    RESET = "reset"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta, extra_claims: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str, role: str) -> str:
    return _create_token(
        user_id,
        TokenType.ACCESS,
        timedelta(minutes=settings.access_token_expire_minutes),
        {"role": role},
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(user_id, TokenType.REFRESH, timedelta(days=settings.refresh_token_expire_days))


def create_reset_token(user_id: str) -> str:
    return _create_token(user_id, TokenType.RESET, timedelta(minutes=30))


class InvalidTokenError(Exception):
    pass


def decode_token(token: str, expected_type: TokenType) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as e:
        raise InvalidTokenError(str(e)) from e
    if payload.get("type") != expected_type.value:
        raise InvalidTokenError(f"Expected {expected_type.value} token, got {payload.get('type')}")
    return payload
