from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing() -> None:
    plain_password = "SecureTestPassword123!"
    password_hash = hash_password(plain_password)

    assert password_hash != plain_password
    assert verify_password(
        plain_password,
        password_hash,
    )
    assert not verify_password(
        "IncorrectPassword",
        password_hash,
    )


def test_access_token_creation() -> None:
    token = create_access_token(
        "test-user-id",
        additional_claims={
            "farm_id": "test-farm-id",
        },
    )

    payload = decode_token(token)

    assert payload["sub"] == "test-user-id"
    assert payload["farm_id"] == "test-farm-id"
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "jti" in payload


def test_refresh_token_creation() -> None:
    token = create_refresh_token("test-user-id")
    payload = decode_token(token)

    assert payload["sub"] == "test-user-id"
    assert payload["type"] == "refresh"
