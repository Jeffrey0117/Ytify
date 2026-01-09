# -*- coding: utf-8 -*-
"""
任務佇列系統
限制同時執行的下載任務數量，超過的排隊等待
"""
import asyncio
from collections import deque
from typing import Callable, Any, Optional, Dict, Set
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
        self.running_task_ids: Set[str] = set()  # 追蹤正在執行的任務 ID
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
        """提交任務到佇列"""
        async with self.lock:
            position = self.queue_length + 1
            self.queue_info[task_id] = {
                "task_id": task_id,
                "status": "queued",
                "queue_position": position,
                "submitted_at": datetime.now().isoformat(),
            }
            self.queue.append((task_id, coro_func, args, kwargs))

        asyncio.create_task(self._try_process())

    async def _try_process(self) -> None:
        """嘗試從佇列取出任務執行"""
        task_id = None
        coro_func = None
        args = None
        kwargs = None

        async with self.lock:
            # 檢查是否可以執行更多任務
            if self.running_count >= self.max_concurrent or not self.queue:
                return

            # 取出任務
            task_id, coro_func, args, kwargs = self.queue.popleft()
            self.running_count += 1
            self.running_task_ids.add(task_id)

            # 更新狀態為執行中
            if task_id in self.queue_info:
                self.queue_info[task_id]["status"] = "running"
                self.queue_info[task_id]["started_at"] = datetime.now().isoformat()

            self._update_queue_positions()

        # 在 lock 外執行任務
        try:
            await coro_func(*args, **kwargs)
        except Exception as e:
            print(f"[佇列] 任務錯誤: {task_id} - {e}")
        finally:
            async with self.lock:
                self.running_count -= 1
                self.running_task_ids.discard(task_id)
                if task_id in self.queue_info:
                    del self.queue_info[task_id]

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
            "running_task_ids": list(self.running_task_ids),
            "queued": self.queue_length,
            "queued_task_ids": [tid for tid, _, _, _ in self.queue],
            "max_concurrent": self.max_concurrent,
        }

    def is_task_queued(self, task_id: str) -> bool:
        """檢查任務是否在佇列中"""
        info = self.queue_info.get(task_id)
        return info is not None and info.get("status") == "queued"


# 全域佇列實例（最多同時 3 個下載）
download_queue = TaskQueue(max_concurrent=3)
