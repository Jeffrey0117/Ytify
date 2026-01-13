# -*- coding: utf-8 -*-
"""
下載歷史持久化服務 - 使用 SQLite
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager


class HistoryDB:
    """下載歷史資料庫"""

    def __init__(self, db_path: str = "./data/history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化資料庫"""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE,
                    video_id TEXT,
                    title TEXT,
                    url TEXT NOT NULL,
                    filename TEXT,
                    format TEXT,
                    audio_only INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    error TEXT,
                    file_size INTEGER,
                    duration INTEGER,
                    thumbnail TEXT,
                    channel TEXT,
                    client_ip TEXT,
                    session_id TEXT,
                    user_id INTEGER,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    updated_at TEXT NOT NULL
                )
            """)

            # 遷移：為舊資料庫新增欄位
            try:
                conn.execute("ALTER TABLE download_history ADD COLUMN client_ip TEXT")
            except sqlite3.OperationalError:
                pass  # 欄位已存在
            try:
                conn.execute("ALTER TABLE download_history ADD COLUMN session_id TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE download_history ADD COLUMN user_id INTEGER")
            except sqlite3.OperationalError:
                pass

            # 建立索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON download_history(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON download_history(created_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_video_id ON download_history(video_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_client_ip ON download_history(client_ip)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON download_history(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON download_history(user_id)")

            conn.commit()
            print(f"[History] 資料庫已初始化: {self.db_path}")

    @contextmanager
    def _get_conn(self):
        """取得資料庫連線"""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def add(self, task_id: str, url: str, **kwargs) -> int:
        """
        新增歷史記錄

        Args:
            task_id: 任務 ID
            url: YouTube URL
            **kwargs: 其他欄位 (video_id, title, filename, format, audio_only, status,
                      client_ip, session_id, user_id, etc.)

        Returns:
            記錄 ID
        """
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO download_history (
                    task_id, video_id, title, url, filename, format, audio_only,
                    status, error, file_size, duration, thumbnail, channel,
                    client_ip, session_id, user_id,
                    created_at, completed_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                kwargs.get('video_id'),
                kwargs.get('title'),
                url,
                kwargs.get('filename'),
                kwargs.get('format'),
                1 if kwargs.get('audio_only') else 0,
                kwargs.get('status', 'pending'),
                kwargs.get('error'),
                kwargs.get('file_size'),
                kwargs.get('duration'),
                kwargs.get('thumbnail'),
                kwargs.get('channel'),
                kwargs.get('client_ip'),
                kwargs.get('session_id'),
                kwargs.get('user_id'),
                now,
                kwargs.get('completed_at'),
                now
            ))
            conn.commit()
            return cursor.lastrowid

    def update(self, task_id: str, **kwargs) -> bool:
        """
        更新歷史記錄

        Args:
            task_id: 任務 ID
            **kwargs: 要更新的欄位

        Returns:
            是否成功
        """
        if not kwargs:
            return False

        # 建立更新語句
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ('video_id', 'title', 'filename', 'format', 'status',
                       'error', 'file_size', 'duration', 'thumbnail', 'channel', 'completed_at'):
                fields.append(f"{key} = ?")
                values.append(value)
            elif key == 'audio_only':
                fields.append("audio_only = ?")
                values.append(1 if value else 0)

        if not fields:
            return False

        # 加入更新時間
        fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(task_id)

        with self._get_conn() as conn:
            cursor = conn.execute(
                f"UPDATE download_history SET {', '.join(fields)} WHERE task_id = ?",
                values
            )
            conn.commit()
            return cursor.rowcount > 0

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        """取得單筆記錄"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM download_history WHERE task_id = ?",
                (task_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_by_video_id(self, video_id: str) -> List[Dict[str, Any]]:
        """根據影片 ID 取得記錄"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM download_history WHERE video_id = ? ORDER BY created_at DESC",
                (video_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    def list(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        client_ip: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        days_limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        取得歷史記錄列表（支援多租戶隔離）

        Args:
            limit: 最大筆數
            offset: 偏移量
            status: 篩選狀態
            client_ip: 篩選 IP
            session_id: 篩選 Session
            user_id: 篩選用戶 ID
            days_limit: 只顯示最近 N 天

        查詢優先級：user_id > session_id > client_ip

        Returns:
            歷史記錄列表
        """
        conditions = []
        params = []

        # 多租戶隔離：優先級 user_id > session_id > client_ip
        if user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)
        elif session_id:
            conditions.append("session_id = ?")
            params.append(session_id)
        elif client_ip:
            conditions.append("client_ip = ?")
            params.append(client_ip)

        if status:
            conditions.append("status = ?")
            params.append(status)

        if days_limit:
            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(days=days_limit)).isoformat()
            conditions.append("created_at >= ?")
            params.append(cutoff)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.extend([limit, offset])

        with self._get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM download_history {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params
            ).fetchall()
            return [dict(row) for row in rows]

    def count(self, status: Optional[str] = None) -> int:
        """取得記錄總數"""
        with self._get_conn() as conn:
            if status:
                row = conn.execute(
                    "SELECT COUNT(*) as count FROM download_history WHERE status = ?",
                    (status,)
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) as count FROM download_history").fetchone()
            return row['count']

    def delete(self, task_id: str) -> bool:
        """刪除記錄"""
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM download_history WHERE task_id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear(self, before_days: Optional[int] = None) -> int:
        """
        清除歷史記錄

        Args:
            before_days: 清除 N 天前的記錄，None 表示全部清除

        Returns:
            刪除的筆數
        """
        with self._get_conn() as conn:
            if before_days:
                from datetime import timedelta
                cutoff = (datetime.now() - timedelta(days=before_days)).isoformat()
                cursor = conn.execute(
                    "DELETE FROM download_history WHERE created_at < ?",
                    (cutoff,)
                )
            else:
                cursor = conn.execute("DELETE FROM download_history")
            conn.commit()
            return cursor.rowcount

    def get_stats(self) -> Dict[str, Any]:
        """取得統計資訊"""
        with self._get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) as count FROM download_history").fetchone()['count']
            completed = conn.execute(
                "SELECT COUNT(*) as count FROM download_history WHERE status = 'completed'"
            ).fetchone()['count']
            failed = conn.execute(
                "SELECT COUNT(*) as count FROM download_history WHERE status = 'failed'"
            ).fetchone()['count']
            total_size = conn.execute(
                "SELECT SUM(file_size) as total FROM download_history WHERE file_size IS NOT NULL"
            ).fetchone()['total'] or 0

            return {
                "total": total,
                "completed": completed,
                "failed": failed,
                "success_rate": round(completed / total * 100, 1) if total > 0 else 0,
                "total_size": total_size,
                "total_size_formatted": self._format_size(total_size)
            }

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


# 全域實例
history_db = HistoryDB()
