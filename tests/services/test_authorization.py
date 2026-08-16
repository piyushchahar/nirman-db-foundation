from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.auth.authorization import (
    AuthzVersionMismatchError,
    UserNotFoundError,
    authorize_user,
)


def test_authorize_user_accepts_matching_version():
    user = Mock()
    user.authz_version = 3

    db = Mock()
    db.query.return_value.filter.return_value.one_or_none.return_value = user

    user_id = uuid4()

    result = authorize_user(db, user_id, 3)

    assert result is user


def test_authorize_user_rejects_stale_version():
    user = Mock()
    user.authz_version = 3

    db = Mock()
    db.query.return_value.filter.return_value.one_or_none.return_value = user

    with pytest.raises(AuthzVersionMismatchError, match="stale"):
        authorize_user(db, uuid4(), 2)


def test_authorize_user_rejects_unknown_user():
    db = Mock()
    db.query.return_value.filter.return_value.one_or_none.return_value = None

    with pytest.raises(UserNotFoundError, match="User not found"):
        authorize_user(db, uuid4(), 1)

