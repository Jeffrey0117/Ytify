# -*- coding: utf-8 -*-
"""
認證相關 API 路由
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List

from services.auth import auth_db, User, UserRole, ROLE_QUOTAS
from services.auth_middleware import (
    require_auth, require_admin, get_current_user,
    AuthConfig
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ===== 請求模型 =====

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "user"


class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    daily_quota: Optional[int] = None
    monthly_quota: Optional[int] = None
    is_active: Optional[bool] = None


class CreateTokenRequest(BaseModel):
    name: str
    permissions: str = "read,download"
    expires_days: Optional[int] = None


# ===== 認證端點 =====

@router.get("/status")
async def get_auth_status():
    """取得認證系統狀態"""
    return {
        "enabled": AuthConfig.ENABLED,
        "allow_anonymous": AuthConfig.ALLOW_ANONYMOUS,
        "anonymous_daily_quota": AuthConfig.ANONYMOUS_DAILY_QUOTA,
        "anonymous_monthly_quota": AuthConfig.ANONYMOUS_MONTHLY_QUOTA
    }


@router.post("/login")
async def login(req: LoginRequest):
    """用戶登入"""
    user = auth_db.authenticate(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")

    # 取得配額資訊
    quota = auth_db.check_quota(user.id)

    return {
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
        },
        "api_token": user.api_token,
        "quota": quota,
        "message": "登入成功"
    }


@router.post("/register")
async def register(req: RegisterRequest):
    """用戶註冊（如果允許）"""
    # 可透過設定控制是否允許公開註冊
    allow_register = True  # TODO: 從設定讀取

    if not allow_register:
        raise HTTPException(status_code=403, detail="目前不開放註冊")

    result = auth_db.create_user(req.username, req.password, req.email)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/me")
async def get_current_user_info(user: User = Depends(require_auth)):
    """取得當前用戶資訊"""
    quota = auth_db.check_quota(user.id)
    stats = auth_db.get_user_stats(user.id)

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "created_at": user.created_at,
            "last_login": user.last_login,
        },
        "quota": quota,
        "stats": stats
    }


@router.post("/change-password")
async def change_password(req: ChangePasswordRequest, user: User = Depends(require_auth)):
    """變更密碼"""
    success = auth_db.change_password(user.id, req.old_password, req.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="原密碼錯誤")
    return {"success": True, "message": "密碼已變更"}


@router.post("/regenerate-token")
async def regenerate_token(user: User = Depends(require_auth)):
    """重新生成 API Token"""
    new_token = auth_db.regenerate_token(user.id)
    return {
        "success": True,
        "api_token": new_token,
        "message": "Token 已重新生成，舊 Token 已失效"
    }


# ===== API Token 管理 =====

@router.get("/tokens")
async def list_tokens(user: User = Depends(require_auth)):
    """列出用戶的 API Tokens"""
    tokens = auth_db.list_api_tokens(user.id)
    return {
        "tokens": tokens,
        "primary_token": f"{user.api_token[:8]}...{user.api_token[-4:]}"
    }


@router.post("/tokens")
async def create_token(req: CreateTokenRequest, user: User = Depends(require_auth)):
    """建立新的 API Token"""
    result = auth_db.create_api_token(
        user.id,
        req.name,
        req.permissions,
        req.expires_days
    )
    return {
        "success": True,
        "token": result["token"],
        "name": result["name"],
        "expires_at": result["expires_at"],
        "message": "請保存此 Token，它只會顯示一次"
    }


@router.delete("/tokens/{token_id}")
async def revoke_token(token_id: int, user: User = Depends(require_auth)):
    """撤銷 API Token"""
    success = auth_db.revoke_api_token(token_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Token 不存在或無權限")
    return {"success": True, "message": "Token 已撤銷"}


# ===== 配額查詢 =====

@router.get("/quota")
async def get_quota(user: User = Depends(require_auth)):
    """查詢配額"""
    return auth_db.check_quota(user.id)


# ===== 管理員功能 =====

@router.get("/admin/users")
async def admin_list_users(
    limit: int = 50,
    offset: int = 0,
    admin: User = Depends(require_admin)
):
    """列出所有用戶（管理員）"""
    users = auth_db.list_users(limit, offset)
    return {
        "users": users,
        "total": len(users),  # TODO: 實作總數查詢
        "limit": limit,
        "offset": offset
    }


@router.post("/admin/users")
async def admin_create_user(req: CreateUserRequest, admin: User = Depends(require_admin)):
    """建立用戶（管理員）"""
    try:
        role = UserRole(req.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"無效的角色: {req.role}")

    result = auth_db.create_user(req.username, req.password, req.email, role)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/admin/users/{user_id}")
async def admin_get_user(user_id: int, admin: User = Depends(require_admin)):
    """取得用戶詳情（管理員）"""
    user = auth_db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")

    quota = auth_db.check_quota(user_id)
    stats = auth_db.get_user_stats(user_id)

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "daily_quota": user.daily_quota,
            "monthly_quota": user.monthly_quota,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "last_login": user.last_login,
        },
        "quota": quota,
        "stats": stats
    }


@router.put("/admin/users/{user_id}")
async def admin_update_user(
    user_id: int,
    req: UpdateUserRequest,
    admin: User = Depends(require_admin)
):
    """更新用戶（管理員）"""
    updates = req.dict(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="沒有要更新的欄位")

    success = auth_db.update_user(user_id, **updates)
    if not success:
        raise HTTPException(status_code=400, detail="更新失敗")

    return {"success": True, "message": "用戶已更新"}


@router.delete("/admin/users/{user_id}")
async def admin_disable_user(user_id: int, admin: User = Depends(require_admin)):
    """停用用戶（管理員）"""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能停用自己")

    success = auth_db.update_user(user_id, is_active=False)
    if not success:
        raise HTTPException(status_code=400, detail="停用失敗")

    return {"success": True, "message": "用戶已停用"}


@router.get("/admin/roles")
async def get_roles(admin: User = Depends(require_admin)):
    """取得角色列表和預設配額"""
    return {
        "roles": [
            {
                "name": role.value,
                "daily_quota": quotas["daily"],
                "monthly_quota": quotas["monthly"]
            }
            for role, quotas in ROLE_QUOTAS.items()
        ]
    }
