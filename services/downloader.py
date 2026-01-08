# -*- coding: utf-8 -*-
"""
ytify 下載服務 - 使用 yt-dlp
"""

import os
import re
import uuid
import time
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Set
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import yt_dlp


def clean_youtube_url(url: str) -> str:
    """清理 YouTube URL，只保留影片 ID，移除多餘參數"""
    # 提取影片 ID
    video_id = None

    # 標準格式: youtube.com/watch?v=xxx
    if 'youtube.com' in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        video_id = params.get('v', [None])[0]
    # 短網址: youtu.be/xxx
    elif 'youtu.be' in url:
        parsed = urlparse(url)
        video_id = parsed.path.strip('/')

    if video_id:
        # 返回乾淨的 URL
        clean_url = f"https://www.youtube.com/watch?v={video_id}"
        if clean_url != url:
            print(f"[URL] 清理: {url[:80]}... -> {clean_url}")
        return clean_url

    # 無法解析，返回原始 URL
    return url


class Downloader:
    """YouTube 下載服務"""

    def __init__(self):
        self.download_path = Path("./downloads")
        self.download_path.mkdir(parents=True, exist_ok=True)

        self.is_running = False
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.current_task_id: Optional[str] = None
        self.history = []

        # 代理設定
        self.proxy = None
        self.proxy_pool_api = None  # 如: "http://localhost:5010/get"

        # 壞代理黑名單 (自動記錄失敗的代理)
        self.bad_proxies: Set[str] = set()
        self.current_proxy: Optional[str] = None  # 當前使用的代理
        self.max_proxy_retries = 20  # 最多嘗試幾個不同代理（免費代理大多不能用）

        # Cookies 設定 (繞過 rate limit)
        self.cookies_file = Path("./cookies.txt")  # Netscape 格式 cookies 檔案
        self.use_browser_cookies = "chrome"  # 或 "firefox", "edge", None

    def _get_cookie_opts(self) -> dict:
        """取得 cookies 相關的 yt-dlp 選項"""
        opts = {}

        # 優先使用 cookies 檔案
        if self.cookies_file.exists():
            opts['cookiefile'] = str(self.cookies_file)
            print(f"[Cookies] 使用檔案: {self.cookies_file}")
        # 否則嘗試從瀏覽器讀取
        elif self.use_browser_cookies:
            opts['cookiesfrombrowser'] = (self.use_browser_cookies,)
            print(f"[Cookies] 從 {self.use_browser_cookies} 瀏覽器讀取")

        return opts

    def _get_proxy(self) -> Optional[str]:
        """取得代理 IP（支援代理池，自動排除壞代理，驗證代理可用性）"""
        if self.proxy_pool_api:
            import requests

            # 嘗試取得可用代理
            for attempt in range(self.max_proxy_retries):
                try:
                    resp = requests.get(self.proxy_pool_api, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        if 'proxy' in data and data['proxy']:
                            proxy = data['proxy']
                            proxy_url = f"http://{proxy}"

                            # 跳過黑名單中的代理
                            if proxy in self.bad_proxies:
                                print(f"[Proxy] Skip bad proxy: {proxy}")
                                time.sleep(0.3)
                                continue

                            # 驗證代理是否可連線
                            if self._test_proxy(proxy_url):
                                print(f"[Proxy] Using: {proxy}")
                                self.current_proxy = proxy
                                return proxy_url
                            else:
                                print(f"[Proxy] Dead proxy: {proxy}")
                                self.mark_proxy_bad(proxy)
                                continue

                    time.sleep(0.5)
                except Exception as e:
                    print(f"[Proxy] Attempt {attempt+1} failed: {e}")
                    time.sleep(0.5)

            print(f"[Proxy] All {self.max_proxy_retries} attempts failed, using direct connection")

        self.current_proxy = None
        return self.proxy

    def _test_proxy(self, proxy_url: str, timeout: int = 8) -> bool:
        """測試代理是否可用（直接測 YouTube）"""
        import requests
        try:
            # 直接測試能不能連 YouTube
            resp = requests.get(
                "https://www.youtube.com/",
                proxies={"http": proxy_url, "https": proxy_url},
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            # 檢查是否被 YouTube 擋（403, 429 等）
            if resp.status_code == 200:
                # 額外檢查是否有被擋的跡象
                if "Sign in" in resp.text[:5000] or "youtube" in resp.text.lower()[:5000]:
                    return True
            return False
        except:
            return False

    def mark_proxy_bad(self, proxy: Optional[str] = None):
        """標記代理為壞代理"""
        target = proxy or self.current_proxy
        if target:
            self.bad_proxies.add(target)
            print(f"[Proxy] Marked as bad: {target} (total bad: {len(self.bad_proxies)})")

            # 通知 proxy_pool 刪除這個代理
            if self.proxy_pool_api:
                self._delete_from_pool(target)

    def _delete_from_pool(self, proxy: str):
        """從 proxy_pool 刪除壞代理"""
        try:
            import requests
            # proxy_pool 的刪除 API
            delete_url = self.proxy_pool_api.replace('/get', '/delete')
            resp = requests.get(f"{delete_url}?proxy={proxy}", timeout=3)
            if resp.status_code == 200:
                print(f"[Proxy] Deleted from pool: {proxy}")
        except Exception as e:
            print(f"[Proxy] Failed to delete from pool: {e}")

    def get_bad_proxies(self) -> list:
        """取得壞代理清單"""
        return list(self.bad_proxies)

    def clear_bad_proxies(self):
        """清除壞代理黑名單"""
        count = len(self.bad_proxies)
        self.bad_proxies.clear()
        print(f"[Proxy] Cleared {count} bad proxies")
        return count

    def get_proxy_stats(self) -> Dict[str, Any]:
        """取得代理統計"""
        return {
            "proxy": self.proxy,
            "proxy_pool_api": self.proxy_pool_api,
            "current_proxy": self.current_proxy,
            "bad_proxy_count": len(self.bad_proxies),
            "bad_proxies": list(self.bad_proxies)[:20],  # 只顯示前 20 個
        }

    def get_status(self) -> Dict[str, Any]:
        """取得當前狀態"""
        current_task = None
        if self.current_task_id:
            current_task = self.tasks.get(self.current_task_id)

        return {
            "is_running": self.is_running,
            "current_task": current_task,
            "pending_count": sum(1 for t in self.tasks.values() if t["status"] == "queued"),
        }

    def create_task(self, url: str, format_option: str = "best", audio_only: bool = False) -> str:
        """建立下載任務"""
        # 清理 URL
        url = clean_youtube_url(url)

        task_id = str(uuid.uuid4())[:8]

        self.tasks[task_id] = {
            "task_id": task_id,
            "url": url,
            "format": format_option,
            "audio_only": audio_only,
            "status": "queued",
            "progress": 0,
            "speed": None,
            "eta": None,
            "filename": None,
            "title": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
        }

        return task_id

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """取得任務狀態"""
        return self.tasks.get(task_id)

    def _progress_hook(self, d: Dict[str, Any]):
        """下載進度回調"""
        if not self.current_task_id:
            return

        task = self.tasks.get(self.current_task_id)
        if not task:
            return

        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0%').strip()
            try:
                percent = float(percent_str.replace('%', ''))
            except:
                percent = 0

            task.update({
                "status": "downloading",
                "progress": percent,
                "speed": d.get('_speed_str', 'N/A'),
                "eta": d.get('_eta_str', 'N/A'),
                "filename": os.path.basename(d.get('filename', '')),
                "downloaded_bytes": d.get('downloaded_bytes'),
                "total_bytes": d.get('total_bytes') or d.get('total_bytes_estimate'),
            })

        elif d['status'] == 'finished':
            task.update({
                "status": "processing",
                "progress": 100,
                "message": "正在處理...",
                "filename": os.path.basename(d.get('filename', '')),
            })

    def _sync_get_video_info(self, url: str) -> Dict[str, Any]:
        """同步取得影片資訊（在線程池中執行）"""
        # 清理 URL
        url = clean_youtube_url(url)

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        # 加入 cookies（繞過 rate limit）- 先關掉，測試 URL 清理是否解決問題
        # ydl_opts.update(self._get_cookie_opts())

        # 加入代理（如果有設定）
        proxy = self._get_proxy()
        if proxy:
            ydl_opts['proxy'] = proxy

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # 整理格式資訊
                formats = []
                for f in info.get('formats', []):
                    if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                        formats.append({
                            "format_id": f.get('format_id'),
                            "ext": f.get('ext'),
                            "resolution": f.get('resolution') or f"{f.get('width', '?')}x{f.get('height', '?')}",
                            "filesize": f.get('filesize') or f.get('filesize_approx'),
                            "vcodec": f.get('vcodec'),
                            "acodec": f.get('acodec'),
                            "fps": f.get('fps'),
                        })

                return {
                    "id": info.get('id'),
                    "title": info.get('title'),
                    "duration": info.get('duration'),
                    "thumbnail": info.get('thumbnail'),
                    "channel": info.get('channel') or info.get('uploader'),
                    "view_count": info.get('view_count'),
                    "upload_date": info.get('upload_date'),
                    "description": info.get('description', '')[:500],  # 截斷描述
                    "formats": formats[-15:],  # 只返回最後 15 個格式
                }
        except Exception as e:
            return {"error": str(e)}

    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """取得影片資訊（非阻塞）"""
        return await asyncio.to_thread(self._sync_get_video_info, url)

    def _sync_execute_download(self, task_id: str) -> Dict[str, Any]:
        """同步執行下載（在線程池中執行，支援代理重試）"""
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "任務不存在"}

        url = task["url"]
        format_option = task["format"]
        audio_only = task["audio_only"]
        max_retries = 3  # 最多重試 3 次（換不同代理）
        last_error = None

        for retry in range(max_retries):
            try:
                # 設定下載選項
                ydl_opts = {
                    'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
                    'progress_hooks': [self._progress_hook],
                    'quiet': True,
                    'no_warnings': True,
                    'socket_timeout': 30,
                }

                # 加入 cookies（繞過 rate limit）- 先關掉
                # ydl_opts.update(self._get_cookie_opts())

                # 加入代理（如果有設定）
                proxy = self._get_proxy()
                if proxy:
                    ydl_opts['proxy'] = proxy
                    task["current_proxy"] = self.current_proxy

                if audio_only:
                    ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'aac',
                        'preferredquality': '192',
                    }]
                else:
                    if format_option == "best":
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                    elif format_option == "1080p":
                        ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
                    elif format_option == "720p":
                        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
                    elif format_option == "480p":
                        ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]/best'
                    else:
                        ydl_opts['format'] = format_option
                    ydl_opts['merge_output_format'] = 'mp4'
                    # 強制音訊轉換成 AAC（避免 Opus 不相容問題）
                    ydl_opts['postprocessor_args'] = ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k']

                # 執行下載
                retry_msg = f" (retry {retry+1})" if retry > 0 else ""
                print(f"[下載] 開始下載{retry_msg}: {url}")
                print(f"[下載] 格式: {ydl_opts.get('format')}")
                if self.current_proxy:
                    print(f"[下載] 代理: {self.current_proxy}")

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if info is None:
                        raise Exception("無法取得影片資訊")

                    filename = ydl.prepare_filename(info)
                    title = info.get('title', 'Unknown')
                    video_id = info.get('id', '')
                    base_filename = os.path.basename(filename)
                    print(f"[下載] 完成: {filename}")

                    # 更新任務狀態
                    task.update({
                        "status": "completed",
                        "progress": 100,
                        "title": title,
                        "filename": base_filename,
                        "completed_at": datetime.now().isoformat(),
                    })

                    # 加入歷史
                    self.history.insert(0, {
                        "task_id": task_id,
                        "id": video_id,
                        "title": title,
                        "filename": base_filename,
                        "url": url,
                        "status": "completed",
                        "completed_at": datetime.now().isoformat(),
                    })

                    return {
                        "success": True,
                        "title": title,
                        "filename": base_filename,
                    }

            except Exception as e:
                last_error = str(e)
                print(f"[下載] 失敗: {last_error}")

                # 檢查是否是代理相關錯誤
                is_proxy_error = any(keyword in last_error.lower() for keyword in [
                    'proxy', 'timeout', 'connection', 'socket', 'rate',
                    'blocked', '429', '403', 'unavailable'
                ])

                if is_proxy_error and self.current_proxy:
                    # 標記當前代理為壞代理
                    self.mark_proxy_bad()
                    print(f"[下載] 將重試 ({retry+1}/{max_retries})...")
                    task["status"] = "retrying"
                    task["retry_count"] = retry + 1
                    time.sleep(2)
                    continue
                else:
                    # 非代理錯誤，直接失敗
                    break

        # 所有重試都失敗
        task.update({
            "status": "failed",
            "error": last_error,
        })

        self.history.insert(0, {
            "task_id": task_id,
            "url": task["url"],
            "status": "failed",
            "error": last_error,
            "failed_at": datetime.now().isoformat(),
        })

        return {"success": False, "error": last_error}

    def _finally_cleanup(self):
        """清理下載狀態"""
        self.is_running = False
        self.current_task_id = None

    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """執行下載任務（非阻塞）"""
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "任務不存在"}

        if self.is_running:
            return {"success": False, "error": "已有下載任務進行中"}

        self.is_running = True
        self.current_task_id = task_id
        task["status"] = "downloading"

        try:
            # 在線程池中執行同步下載，不阻塞 event loop
            return await asyncio.to_thread(self._sync_execute_download, task_id)
        finally:
            self.is_running = False
            self.current_task_id = None

    def list_downloads(self):
        """列出已下載的檔案"""
        if not self.download_path.exists():
            return []

        videos = []
        extensions = {'.mp4', '.webm', '.mkv', '.avi', '.mp3', '.m4a', '.wav', '.flac'}

        for file in self.download_path.iterdir():
            if file.is_file() and file.suffix.lower() in extensions:
                stat = file.stat()
                videos.append({
                    "filename": file.name,
                    "size": stat.st_size,
                    "size_formatted": self._format_size(stat.st_size),
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "path": str(file.absolute()),
                })

        videos.sort(key=lambda x: x["created_at"], reverse=True)
        return videos

    def delete_file(self, filename: str) -> bool:
        """刪除檔案"""
        file_path = self.download_path / filename
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False

    def get_history(self):
        """取得下載歷史"""
        return self.history[:100]

    def clear_history(self):
        """清除歷史"""
        self.history = []

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化檔案大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


# 單例
downloader = Downloader()
