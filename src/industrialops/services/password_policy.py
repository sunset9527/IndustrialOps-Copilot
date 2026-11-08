"""Password checks for newly created or changed accounts."""

from __future__ import annotations

import re


_WEAK_PASSWORDS = frozenset(
    {
        "1234567890",
        "123456789",
        "12345678",
        "password",
        "password123",
        "qwerty123",
        "qwertyuiop",
        "letmein",
        "admin123",
    }
)
_IDENTITY_RE = re.compile(r"[^a-z0-9]+")


class PasswordPolicyError(ValueError):
    """A stable error that does not retain the rejected password."""

    def __init__(self, code: str, public_message: str):
        super().__init__(public_message)
        self.code = code


def validate_password(password: str, *, username: str, email: str, is_admin: bool) -> None:
    """Validate password strength without logging its value."""

    if not password.strip():
        raise PasswordPolicyError("password_blank", "Password cannot contain only whitespace")
    if len(password) > 128:
        raise PasswordPolicyError("password_too_long", "Password cannot exceed 128 characters")

    minimum = 12 if is_admin else 10
    if len(password) < minimum:
        raise PasswordPolicyError("password_too_short", f"Password must contain at least {minimum} characters")
    if password.casefold() in _WEAK_PASSWORDS:
        raise PasswordPolicyError("password_too_weak", "Password is too common")

    candidate = _identity_token(password)
    identities = (_identity_token(username), _identity_token(email.split("@", 1)[0]))
    if any(len(identity) >= 3 and (candidate == identity or candidate.startswith(identity)) for identity in identities):
        raise PasswordPolicyError("password_too_similar", "Password is too similar to the account identity")


def _identity_token(value: str) -> str:
    return _IDENTITY_RE.sub("", value.casefold())
