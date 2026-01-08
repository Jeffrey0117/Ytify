# -*- coding: utf-8 -*-
"""
ytify - YouTube Downloader API
本地 API 服務，供 Tampermonkey 腳本調用
"""

import uvicorn
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.routes import router
from services.downloader import downloader
from services.queue import download_queue

# Rate Limiter 初始化
limiter = Limiter(key_func=get_remote_address)


# 自動清理設定
AUTO_CLEANUP_INTERVAL = 3600  # 每小時檢查一次
FILE_MAX_AGE_HOURS = 24       # 檔案保留 24 小時


async def cleanup_old_files():
    """定時清理超過 24 小時的舊檔案"""
    while True:
        await asyncio.sleep(AUTO_CLEANUP_INTERVAL)
        try:
            now = datetime.now()
            count = 0
            for file in downloader.download_path.iterdir():
                if file.is_file() and file.suffix != '.gitkeep':
                    file_age = now - datetime.fromtimestamp(file.stat().st_mtime)
                    if file_age > timedelta(hours=FILE_MAX_AGE_HOURS):
                        file.unlink()
                        count += 1
                        print(f"[自動清理] 刪除過期檔案: {file.name}")
            if count > 0:
                print(f"[自動清理] 共清理 {count} 個過期檔案")
        except Exception as e:
            print(f"[自動清理] 錯誤: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時
    cleanup_task = asyncio.create_task(cleanup_old_files())
    print("[啟動] 自動清理任務已啟動（24小時過期檔案）")
    yield
    # 關閉時
    cleanup_task.cancel()
    print("[關閉] 清理任務已停止")

app = FastAPI(
    title="ytify",
    description="YouTube Downloader API for Tampermonkey",
    version="1.0.0",
    lifespan=lifespan
)

# Rate Limiter 設定
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Rate Limit 超過時的錯誤處理"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "請求過於頻繁",
            "detail": "請稍後再試",
            "retry_after": 60
        }
    )


# CORS 設定 - 允許所有來源（Tampermonkey GM_xmlhttpRequest 需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # 使用 * 時不能設 True
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "ytify",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/home")
async def home():
    """官網首頁"""
    static_path = Path(__file__).parent / "static" / "index.html"
    if static_path.exists():
        return FileResponse(static_path)
    return {"error": "index.html not found"}


@app.get("/download")
async def download_page():
    """網頁版下載頁面"""
    static_path = Path(__file__).parent / "static" / "download.html"
    if static_path.exists():
        return FileResponse(static_path)
    return {"error": "download.html not found"}


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    print("=" * 50)
    print("  ytify - YouTube Downloader API")
    print("  http://localhost:8765")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8765)
