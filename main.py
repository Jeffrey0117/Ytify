# -*- coding: utf-8 -*-
"""
ytify - YouTube Downloader API
本地 API 服務，供 Tampermonkey 腳本調用
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(
    title="ytify",
    description="YouTube Downloader API for Tampermonkey",
    version="1.0.0"
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
