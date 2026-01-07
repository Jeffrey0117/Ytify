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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from services.downloader import downloader


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

# CORS 設定 - 允許 YouTube 網頁調用
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.youtube.com",
        "https://youtube.com",
        "https://m.youtube.com",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
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


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    print("=" * 50)
    print("  ytify - YouTube Downloader API")
    print("  http://localhost:8765")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8765)
