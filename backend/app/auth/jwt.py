from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.core.config import get_jwt_secret


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(
    user_id: UUID,
    authz_version: int,
) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "authz_version": authz_version,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        get_jwt_secret(),
        algorithms=[ALGORITHM],
    )
