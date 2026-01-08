# -*- coding: utf-8 -*-
"""
yt-dlp 版本管理與自動更新服務
"""

import asyncio
import subprocess
import sys
import re
from datetime import datetime, timedelta
from typing import Optional
import aiohttp


class YtdlpUpdater:
    """yt-dlp 版本管理器"""

    def __init__(self):
        self._current_version: Optional[str] = None
        self._latest_version: Optional[str] = None
        self._last_check: Optional[datetime] = None
        self._update_in_progress: bool = False
        self._last_update: Optional[datetime] = None
        self._update_history: list = []

    def get_current_version(self) -> str:
        """取得目前安裝的 yt-dlp 版本"""
        try:
            import yt_dlp
            self._current_version = yt_dlp.version.__version__
            return self._current_version
        except Exception as e:
            return f"unknown ({e})"

    def get_version_info(self) -> dict:
        """取得完整版本資訊"""
        current = self.get_current_version()
        return {
            "current_version": current,
            "latest_version": self._latest_version,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "last_update": self._last_update.isoformat() if self._last_update else None,
            "update_in_progress": self._update_in_progress,
            "update_available": self._latest_version and current != self._latest_version
        }

    async def check_update(self, force: bool = False) -> dict:
        """
        檢查是否有新版本

        Args:
            force: 強制檢查，忽略快取
        """
        # 快取 10 分鐘
        if not force and self._last_check:
            if datetime.now() - self._last_check < timedelta(minutes=10):
                return {
                    "current_version": self._current_version or self.get_current_version(),
                    "latest_version": self._latest_version,
                    "update_available": self._latest_version and self._current_version != self._latest_version,
                    "cached": True
                }

        current = self.get_current_version()

        try:
            # 從 PyPI 取得最新版本
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://pypi.org/pypi/yt-dlp/json",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._latest_version = data["info"]["version"]
                        self._last_check = datetime.now()

                        return {
                            "current_version": current,
                            "latest_version": self._latest_version,
                            "update_available": current != self._latest_version,
                            "cached": False
                        }
                    else:
                        return {
                            "current_version": current,
                            "latest_version": None,
                            "error": f"PyPI 回應錯誤: {resp.status}"
                        }
        except asyncio.TimeoutError:
            return {
                "current_version": current,
                "latest_version": None,
                "error": "檢查超時"
            }
        except Exception as e:
            return {
                "current_version": current,
                "latest_version": None,
                "error": str(e)
            }

    async def update(self) -> dict:
        """
        更新 yt-dlp 到最新版本

        Returns:
            dict: 包含更新結果的字典
        """
        if self._update_in_progress:
            return {
                "success": False,
                "error": "更新正在進行中，請稍後再試"
            }

        self._update_in_progress = True
        old_version = self.get_current_version()

        try:
            # 使用 pip 更新
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=120  # 2 分鐘超時
            )

            if process.returncode == 0:
                # 重新載入 yt_dlp 模組以取得新版本
                import importlib
                import yt_dlp
                importlib.reload(yt_dlp)

                new_version = self.get_current_version()
                self._last_update = datetime.now()
                self._latest_version = new_version

                # 記錄更新歷史
                self._update_history.append({
                    "time": datetime.now().isoformat(),
                    "from_version": old_version,
                    "to_version": new_version,
                    "success": True
                })

                # 只保留最近 10 筆記錄
                if len(self._update_history) > 10:
                    self._update_history = self._update_history[-10:]

                return {
                    "success": True,
                    "old_version": old_version,
                    "new_version": new_version,
                    "message": f"更新成功: {old_version} → {new_version}" if old_version != new_version else "已是最新版本",
                    "updated": old_version != new_version
                }
            else:
                error_msg = stderr.decode("utf-8", errors="ignore")
                self._update_history.append({
                    "time": datetime.now().isoformat(),
                    "from_version": old_version,
                    "to_version": None,
                    "success": False,
                    "error": error_msg[:500]
                })

                return {
                    "success": False,
                    "error": f"pip 更新失敗: {error_msg[:500]}"
                }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "更新超時（超過 2 分鐘）"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            self._update_in_progress = False

    def get_update_history(self) -> list:
        """取得更新歷史"""
        return self._update_history

    async def auto_check_and_notify(self) -> Optional[dict]:
        """
        自動檢查更新（用於啟動時或定時任務）

        Returns:
            dict: 如果有更新可用，返回版本資訊
        """
        result = await self.check_update(force=True)
        if result.get("update_available"):
            print(f"[yt-dlp] 發現新版本: {result['latest_version']} (目前: {result['current_version']})")
            return result
        return None


# 單例
ytdlp_updater = YtdlpUpdater()
