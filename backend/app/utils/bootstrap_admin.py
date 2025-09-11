"""CLI utility to bootstrap or update platform users."""

from __future__ import annotations

import argparse

from sqlalchemy import select

from backend.app.core.security import get_password_hash
from backend.app.db.session import SessionLocal
from backend.app.models.user import User, UserRole


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for user bootstrap."""
    parser = argparse.ArgumentParser(description="Bootstrap or update a platform user.")
    parser.add_argument("--username", required=True, help="Username to create or update.")
    parser.add_argument("--password", required=True, help="Plain text password.")
    parser.add_argument(
        "--role",
        default="admin",
        choices=[role.value for role in UserRole],
        help="RBAC role for this user.",
    )
    return parser.parse_args()


def upsert_user(username: str, password: str, role: UserRole) -> str:
    """Create user if missing; otherwise rotate credentials and role."""
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.username == username))
        if existing:
            existing.hashed_password = get_password_hash(password)
            existing.role = role
            db.commit()
            return "updated"

        db.add(
            User(
                username=username,
                hashed_password=get_password_hash(password),
                role=role,
            )
        )
        db.commit()
        return "created"


def main() -> None:
    """Entrypoint for CLI execution."""
    args = parse_args()
    action = upsert_user(args.username, args.password, UserRole(args.role))
    print(f"User '{args.username}' {action} with role '{args.role}'.")


if __name__ == "__main__":
    main()
