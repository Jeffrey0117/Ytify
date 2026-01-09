# -*- coding: utf-8 -*-
"""
ytify API 路由
"""

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import asyncio
import urllib.parse
import subprocess
import sys
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.downloader import downloader, is_valid_youtube_url, is_playlist_url
from services.queue import download_queue
from services.ytdlp_updater import ytdlp_updater
from services.websocket_manager import ws_manager, progress_notifier

router = APIRouter(prefix="/api", tags=["youtube"])

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)


class InfoRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    format: str = "best"  # best | 1080p | 720p | 480p
    audio_only: bool = False


class PlaylistDownloadRequest(BaseModel):
    url: str
    format: str = "720p"  # 播放清單預設 720p
    audio_only: bool = False
    max_videos: int = 50  # 最多下載幾部


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

    # DEBUG: 驗證任務確實存在
    verify = downloader.get_task_status(task_id)
    print(f"[DEBUG routes] create_task 後驗證: task_id={task_id}, exists={verify is not None}, downloader_id={id(downloader)}")

    # 取得當前佇列狀態
    stats = download_queue.get_stats()
    queue_position = stats["queued"] + 1 if stats["running"] >= stats["max_concurrent"] else 0

    # 提交到佇列執行
    print(f"[DEBUG routes] 準備 submit: task_id={task_id}, downloader_id={id(downloader)}")
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
    """取得佇列狀態（含詳細診斷資訊）"""
    stats = download_queue.get_stats()
    # 加入下載器的狀態以交叉比對
    downloader_status = downloader.get_status()
    stats["downloader_running_count"] = downloader_status.get("running_count", 0)
    stats["downloader_running_tasks"] = list(downloader.running_tasks)
    return stats


@router.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    """
    取消下載任務

    Args:
        task_id: 任務 ID

    Returns:
        取消結果
    """
    result = downloader.cancel_task(task_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


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
async def get_history(limit: int = 100, status: Optional[str] = None):
    """
    取得下載歷史

    Args:
        limit: 最大筆數（預設 100）
        status: 篩選狀態（completed, failed, pending）
    """
    return downloader.get_history(limit=limit, status=status)


@router.get("/history/stats")
async def get_history_stats():
    """取得歷史統計（總數、成功率、總容量等）"""
    return downloader.get_history_stats()


@router.delete("/history")
async def clear_history(before_days: Optional[int] = None):
    """
    清除下載歷史

    Args:
        before_days: 只清除 N 天前的記錄（不傳則全部清除）
    """
    count = downloader.clear_history(before_days=before_days)
    return {
        "success": True,
        "deleted_count": count,
        "message": f"已清除 {count} 筆歷史記錄"
    }


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


# ===== 播放清單下載 =====

@router.post("/playlist/info")
@limiter.limit("20/minute")
async def get_playlist_info(request: Request, req: InfoRequest):
    """
    取得播放清單資訊

    Returns:
        播放清單標題、影片數量、影片列表等
    """
    if not is_playlist_url(req.url):
        raise HTTPException(status_code=400, detail="無效的播放清單 URL")

    info = await downloader.get_playlist_info(req.url)
    if "error" in info:
        raise HTTPException(status_code=400, detail=info["error"])
    return info


@router.post("/playlist/download")
@limiter.limit("5/minute")
async def start_playlist_download(request: Request, req: PlaylistDownloadRequest):
    """
    開始下載播放清單

    會先取得播放清單資訊，然後批次建立下載任務
    """
    if not is_playlist_url(req.url):
        raise HTTPException(status_code=400, detail="無效的播放清單 URL")

    # 取得播放清單資訊
    info = await downloader.get_playlist_info(req.url)
    if "error" in info:
        raise HTTPException(status_code=400, detail=info["error"])

    videos = info.get("videos", [])
    if not videos:
        raise HTTPException(status_code=400, detail="播放清單沒有可下載的影片")

    # 建立批次任務
    result = downloader.create_playlist_tasks(
        videos=videos,
        format_option=req.format,
        audio_only=req.audio_only,
        max_videos=req.max_videos,
        playlist_id=info.get("playlist_id")
    )

    # 提交所有任務到佇列
    for task_id in result["task_ids"]:
        await download_queue.submit(task_id, downloader.execute_task, task_id)

    return {
        "playlist_id": result["playlist_id"],
        "playlist_title": info.get("title", "未知播放清單"),
        "total_videos": info.get("video_count", 0),
        "queued_count": result["created_count"],
        "task_ids": result["task_ids"],
        "skipped": result.get("skipped", []),
        "message": f"已加入 {result['created_count']} 部影片到下載佇列"
    }


@router.get("/playlist/status/{playlist_id}")
async def get_playlist_status(playlist_id: str):
    """
    取得播放清單下載狀態

    透過播放清單 ID 查詢所有相關任務的狀態
    """
    # 從下載器取得該播放清單的所有任務
    tasks = downloader.get_playlist_tasks(playlist_id)
    if not tasks:
        raise HTTPException(status_code=404, detail="找不到該播放清單的下載任務")

    # 統計各狀態數量
    status_count = {
        "completed": 0,
        "downloading": 0,
        "queued": 0,
        "failed": 0,
        "cancelled": 0
    }

    task_details = []
    for task_id in tasks:
        status = downloader.get_task_status(task_id)
        if status:
            s = status.get("status", "unknown")
            if s in status_count:
                status_count[s] += 1
            task_details.append({
                "task_id": task_id,
                "title": status.get("title", "未知"),
                "status": s,
                "progress": status.get("progress", 0)
            })

    total = len(tasks)
    return {
        "playlist_id": playlist_id,
        "total_tasks": total,
        "completed": status_count["completed"],
        "downloading": status_count["downloading"],
        "queued": status_count["queued"],
        "failed": status_count["failed"],
        "cancelled": status_count["cancelled"],
        "progress": round(status_count["completed"] / total * 100, 1) if total > 0 else 0,
        "tasks": task_details
    }


# ===== WebSocket 進度推送 =====

@router.websocket("/ws/progress/{task_id}")
async def websocket_task_progress(websocket: WebSocket, task_id: str):
    """
    WebSocket 端點 - 訂閱特定任務的進度更新

    連線後會即時推送該任務的進度變化
    """
    await ws_manager.connect(websocket, task_id)

    try:
        # 先發送當前狀態
        current_status = downloader.get_task_status(task_id)
        if current_status:
            await ws_manager.send_personal(websocket, {
                "task_id": task_id,
                "status": current_status.get("status", "unknown"),
                "progress": current_status.get("progress", 0),
                "speed": current_status.get("speed"),
                "eta": current_status.get("eta"),
                "message": "已連線",
                "type": "initial"
            })

        # 保持連線，等待客戶端斷開
        while True:
            try:
                # 接收客戶端訊息（主要用於保持連線和 ping/pong）
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # 超時發送 ping
                try:
                    await websocket.send_text("ping")
                except:
                    break

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, task_id)


@router.websocket("/ws/all")
async def websocket_all_progress(websocket: WebSocket):
    """
    WebSocket 端點 - 訂閱所有任務的進度更新

    適用於儀表板等需要監控所有下載的場景
    """
    await ws_manager.connect(websocket, task_id=None)

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                try:
                    await websocket.send_text("ping")
                except:
                    break

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket, task_id=None)


@router.get("/ws/stats")
async def get_ws_stats():
    """取得 WebSocket 連線統計"""
    return {
        "total_connections": ws_manager.get_connection_count(),
        "global_subscribers": len(ws_manager.global_subscribers),
        "task_subscriptions": {
            task_id: len(conns)
            for task_id, conns in ws_manager.active_connections.items()
        }
    }


# ===== yt-dlp 版本管理 =====

@router.get("/ytdlp/version")
async def get_ytdlp_version():
    """取得 yt-dlp 版本資訊"""
    return ytdlp_updater.get_version_info()


@router.get("/ytdlp/check-update")
async def check_ytdlp_update():
    """檢查 yt-dlp 是否有新版本"""
    return await ytdlp_updater.check_update()


@router.post("/ytdlp/update")
@limiter.limit("2/hour")
async def update_ytdlp(request: Request):
    """更新 yt-dlp 到最新版本"""
    result = await ytdlp_updater.update()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


# ===== 優雅重啟支援 =====

@router.get("/can-restart")
async def can_restart():
    """
    檢查是否可以安全重啟服務

    用於 auto-update.bat 在重啟前確認沒有正在執行的任務
    """
    status = downloader.get_status()
    running = status.get("running_count", 0)
    pending = status.get("pending_count", 0)

    return {
        "can_restart": running == 0 and pending == 0,
        "running_tasks": running,
        "pending_tasks": pending,
        "message": "可以安全重啟" if running == 0 and pending == 0 else f"有 {running} 個任務執行中，{pending} 個待執行"
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
