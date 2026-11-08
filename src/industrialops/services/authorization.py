"""Small role checks shared by future API dependencies and services."""

from __future__ import annotations

from collections.abc import Set


class AuthorizationError(PermissionError):
    """Stable authorization failure that callers can map to a 403 response."""

    code = "forbidden"


def require_role(role: str, *, allowed_roles: Set[str]) -> None:
    """Raise when a role is not allowed to perform an operation."""

    if role not in allowed_roles:
        raise AuthorizationError("The current role is not authorized for this operation")
