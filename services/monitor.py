# -*- coding: utf-8 -*-
"""
監控告警系統
"""

import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from contextlib import contextmanager
import json


class AlertLevel(Enum):
    """告警等級"""
    INFO = "info"           # 資訊
    WARNING = "warning"     # 警告
    ERROR = "error"         # 錯誤
    CRITICAL = "critical"   # 嚴重


class AlertType(Enum):
    """告警類型"""
    SYSTEM = "system"              # 系統相關
    DOWNLOAD = "download"          # 下載相關
    QUOTA = "quota"                # 配額相關
    ERROR_RATE = "error_rate"      # 錯誤率
    DISK_SPACE = "disk_space"      # 磁碟空間
    YTDLP = "ytdlp"                # yt-dlp 相關


@dataclass
class Alert:
    """告警資料"""
    id: Optional[int]
    type: AlertType
    level: AlertLevel
    title: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    is_read: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: Optional[str] = None


@dataclass
class MonitorMetric:
    """監控指標"""
    name: str
    value: float
    unit: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: Dict[str, str] = field(default_factory=dict)


class MonitorDB:
    """監控資料庫"""

    def __init__(self, db_path: str = "./data/monitor.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_conn(self):
        """取得資料庫連線"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        """初始化資料庫"""
        with self._get_conn() as conn:
            # 告警表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT,
                    data TEXT,
                    is_read INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TEXT
                )
            """)

            # 指標表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 系統事件表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    description TEXT,
                    data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 建立索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_level ON alerts(level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(name, created_at)")

    def add_alert(self, alert: Alert) -> int:
        """新增告警"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO alerts (type, level, title, message, data, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.type.value,
                alert.level.value,
                alert.title,
                alert.message,
                json.dumps(alert.data) if alert.data else None,
                int(alert.is_read),
                alert.created_at
            ))
            return cursor.lastrowid

    def get_alerts(
        self,
        limit: int = 50,
        level: Optional[AlertLevel] = None,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """取得告警列表"""
        with self._get_conn() as conn:
            query = "SELECT * FROM alerts WHERE 1=1"
            params = []

            if level:
                query += " AND level = ?"
                params.append(level.value)

            if unread_only:
                query += " AND is_read = 0"

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

            result = []
            for row in rows:
                d = dict(row)
                if d["data"]:
                    try:
                        d["data"] = json.loads(d["data"])
                    except:
                        pass
                result.append(d)

            return result

    def mark_read(self, alert_id: int) -> bool:
        """標記已讀"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "UPDATE alerts SET is_read = 1 WHERE id = ?",
                (alert_id,)
            )
            return cursor.rowcount > 0

    def mark_all_read(self) -> int:
        """全部標記已讀"""
        with self._get_conn() as conn:
            cursor = conn.execute("UPDATE alerts SET is_read = 1 WHERE is_read = 0")
            return cursor.rowcount

    def resolve_alert(self, alert_id: int) -> bool:
        """解決告警"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "UPDATE alerts SET resolved_at = ? WHERE id = ?",
                (datetime.now().isoformat(), alert_id)
            )
            return cursor.rowcount > 0

    def get_unread_count(self) -> int:
        """取得未讀數量"""
        with self._get_conn() as conn:
            row = conn.execute("SELECT COUNT(*) as c FROM alerts WHERE is_read = 0").fetchone()
            return row["c"]

    def add_metric(self, metric: MonitorMetric):
        """記錄指標"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO metrics (name, value, unit, tags, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                metric.name,
                metric.value,
                metric.unit,
                json.dumps(metric.tags) if metric.tags else None,
                metric.timestamp
            ))

    def get_metrics(
        self,
        name: str,
        hours: int = 24,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """取得指標歷史"""
        with self._get_conn() as conn:
            since = (datetime.now() - timedelta(hours=hours)).isoformat()
            rows = conn.execute("""
                SELECT * FROM metrics
                WHERE name = ? AND created_at >= ?
                ORDER BY created_at DESC LIMIT ?
            """, (name, since, limit)).fetchall()

            return [dict(row) for row in rows]

    def log_event(self, event_type: str, description: str, data: Dict = None):
        """記錄事件"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO events (event_type, description, data)
                VALUES (?, ?, ?)
            """, (event_type, description, json.dumps(data) if data else None))

    def get_events(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """取得事件列表"""
        with self._get_conn() as conn:
            since = (datetime.now() - timedelta(hours=hours)).isoformat()
            rows = conn.execute("""
                SELECT * FROM events
                WHERE created_at >= ?
                ORDER BY created_at DESC LIMIT ?
            """, (since, limit)).fetchall()

            result = []
            for row in rows:
                d = dict(row)
                if d["data"]:
                    try:
                        d["data"] = json.loads(d["data"])
                    except:
                        pass
                result.append(d)

            return result

    def cleanup_old_data(self, days: int = 30):
        """清理舊資料"""
        with self._get_conn() as conn:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            conn.execute("DELETE FROM metrics WHERE created_at < ?", (cutoff,))
            conn.execute("DELETE FROM events WHERE created_at < ?", (cutoff,))
            conn.execute("DELETE FROM alerts WHERE created_at < ? AND resolved_at IS NOT NULL", (cutoff,))


class MonitorService:
    """監控服務"""

    def __init__(self):
        self.db = MonitorDB()
        self._alert_handlers: List[Callable[[Alert], None]] = []
        self._running = False
        self._check_interval = 60  # 檢查間隔（秒）

        # 監控閾值
        self.thresholds = {
            "error_rate": 0.3,           # 錯誤率 > 30% 告警
            "disk_space_mb": 500,        # 剩餘空間 < 500MB 告警
            "queue_size": 50,            # 佇列大小 > 50 告警
            "download_timeout": 600,     # 下載超時 > 10 分鐘告警
        }

    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """添加告警處理器"""
        self._alert_handlers.append(handler)

    def trigger_alert(self, alert: Alert):
        """觸發告警"""
        alert_id = self.db.add_alert(alert)
        alert.id = alert_id

        # 呼叫所有處理器
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"[監控] 告警處理器錯誤: {e}")

        print(f"[告警] [{alert.level.value.upper()}] {alert.title}: {alert.message}")

    def info(self, title: str, message: str, alert_type: AlertType = AlertType.SYSTEM, data: Dict = None):
        """資訊告警"""
        self.trigger_alert(Alert(
            id=None,
            type=alert_type,
            level=AlertLevel.INFO,
            title=title,
            message=message,
            data=data or {}
        ))

    def warning(self, title: str, message: str, alert_type: AlertType = AlertType.SYSTEM, data: Dict = None):
        """警告告警"""
        self.trigger_alert(Alert(
            id=None,
            type=alert_type,
            level=AlertLevel.WARNING,
            title=title,
            message=message,
            data=data or {}
        ))

    def error(self, title: str, message: str, alert_type: AlertType = AlertType.SYSTEM, data: Dict = None):
        """錯誤告警"""
        self.trigger_alert(Alert(
            id=None,
            type=alert_type,
            level=AlertLevel.ERROR,
            title=title,
            message=message,
            data=data or {}
        ))

    def critical(self, title: str, message: str, alert_type: AlertType = AlertType.SYSTEM, data: Dict = None):
        """嚴重告警"""
        self.trigger_alert(Alert(
            id=None,
            type=alert_type,
            level=AlertLevel.CRITICAL,
            title=title,
            message=message,
            data=data or {}
        ))

    def record_metric(self, name: str, value: float, unit: str = "", tags: Dict = None):
        """記錄指標"""
        self.db.add_metric(MonitorMetric(
            name=name,
            value=value,
            unit=unit,
            tags=tags or {}
        ))

    def log_event(self, event_type: str, description: str, data: Dict = None):
        """記錄事件"""
        self.db.log_event(event_type, description, data)

    async def start_monitoring(self):
        """啟動背景監控"""
        self._running = True
        print("[監控] 背景監控已啟動")

        while self._running:
            try:
                await self._check_system_health()
            except Exception as e:
                print(f"[監控] 檢查錯誤: {e}")

            await asyncio.sleep(self._check_interval)

    def stop_monitoring(self):
        """停止監控"""
        self._running = False
        print("[監控] 背景監控已停止")

    async def _check_system_health(self):
        """檢查系統健康狀態"""
        import shutil

        # 檢查磁碟空間
        try:
            downloads_path = Path("./downloads")
            if downloads_path.exists():
                total, used, free = shutil.disk_usage(downloads_path)
                free_mb = free / (1024 * 1024)

                self.record_metric("disk_free_mb", free_mb, "MB")

                if free_mb < self.thresholds["disk_space_mb"]:
                    self.warning(
                        "磁碟空間不足",
                        f"剩餘空間僅 {free_mb:.0f} MB",
                        AlertType.DISK_SPACE,
                        {"free_mb": free_mb, "threshold": self.thresholds["disk_space_mb"]}
                    )
        except Exception as e:
            print(f"[監控] 磁碟檢查失敗: {e}")

        # 清理舊資料
        try:
            self.db.cleanup_old_data(days=30)
        except Exception as e:
            print(f"[監控] 清理舊資料失敗: {e}")

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """取得儀表板統計"""
        return {
            "unread_alerts": self.db.get_unread_count(),
            "recent_alerts": self.db.get_alerts(limit=5, unread_only=True),
            "recent_events": self.db.get_events(hours=24, limit=10),
        }


# 全域實例
monitor = MonitorService()
