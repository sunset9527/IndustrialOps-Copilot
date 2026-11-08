"""Database-backed account creation and authentication services."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from industrialops.models.user import User
from industrialops.services.password_policy import PasswordPolicyError, validate_password

try:
    from passlib.context import CryptContext
except ImportError as error:  # pragma: no cover - covered by installation validation later
    raise RuntimeError("passlib is required for password hashing") from error


_PASSWORD_CONTEXT = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")
_INVALID_CREDENTIALS = "Invalid username or password"


def hash_password(password: str) -> str:
    """Hash a password before it reaches persistence."""

    return _PASSWORD_CONTEXT.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its stored hash."""

    return _PASSWORD_CONTEXT.verify(password, password_hash)


def create_user(db: Session, username: str, email: str, password: str) -> tuple[User | None, str | None]:
    """Create a regular user after policy and uniqueness checks."""

    try:
        validate_password(password, username=username, email=email, is_admin=False)
    except PasswordPolicyError as error:
        return None, str(error)

    if _get_user_by_username(db, username):
        return None, "Username is already registered"
    if db.scalar(select(User).where(User.email == email)):
        return None, "Email is already registered"

    user = User(username=username, email=email, password_hash=hash_password(password), role="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, None


def authenticate_user(db: Session, username: str, password: str) -> tuple[User | None, str | None]:
    """Authenticate without revealing whether a username exists."""

    user = _get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        return None, _INVALID_CREDENTIALS
    return user, None


def _get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))
