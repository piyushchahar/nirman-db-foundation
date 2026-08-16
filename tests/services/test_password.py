from app.auth.password import hash_password, verify_password


def test_hash_password_does_not_return_plaintext():
    password = "StrongPassword123!"

    hashed = hash_password(password)

    assert hashed != password


def test_verify_password_accepts_correct_password():
    password = "StrongPassword123!"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_rejects_wrong_password():
    password = "StrongPassword123!"
    hashed = hash_password(password)

    assert verify_password("WrongPassword123!", hashed) is False

