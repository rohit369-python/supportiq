"""FastAPI dependencies: current user, permissions, tenant isolation."""

from typing import Annotated, Optional
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.user import User, UserRole, Role, RolePermission, Permission
from app.core.security import decode_token

security_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(self, user: User, permissions: set[str]):
        self.user = user
        self.permissions = permissions
        self.organization_id = user.organization_id
        self.user_id = user.id
        self.is_superuser = user.is_superuser

    def has_permission(self, codename: str) -> bool:
        if self.is_superuser:
            return True
        return codename in self.permissions

    def require_permission(self, codename: str) -> None:
        if not self.has_permission(codename):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {codename}",
            )


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user id")

    result = await db.execute(
        select(User)
        .options(
            selectinload(User.user_roles)
            .selectinload(UserRole.role)
            .selectinload(Role.permissions)
            .selectinload(RolePermission.permission)
        )
        .where(User.id == uid, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    permissions: set[str] = set()
    for ur in user.user_roles:
        for rp in ur.role.permissions:
            permissions.add(rp.permission.codename)

    return CurrentUser(user=user, permissions=permissions)


async def get_optional_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Optional[CurrentUser]:
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_permissions(*codenames: str):
    """Dependency factory that checks one or more permissions."""

    async def checker(current: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        for code in codenames:
            current.require_permission(code)
        return current

    return checker


# Common permission constants
class Perm:
    VIEW_TICKETS = "tickets.view"
    CREATE_TICKETS = "tickets.create"
    ASSIGN_TICKETS = "tickets.assign"
    UPDATE_TICKETS = "tickets.update"
    CLOSE_TICKETS = "tickets.close"
    VIEW_CUSTOMERS = "customers.view"
    MANAGE_CUSTOMERS = "customers.manage"
    MANAGE_AGENTS = "agents.manage"
    MANAGE_KB = "knowledge.manage"
    MANAGE_AI = "ai.manage"
    VIEW_ANALYTICS = "analytics.view"
    MANAGE_ORG = "organization.manage"
    MANAGE_USERS = "users.manage"
    VIEW_AUDIT = "audit.view"