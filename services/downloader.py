# -*- coding: utf-8 -*-
"""
ytify 下載服務 - 使用 yt-dlp
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import yt_dlp


class Downloader:
    """YouTube 下載服務"""

    def __init__(self):
        self.download_path = Path("./downloads")
        self.download_path.mkdir(parents=True, exist_ok=True)

        self.is_running = False
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.current_task_id: Optional[str] = None
        self.history = []

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

    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """取得影片資訊"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

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

    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """執行下載任務"""
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "任務不存在"}

        if self.is_running:
            return {"success": False, "error": "已有下載任務進行中"}

        self.is_running = True
        self.current_task_id = task_id
        task["status"] = "downloading"

        try:
            url = task["url"]
            format_option = task["format"]
            audio_only = task["audio_only"]

            # 設定下載選項
            ydl_opts = {
                'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
            }

            if audio_only:
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                if format_option == "best":
                    ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                elif format_option == "1080p":
                    ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]'
                elif format_option == "720p":
                    ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]'
                elif format_option == "480p":
                    ydl_opts['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]'
                else:
                    ydl_opts['format'] = format_option

                ydl_opts['merge_output_format'] = 'mp4'

            # 執行下載
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

                # 更新任務狀態
                task.update({
                    "status": "completed",
                    "progress": 100,
                    "title": info.get('title'),
                    "filename": os.path.basename(filename),
                    "completed_at": datetime.now().isoformat(),
                })

                # 加入歷史
                self.history.insert(0, {
                    "task_id": task_id,
                    "id": info.get('id'),
                    "title": info.get('title'),
                    "filename": os.path.basename(filename),
                    "url": url,
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),
                })

            return {
                "success": True,
                "title": info.get('title'),
                "filename": os.path.basename(filename),
            }

        except Exception as e:
            error_msg = str(e)

            task.update({
                "status": "failed",
                "error": error_msg,
            })

            self.history.insert(0, {
                "task_id": task_id,
                "url": task["url"],
                "status": "failed",
                "error": error_msg,
                "failed_at": datetime.now().isoformat(),
            })

            return {"success": False, "error": error_msg}

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
