from uuid import uuid4

from app.auth.jwt import create_access_token, decode_access_token


def test_create_and_decode_access_token():
    user_id = uuid4()

    token = create_access_token(
        user_id=user_id,
        authz_version=1,
    )

    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["authz_version"] == 1
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload

