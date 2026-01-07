# -*- coding: utf-8 -*-
"""
ytify API 路由
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import asyncio
import urllib.parse

from services.downloader import downloader

router = APIRouter(prefix="/api", tags=["youtube"])


class InfoRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    format: str = "best"  # best | 1080p | 720p | 480p
    audio_only: bool = False


@router.post("/info")
async def get_video_info(request: InfoRequest):
    """取得影片資訊"""
    info = await downloader.get_video_info(request.url)
    if "error" in info:
        raise HTTPException(status_code=400, detail=info["error"])
    return info


@router.post("/download")
async def start_download(request: DownloadRequest):
    """開始下載影片"""
    if downloader.is_running:
        raise HTTPException(status_code=400, detail="已有下載任務進行中")

    # 建立任務
    task_id = downloader.create_task(
        url=request.url,
        format_option=request.format,
        audio_only=request.audio_only
    )

    # 背景執行下載
    asyncio.create_task(downloader.execute_task(task_id))

    return {
        "task_id": task_id,
        "status": "started",
        "message": "開始下載"
    }


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """查詢下載狀態"""
    status = downloader.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="找不到該任務")
    return status


@router.get("/status")
async def get_current_status():
    """取得當前下載狀態"""
    return downloader.get_status()


@router.get("/files")
async def list_files():
    """列出已下載檔案"""
    return downloader.list_downloads()


@router.delete("/files/{filename:path}")
async def delete_file(filename: str):
    """刪除檔案"""
    success = downloader.delete_file(filename)
    if not success:
        raise HTTPException(status_code=404, detail="檔案不存在")
    return {"success": True, "message": "檔案已刪除"}


@router.get("/history")
async def get_history():
    """取得下載歷史"""
    return downloader.get_history()


@router.delete("/history")
async def clear_history():
    """清除下載歷史"""
    downloader.clear_history()
    return {"success": True, "message": "歷史已清除"}


@router.get("/download-file/{filename:path}")
async def download_file(filename: str):
    """下載檔案到使用者電腦"""
    file_path = downloader.download_path / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="檔案不存在")

    # 安全檢查：確保路徑在 downloads 資料夾內
    try:
        file_path.resolve().relative_to(downloader.download_path.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="禁止存取")

    # 設定檔名（支援中文）
    encoded_filename = urllib.parse.quote(filename)

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )
