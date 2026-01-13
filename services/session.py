# -*- coding: utf-8 -*-
"""
Session 管理服務
為訪客生成唯一識別碼，支援多租戶隔離
"""

import uuid
from typing import Optional, Tuple
from fastapi import Request, Response

# Cookie 設定
SESSION_COOKIE_NAME = "ytify_session"
SESSION_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 天


def get_client_ip(request: Request) -> str:
    """
    取得客戶端真實 IP

    優先順序：
    1. CF-Connecting-IP (Cloudflare)
    2. X-Real-IP (Nginx)
    3. X-Forwarded-For (Proxy)
    4. request.client.host (直連)
    """
    # Cloudflare
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip

    # Nginx proxy
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 標準 proxy header
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # 取第一個 IP（最原始的客戶端）
        return forwarded.split(",")[0].strip()

    # 直連
    if request.client:
        return request.client.host

    return "unknown"


def get_session_id(request: Request) -> Optional[str]:
    """從 Cookie 取得 session_id"""
    return request.cookies.get(SESSION_COOKIE_NAME)


def create_session_id() -> str:
    """生成新的 session_id"""
    return str(uuid.uuid4())


def set_session_cookie(response: Response, session_id: str):
    """設定 session cookie"""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        max_age=SESSION_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax"
    )


def get_client_identity(request: Request) -> Tuple[str, Optional[str]]:
    """
    取得客戶端識別資訊

    Returns:
        (client_ip, session_id)
    """
    client_ip = get_client_ip(request)
    session_id = get_session_id(request)
    return client_ip, session_id


class SessionMiddleware:
    """
    Session Middleware
    自動為沒有 session 的訪客生成 session_id
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 檢查是否需要設定 session
        request = Request(scope, receive)
        session_id = get_session_id(request)
        new_session = False

        if not session_id:
            session_id = create_session_id()
            new_session = True

        # 將 session_id 存入 scope.state 供後續使用
        scope["state"] = scope.get("state", {})
        scope["state"]["session_id"] = session_id
        scope["state"]["client_ip"] = get_client_ip(request)
        scope["state"]["new_session"] = new_session

        # 如果是新 session，需要在 response 設定 cookie
        if new_session:
            async def send_with_cookie(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    cookie_value = f"{SESSION_COOKIE_NAME}={session_id}; Path=/; Max-Age={SESSION_COOKIE_MAX_AGE}; HttpOnly; SameSite=Lax"
                    headers.append((b"set-cookie", cookie_value.encode()))
                    message["headers"] = headers
                await send(message)
            await self.app(scope, receive, send_with_cookie)
        else:
            await self.app(scope, receive, send)
