# -*- coding: utf-8 -*-
"""
認證中介軟體
"""

from typing import Optional, Callable
from functools import wraps
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader

from services.auth import auth_db, User, UserRole


# API Key Header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Bearer Token
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[User]:
    """
    取得當前用戶

    支援多種認證方式：
    1. X-API-Key Header
    2. Authorization: Bearer <token>
    3. Query parameter: ?token=xxx
    """
    token = None

    # 優先使用 X-API-Key
    if api_key:
        token = api_key

    # 其次使用 Bearer Token
    elif bearer:
        token = bearer.credentials

    # 最後檢查 Query Parameter
    else:
        token = request.query_params.get("token")

    if not token:
        return None

    return auth_db.get_user_by_token(token)


async def require_auth(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    要求認證（任何有效用戶）
    """
    if not user:
        raise HTTPException(
            status_code=401,
            detail="需要認證",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


async def require_admin(
    user: User = Depends(require_auth)
) -> User:
    """
    要求管理員權限
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="需要管理員權限"
        )
    return user


async def require_vip_or_admin(
    user: User = Depends(require_auth)
) -> User:
    """
    要求 VIP 或管理員權限
    """
    if user.role not in [UserRole.ADMIN, UserRole.VIP]:
        raise HTTPException(
            status_code=403,
            detail="需要 VIP 或管理員權限"
        )
    return user


async def check_quota(
    user: User = Depends(require_auth)
) -> User:
    """
    檢查下載配額
    """
    quota = auth_db.check_quota(user.id)
    if not quota["allowed"]:
        daily = quota.get("daily", {})
        monthly = quota.get("monthly", {})

        if daily.get("remaining", 0) <= 0:
            raise HTTPException(
                status_code=429,
                detail=f"已達每日下載上限 ({daily.get('quota', 0)} 次)"
            )
        if monthly.get("remaining", 0) <= 0:
            raise HTTPException(
                status_code=429,
                detail=f"已達每月下載上限 ({monthly.get('quota', 0)} 次)"
            )

    return user


def optional_auth(func: Callable):
    """
    可選認證裝飾器

    用於支援匿名訪問但有認證時提供更多功能的端點
    """
    @wraps(func)
    async def wrapper(*args, request: Request, **kwargs):
        user = await get_current_user(
            request,
            api_key=request.headers.get("X-API-Key"),
            bearer=None
        )
        kwargs["current_user"] = user
        return await func(*args, request=request, **kwargs)
    return wrapper


class AuthConfig:
    """
    認證設定

    可透過環境變數或設定檔調整
    """
    # 是否啟用認證（False = 開放模式）
    ENABLED: bool = False

    # 是否允許匿名下載
    ALLOW_ANONYMOUS: bool = True

    # 匿名用戶配額
    ANONYMOUS_DAILY_QUOTA: int = 10
    ANONYMOUS_MONTHLY_QUOTA: int = 100

    # Session 過期時間（秒）
    SESSION_EXPIRE: int = 86400  # 24 小時

    @classmethod
    def load_from_env(cls):
        """從環境變數載入設定"""
        import os
        cls.ENABLED = os.environ.get("YTIFY_AUTH_ENABLED", "false").lower() == "true"
        cls.ALLOW_ANONYMOUS = os.environ.get("YTIFY_ALLOW_ANONYMOUS", "true").lower() == "true"
        cls.ANONYMOUS_DAILY_QUOTA = int(os.environ.get("YTIFY_ANON_DAILY_QUOTA", "10"))
        cls.ANONYMOUS_MONTHLY_QUOTA = int(os.environ.get("YTIFY_ANON_MONTHLY_QUOTA", "100"))


# 載入設定
AuthConfig.load_from_env()


async def get_user_or_anonymous(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[User]:
    """
    取得用戶或允許匿名

    當認證未啟用或允許匿名時，返回 None 代表匿名用戶
    """
    if not AuthConfig.ENABLED:
        return None

    user = await get_current_user(request, api_key, bearer)

    if not user and not AuthConfig.ALLOW_ANONYMOUS:
        raise HTTPException(
            status_code=401,
            detail="需要認證",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user
