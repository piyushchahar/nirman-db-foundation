from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User


class AuthorizationError(Exception):
    """Base authorization error."""


class UserNotFoundError(AuthorizationError):
    """Raised when the user does not exist."""


class AuthzVersionMismatchError(AuthorizationError):
    """Raised when the token's authorization version is stale."""


def authorize_user(
    db: Session,
    user_id: UUID,
    token_authz_version: int,
) -> User:
    user = db.query(User).filter(User.id == user_id).one_or_none()

    if user is None:
        raise UserNotFoundError("User not found")

    if user.authz_version != token_authz_version:
        raise AuthzVersionMismatchError("Authorization version is stale")

    return user
