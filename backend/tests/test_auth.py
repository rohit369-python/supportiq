"""Basic auth and security tests (run with pytest against a test DB or mocks)."""

import pytest
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token


def test_password_hash_and_verify():
    hashed = get_password_hash("TestPassword1")
    assert verify_password("TestPassword1", hashed)
    assert not verify_password("WrongPassword", hashed)


def test_jwt_create_and_decode():
    token = create_access_token(subject="user-123", extra_claims={"org": "org-1"})
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["org"] == "org-1"
    assert payload["type"] == "access"


def test_invalid_token():
    assert decode_token("not.a.valid.token") is None