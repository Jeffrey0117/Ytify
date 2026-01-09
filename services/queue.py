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
        """
        提交任務到佇列

        Args:
            task_id: 任務 ID
            coro_func: 協程函數
            *args, **kwargs: 傳給協程的參數
        """
        should_process_more = False

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
            print(f"[佇列] 任務加入: {task_id}，位置: {position}，"
                  f"running={self.running_count}/{self.max_concurrent}，等待中: {self.queue_length}")

            # 在 lock 內檢查是否需要處理更多任務
            should_process_more = self.running_count < self.max_concurrent

        # 嘗試執行（立即檢查是否可以開始）
        print(f"[佇列 DEBUG] submit 完成，觸發 _try_process (should_process_more={should_process_more})")
        asyncio.create_task(self._try_process())

        # 如果還有空位，持續觸發直到填滿
        if should_process_more:
            # 給一點時間讓前一個 _try_process 執行
            await asyncio.sleep(0.01)
            # 再次檢查並觸發
            if self.running_count < self.max_concurrent and self.queue_length > 0:
                print(f"[佇列 DEBUG] 還有空位，額外觸發 _try_process")
                asyncio.create_task(self._try_process())

    async def _try_process(self) -> None:
        """嘗試從佇列取出任務執行"""
        task_id = None
        coro_func = None
        args = None
        kwargs = None

        async with self.lock:
            # Debug: 印出當前狀態
            print(f"[佇列 DEBUG] _try_process 開始: running={self.running_count}/{self.max_concurrent}, "
                  f"queued={self.queue_length}, running_ids={self.running_task_ids}")

            # 檢查是否可以執行更多任務
            if self.running_count >= self.max_concurrent:
                print(f"[佇列] 已達上限: {self.running_count}/{self.max_concurrent}，等待中: {self.queue_length}")
                return
            if not self.queue:
                print(f"[佇列 DEBUG] 佇列為空，無任務可執行")
                return

            # 取出任務
            task_id, coro_func, args, kwargs = self.queue.popleft()
            self.running_count += 1
            self.running_task_ids.add(task_id)

            # 更新狀態為執行中（在 lock 內更新，避免競態條件）
            if task_id in self.queue_info:
                self.queue_info[task_id]["status"] = "running"
                self.queue_info[task_id]["started_at"] = datetime.now().isoformat()

            # 更新排隊中任務的位置
            self._update_queue_positions()

            print(f"[佇列] 開始執行: {task_id}，執行中: {self.running_count}/{self.max_concurrent}，等待中: {self.queue_length}")

        # 在 lock 外執行任務
        try:
            print(f"[佇列 DEBUG] 準備呼叫 coro_func: {coro_func}, args: {args}")
            result = await coro_func(*args, **kwargs)
            print(f"[佇列 DEBUG] coro_func 返回: {result}")
        except Exception as e:
            import traceback
            print(f"[佇列] 任務執行錯誤: {task_id} - {e}")
            traceback.print_exc()
        finally:
            # 完成後減少計數
            async with self.lock:
                self.running_count -= 1
                self.running_task_ids.discard(task_id)
                # 清理佇列資訊
                if task_id in self.queue_info:
                    del self.queue_info[task_id]
                print(f"[佇列] 任務完成: {task_id}，執行中: {self.running_count}/{self.max_concurrent}，"
                      f"等待中: {self.queue_length}，running_ids={self.running_task_ids}")

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
