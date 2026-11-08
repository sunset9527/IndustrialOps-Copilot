from __future__ import annotations

import pytest

from industrialops.services.password_policy import PasswordPolicyError, validate_password


def test_regular_user_password_accepts_a_long_memorable_phrase() -> None:
    validate_password(
        "two words are allowed",
        username="operator",
        email="operator@example.com",
        is_admin=False,
    )


@pytest.mark.parametrize(
    ("password", "username", "email", "is_admin", "code"),
    [
        ("123456789", "operator", "operator@example.com", False, "password_too_short"),
        ("12345678901", "admin", "admin@example.com", True, "password_too_short"),
        ("password123", "operator", "operator@example.com", False, "password_too_weak"),
        ("Operator-2026", "operator", "operator@example.com", False, "password_too_similar"),
        (" " * 10, "operator", "operator@example.com", False, "password_blank"),
    ],
)
def test_password_policy_rejects_unsafe_passwords_without_echoing_them(
    password: str,
    username: str,
    email: str,
    is_admin: bool,
    code: str,
) -> None:
    with pytest.raises(PasswordPolicyError) as raised:
        validate_password(password, username=username, email=email, is_admin=is_admin)

    assert raised.value.code == code
    assert password not in str(raised.value)
