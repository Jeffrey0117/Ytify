# -*- coding: utf-8 -*-
"""
ytify API 路由
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import asyncio
import urllib.parse
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.downloader import downloader, is_valid_youtube_url
from services.queue import download_queue

router = APIRouter(prefix="/api", tags=["youtube"])

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)


class InfoRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    format: str = "best"  # best | 1080p | 720p | 480p
    audio_only: bool = False


@router.post("/info")
@limiter.limit("30/minute")
async def get_video_info(request: Request, req: InfoRequest):
    """取得影片資訊"""
    # URL 驗證
    if not is_valid_youtube_url(req.url):
        raise HTTPException(status_code=400, detail="無效的 YouTube URL")

    info = await downloader.get_video_info(req.url)
    if "error" in info:
        raise HTTPException(status_code=400, detail=info["error"])
    return info


@router.post("/download")
@limiter.limit("10/minute")
async def start_download(request: Request, req: DownloadRequest):
    """開始下載影片（加入佇列）"""
    # URL 驗證
    if not is_valid_youtube_url(req.url):
        raise HTTPException(status_code=400, detail="無效的 YouTube URL")

    # 建立任務
    task_id = downloader.create_task(
        url=req.url,
        format_option=req.format,
        audio_only=req.audio_only
    )

    # 取得當前佇列狀態
    stats = download_queue.get_stats()
    queue_position = stats["queued"] + 1 if stats["running"] >= stats["max_concurrent"] else 0

    # 提交到佇列執行
    await download_queue.submit(task_id, downloader.execute_task, task_id)

    return {
        "task_id": task_id,
        "status": "queued" if queue_position > 0 else "started",
        "queue_position": queue_position,
        "message": f"排隊中（第 {queue_position} 位）" if queue_position > 0 else "開始下載"
    }


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """查詢下載狀態"""
    # 先檢查佇列狀態
    queue_info = download_queue.get_queue_info(task_id)
    if queue_info and queue_info.get("status") == "queued":
        return {
            "status": "queued",
            "queue_position": queue_info.get("queue_position", 0),
            "message": f"排隊中（第 {queue_info.get('queue_position', 0)} 位）"
        }

    # 查詢下載狀態
    status = downloader.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="找不到該任務")
    return status


@router.get("/queue-stats")
async def get_queue_stats():
    """取得佇列狀態"""
    return download_queue.get_stats()


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


class ProxyConfig(BaseModel):
    proxy: Optional[str] = None  # 單一代理: "http://ip:port"
    proxy_pool_api: Optional[str] = None  # 代理池 API: "http://localhost:5010/get"


@router.get("/proxy")
async def get_proxy_config():
    """取得代理設定與統計"""
    return downloader.get_proxy_stats()


@router.post("/proxy")
async def set_proxy_config(config: ProxyConfig):
    """設定代理"""
    downloader.proxy = config.proxy
    downloader.proxy_pool_api = config.proxy_pool_api
    return {
        "success": True,
        "message": "代理設定已更新",
        "proxy": downloader.proxy,
        "proxy_pool_api": downloader.proxy_pool_api
    }


@router.get("/proxy/bad")
async def get_bad_proxies():
    """取得壞代理清單"""
    return {
        "count": len(downloader.bad_proxies),
        "proxies": downloader.get_bad_proxies()
    }


@router.delete("/proxy/bad")
async def clear_bad_proxies():
    """清除壞代理黑名單"""
    count = downloader.clear_bad_proxies()
    return {
        "success": True,
        "message": f"已清除 {count} 個壞代理"
    }


@router.post("/proxy/bad/{proxy}")
async def mark_proxy_bad(proxy: str):
    """手動標記代理為壞代理"""
    downloader.mark_proxy_bad(proxy)
    return {
        "success": True,
        "message": f"已標記 {proxy} 為壞代理"
    }


@router.get("/download-file/{filename:path}")
async def download_file(filename: str, auto_delete: bool = True):
    """
    下載檔案到使用者電腦

    Args:
        filename: 檔案名稱
        auto_delete: 下載後自動刪除 Server 上的檔案（預設 True）
    """
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

    # 使用 background task 在回應完成後刪除檔案
    from fastapi import BackgroundTasks
    from starlette.background import BackgroundTask

    def delete_file_after_download():
        if auto_delete and file_path.exists():
            try:
                file_path.unlink()
                print(f"[清理] 已刪除: {filename}")
            except Exception as e:
                print(f"[清理] 刪除失敗: {filename} - {e}")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        },
        background=BackgroundTask(delete_file_after_download)
    )
