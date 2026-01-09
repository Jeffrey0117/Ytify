# -*- coding: utf-8 -*-
"""
WebSocket 連線管理與進度推送
"""

import asyncio
import json
from typing import Dict, Set, Optional
from fastapi import WebSocket
from datetime import datetime


class ConnectionManager:
    """WebSocket 連線管理器"""

    def __init__(self):
        # task_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # 全域訂閱者（接收所有任務更新）
        self.global_subscribers: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, task_id: Optional[str] = None):
        """接受 WebSocket 連線"""
        await websocket.accept()

        async with self._lock:
            if task_id:
                # 訂閱特定任務
                if task_id not in self.active_connections:
                    self.active_connections[task_id] = set()
                self.active_connections[task_id].add(websocket)
                print(f"[WS] 連線加入: task={task_id}, 連線數={len(self.active_connections[task_id])}")
            else:
                # 全域訂閱
                self.global_subscribers.add(websocket)
                print(f"[WS] 全域訂閱加入, 連線數={len(self.global_subscribers)}")

    async def disconnect(self, websocket: WebSocket, task_id: Optional[str] = None):
        """斷開 WebSocket 連線"""
        async with self._lock:
            if task_id and task_id in self.active_connections:
                self.active_connections[task_id].discard(websocket)
                if not self.active_connections[task_id]:
                    del self.active_connections[task_id]
                print(f"[WS] 連線移除: task={task_id}")
            else:
                self.global_subscribers.discard(websocket)
                print(f"[WS] 全域訂閱移除")

    async def broadcast_to_task(self, task_id: str, data: dict):
        """向特定任務的所有訂閱者廣播"""
        message = json.dumps(data, ensure_ascii=False)

        # 發送給任務訂閱者
        if task_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    dead_connections.add(connection)

            # 清理斷開的連線
            for dead in dead_connections:
                self.active_connections[task_id].discard(dead)

        # 也發送給全域訂閱者
        dead_global = set()
        for connection in self.global_subscribers:
            try:
                await connection.send_text(message)
            except Exception:
                dead_global.add(connection)

        for dead in dead_global:
            self.global_subscribers.discard(dead)

    async def send_personal(self, websocket: WebSocket, data: dict):
        """發送個人訊息"""
        try:
            message = json.dumps(data, ensure_ascii=False)
            await websocket.send_text(message)
        except Exception:
            pass

    def get_connection_count(self, task_id: Optional[str] = None) -> int:
        """取得連線數"""
        if task_id:
            return len(self.active_connections.get(task_id, set()))
        return sum(len(conns) for conns in self.active_connections.values()) + len(self.global_subscribers)


# 全域實例
ws_manager = ConnectionManager()


class ProgressNotifier:
    """進度通知器 - 整合到下載流程中"""

    def __init__(self, manager: ConnectionManager):
        self.manager = manager
        self._update_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    async def start(self):
        """啟動通知處理迴圈"""
        self._running = True
        asyncio.create_task(self._process_queue())

    async def stop(self):
        """停止通知處理"""
        self._running = False

    async def _process_queue(self):
        """處理更新佇列"""
        while self._running:
            try:
                task_id, data = await asyncio.wait_for(
                    self._update_queue.get(),
                    timeout=1.0
                )
                await self.manager.broadcast_to_task(task_id, data)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[WS] 處理佇列錯誤: {e}")

    def notify(self, task_id: str, status: str, **kwargs):
        """
        發送進度通知（非阻塞）

        Args:
            task_id: 任務 ID
            status: 狀態 (queued, downloading, processing, completed, failed)
            **kwargs: 額外資訊 (progress, speed, eta, message, error 等)
        """
        data = {
            "task_id": task_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }

        try:
            self._update_queue.put_nowait((task_id, data))
        except asyncio.QueueFull:
            pass  # 佇列滿了就丟棄

    async def notify_async(self, task_id: str, status: str, **kwargs):
        """發送進度通知（異步版本，直接發送）"""
        data = {
            "task_id": task_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        await self.manager.broadcast_to_task(task_id, data)


# 全域通知器實例
progress_notifier = ProgressNotifier(ws_manager)
