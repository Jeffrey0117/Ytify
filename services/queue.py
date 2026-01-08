# -*- coding: utf-8 -*-
"""
任務佇列系統
限制同時執行的下載任務數量，超過的排隊等待
"""
import asyncio
from collections import deque
from typing import Callable, Any, Optional, Dict
from datetime import datetime


class TaskQueue:
    """下載任務佇列"""

    def __init__(self, max_concurrent: int = 3):
        """
        Args:
            max_concurrent: 最大同時執行數量
        """
        self.max_concurrent = max_concurrent
        self.running_count = 0
        self.queue: deque = deque()
        self.lock = asyncio.Lock()
        self.queue_info: Dict[str, dict] = {}  # task_id -> queue info

    @property
    def queue_length(self) -> int:
        return len(self.queue)

    @property
    def running(self) -> int:
        return self.running_count

    async def submit(self, task_id: str, coro_func: Callable, *args, **kwargs) -> None:
        """
        提交任務到佇列

        Args:
            task_id: 任務 ID
            coro_func: 協程函數
            *args, **kwargs: 傳給協程的參數
        """
        async with self.lock:
            # 記錄佇列資訊
            position = self.queue_length + 1
            self.queue_info[task_id] = {
                "task_id": task_id,
                "status": "queued",
                "queue_position": position,
                "submitted_at": datetime.now().isoformat(),
            }

            # 加入佇列
            self.queue.append((task_id, coro_func, args, kwargs))
            print(f"[佇列] 任務加入: {task_id}，位置: {position}，等待中: {self.queue_length}")

        # 嘗試執行
        asyncio.create_task(self._try_process())

    async def _try_process(self) -> None:
        """嘗試從佇列取出任務執行"""
        async with self.lock:
            # 檢查是否可以執行更多任務
            if self.running_count >= self.max_concurrent:
                return
            if not self.queue:
                return

            # 取出任務
            task_id, coro_func, args, kwargs = self.queue.popleft()
            self.running_count += 1

            # 更新排隊中任務的位置
            self._update_queue_positions()

            print(f"[佇列] 開始執行: {task_id}，執行中: {self.running_count}，等待中: {self.queue_length}")

        # 更新狀態為執行中
        if task_id in self.queue_info:
            self.queue_info[task_id]["status"] = "running"
            self.queue_info[task_id]["started_at"] = datetime.now().isoformat()

        try:
            # 執行任務
            await coro_func(*args, **kwargs)
        except Exception as e:
            print(f"[佇列] 任務執行錯誤: {task_id} - {e}")
        finally:
            # 完成後減少計數
            async with self.lock:
                self.running_count -= 1
                # 清理佇列資訊
                if task_id in self.queue_info:
                    del self.queue_info[task_id]
                print(f"[佇列] 任務完成: {task_id}，執行中: {self.running_count}，等待中: {self.queue_length}")

            # 嘗試執行下一個任務
            asyncio.create_task(self._try_process())

    def _update_queue_positions(self):
        """更新所有排隊中任務的位置"""
        for i, (tid, _, _, _) in enumerate(self.queue):
            if tid in self.queue_info:
                self.queue_info[tid]["queue_position"] = i + 1

    def get_queue_info(self, task_id: str) -> Optional[dict]:
        """取得任務的佇列資訊"""
        return self.queue_info.get(task_id)

    def get_stats(self) -> dict:
        """取得佇列統計"""
        return {
            "running": self.running_count,
            "queued": self.queue_length,
            "max_concurrent": self.max_concurrent,
        }

    def is_task_queued(self, task_id: str) -> bool:
        """檢查任務是否在佇列中"""
        info = self.queue_info.get(task_id)
        return info is not None and info.get("status") == "queued"


# 全域佇列實例（最多同時 3 個下載）
download_queue = TaskQueue(max_concurrent=3)
