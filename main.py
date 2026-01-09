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
from services.ytdlp_updater import ytdlp_updater
from services.websocket_manager import progress_notifier

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


async def check_ytdlp_update_on_startup():
    """啟動時檢查 yt-dlp 更新"""
    try:
        version = ytdlp_updater.get_current_version()
        print(f"[yt-dlp] 目前版本: {version}")

        result = await ytdlp_updater.check_update(force=True)
        if result.get("update_available"):
            print(f"[yt-dlp] ⚠️  發現新版本: {result['latest_version']}")
            print(f"[yt-dlp]    可透過 POST /api/ytdlp/update 更新")
        else:
            print(f"[yt-dlp] ✓ 已是最新版本")
    except Exception as e:
        print(f"[yt-dlp] 檢查更新失敗: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時
    cleanup_task = asyncio.create_task(cleanup_old_files())
    print("[啟動] 自動清理任務已啟動（24小時過期檔案）")

    # 啟動 WebSocket 進度通知器
    await progress_notifier.start()
    print("[啟動] WebSocket 進度推送已啟用")

    # 檢查 yt-dlp 更新
    await check_ytdlp_update_on_startup()

    yield
    # 關閉時
    cleanup_task.cancel()
    await progress_notifier.stop()
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

# 掛載靜態檔案目錄（圖片、CSS、JS 等）
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


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


@app.get("/playlist")
async def playlist_page():
    """播放清單下載頁面"""
    static_path = Path(__file__).parent / "static" / "playlist.html"
    if static_path.exists():
        return FileResponse(static_path)
    return {"error": "playlist.html not found"}


@app.get("/history")
async def history_page():
    """下載歷史頁面"""
    static_path = Path(__file__).parent / "static" / "history.html"
    if static_path.exists():
        return FileResponse(static_path)
    return {"error": "history.html not found"}


@app.get("/files")
async def files_page():
    """檔案管理頁面"""
    static_path = Path(__file__).parent / "static" / "files.html"
    if static_path.exists():
        return FileResponse(static_path)
    return {"error": "files.html not found"}


@app.get("/dashboard")
async def dashboard_page():
    """系統狀態儀表板頁面"""
    static_path = Path(__file__).parent / "static" / "dashboard.html"
    if static_path.exists():
        return FileResponse(static_path)
    return {"error": "dashboard.html not found"}


@app.get("/about")
async def about_page():
    """關於頁面"""
    static_path = Path(__file__).parent / "static" / "about.html"
    if static_path.exists():
        return FileResponse(static_path)
    return {"error": "about.html not found"}


@app.get("/health")
async def health():
    """健康檢查與版本資訊"""
    ytdlp_info = ytdlp_updater.get_version_info()
    return {
        "status": "ok",
        "version": "1.0.0",
        "ytdlp_version": ytdlp_info["current_version"],
        "ytdlp_update_available": ytdlp_info["update_available"]
    }


if __name__ == "__main__":
    print("=" * 50)
    print("  ytify - YouTube Downloader API")
    print("  http://localhost:8765")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8765)
