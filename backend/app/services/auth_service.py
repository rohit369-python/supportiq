"""Authentication service."""

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.user import User, RefreshToken, UserRole, Role
from app.models.organization import Organization
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    hash_token,
    decode_token,
)
from app.config.settings import settings
from app.schemas.auth import TokenResponse, UserOut


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, email: str, password: str, organization_id: Optional[uuid.UUID] = None) -> User:
        q = select(User).where(User.email == email.lower(), User.is_active.is_(True))
        if organization_id:
            q = q.where(User.organization_id == organization_id)
        result = await self.db.execute(q)
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()
        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.authenticate(email, password)
        access = create_access_token(
            subject=str(user.id),
            extra_claims={"org": str(user.organization_id), "email": user.email},
        )
        raw_refresh, token_hash, expires_at = create_refresh_token(str(user.id))
        rt = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(rt)
        await self.db.flush()
        return TokenResponse(
            access_token=access,
            refresh_token=raw_refresh,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def refresh(self, raw_refresh_token: str) -> TokenResponse:
        token_hash = hash_token(raw_refresh_token)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
            )
        )
        rt = result.scalar_one_or_none()
        if not rt or rt.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        result = await self.db.execute(select(User).where(User.id == rt.user_id, User.is_active.is_(True)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        # Rotate refresh token
        rt.revoked = True
        access = create_access_token(
            subject=str(user.id),
            extra_claims={"org": str(user.organization_id), "email": user.email},
        )
        new_raw, new_hash, new_exp = create_refresh_token(str(user.id))
        new_rt = RefreshToken(user_id=user.id, token_hash=new_hash, expires_at=new_exp)
        self.db.add(new_rt)
        await self.db.flush()
        return TokenResponse(
            access_token=access,
            refresh_token=new_raw,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    async def logout(self, raw_refresh_token: str) -> None:
        token_hash = hash_token(raw_refresh_token)
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        rt = result.scalar_one_or_none()
        if rt:
            rt.revoked = True
            await self.db.flush()

    async def get_user_out(self, user: User) -> UserOut:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.id == user.id)
        )
        u = result.scalar_one()
        roles = [ur.role.name for ur in u.user_roles]
        return UserOut(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            organization_id=u.organization_id,
            is_active=u.is_active,
            is_email_verified=u.is_email_verified,
            roles=roles,
            timezone=u.timezone,
            preferred_language=u.preferred_language,
        )