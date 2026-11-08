from __future__ import annotations

import pytest

from industrialops.services.authorization import AuthorizationError, require_role


def test_require_role_allows_an_authorized_role() -> None:
    require_role("admin", allowed_roles={"admin"})


def test_require_role_rejects_an_unauthorized_role_with_a_stable_code() -> None:
    with pytest.raises(AuthorizationError) as raised:
        require_role("user", allowed_roles={"admin"})

    assert raised.value.code == "forbidden"
