from collections.abc import Callable
from enum import StrEnum

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings


class UserRole(StrEnum):
    VIEWER = "VIEWER"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"


ROLE_RANK = {UserRole.VIEWER: 0, UserRole.REVIEWER: 1, UserRole.ADMIN: 2}


def current_role(
    x_user_role: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> UserRole:
    if settings.app_env.lower() != "development" or not settings.allow_dev_role_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="An authentication provider must be configured for this environment",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if x_user_role is None:
        return UserRole.VIEWER
    try:
        return UserRole(x_user_role.upper())
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Unknown development role") from exc


def require_role(minimum_role: UserRole) -> Callable[..., UserRole]:
    def dependency(role: UserRole = Depends(current_role)) -> UserRole:
        if ROLE_RANK[role] < ROLE_RANK[minimum_role]:
            raise HTTPException(status_code=403, detail="Insufficient role for this action")
        return role

    return dependency
