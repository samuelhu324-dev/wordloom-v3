"""
Security utilities - JWT, password hashing, authentication

Provides:
- JWT token creation and verification
- Password hashing utilities
- Current user dependency injection
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4
import jwt
from .setting import get_settings

from api.app.shared.actor import Actor
from api.app.shared.request_context import with_actor_id


class SecurityConfig:
    """Centralized security configuration"""

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token

        Args:
            data: Claims to encode in token
            expires_delta: Optional custom expiration time

        Returns:
            str: Encoded JWT token
        """
        settings = get_settings()
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify JWT token validity

        Args:
            token: JWT token string

        Returns:
            dict: Decoded payload if valid, None if invalid
        """
        settings = get_settings()
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
            return payload
        except jwt.InvalidTokenError:
            return None


async def get_current_user_id() -> UUID:
    """开发环境当前用户 ID 依赖。

    之前写死为固定 UUID 导致：数据库里已有的库都是另外的 user_id → /libraries 按用户过滤结果为空。

    改进：
    1. 支持通过环境变量 DEV_USER_ID 覆盖。
       在 WSL2 或 Windows 设置后端进程环境：
         Linux/WSL2: `export DEV_USER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
         Windows PowerShell: `$env:DEV_USER_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"`
    2. 若未设置则回退到原始固定测试 UUID。
    3. 保留后续 TODO（JWT 解析）。
    """
    import os
    override = os.getenv("DEV_USER_ID")
    if override:
        try:
            return UUID(override)
        except Exception:
            # 环境变量格式不合法时仍使用默认测试 ID，避免启动失败
            pass
    return UUID("550e8400-e29b-41d4-a716-446655440000")


async def get_current_actor() -> Actor:
    """当前请求的 Actor（认证后的身份载体）。

    目前仍处于开发模式：只提供 user_id。
    后续接入 JWT 后，这里会解析 token 并填充 workspace_id/roles 等。
    """

    user_id = await get_current_user_id()
    with_actor_id(user_id)
    return Actor(user_id=user_id)
