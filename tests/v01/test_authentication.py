from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from industrialops.database import Base
from industrialops.models.user import User
from industrialops.services.auth import authenticate_user, create_user


def _session():
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_create_user_hashes_the_password_and_authenticates_the_account() -> None:
    db = _session()

    user, error = create_user(db, "operator", "operator@example.com", "long memorable password")
    authenticated, authentication_error = authenticate_user(db, "operator", "long memorable password")

    assert error is None
    assert user is not None
    assert user.password_hash != "long memorable password"
    assert authenticated is not None
    assert authenticated.id == user.id
    assert authentication_error is None


def test_authentication_uses_the_same_error_for_missing_user_and_wrong_password() -> None:
    db = _session()
    created, error = create_user(db, "operator", "operator@example.com", "long memorable password")

    assert created is not None
    assert error is None

    missing_user, missing_error = authenticate_user(db, "missing", "wrong-password")
    wrong_password_user, wrong_password_error = authenticate_user(db, "operator", "wrong-password")

    assert missing_user is None
    assert wrong_password_user is None
    assert missing_error == wrong_password_error == "Invalid username or password"


def test_create_user_rejects_duplicate_username_without_persisting_a_second_row() -> None:
    db = _session()
    first, first_error = create_user(db, "operator", "operator@example.com", "long memorable password")
    duplicate, duplicate_error = create_user(db, "operator", "second@example.com", "another long password")

    assert first is not None
    assert first_error is None
    assert duplicate is None
    assert duplicate_error == "Username is already registered"
    assert db.query(User).count() == 1
