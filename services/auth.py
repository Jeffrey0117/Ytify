# -*- coding: utf-8 -*-
"""
用戶認證與權限管理系統
"""

import os
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from contextlib import contextmanager


class UserRole(Enum):
    """用戶角色"""
    ADMIN = "admin"       # 管理員 - 完整權限
    USER = "user"         # 一般用戶 - 基本下載
    VIP = "vip"           # VIP 用戶 - 高配額
    GUEST = "guest"       # 訪客 - 受限功能


@dataclass
class User:
    """用戶資料"""
    id: int
    username: str
    email: Optional[str]
    role: UserRole
    api_token: Optional[str]
    daily_quota: int          # 每日下載配額
    monthly_quota: int        # 每月下載配額
    daily_used: int           # 今日已用
    monthly_used: int         # 本月已用
    is_active: bool
    created_at: str
    last_login: Optional[str]


# 角色預設配額
ROLE_QUOTAS = {
    UserRole.ADMIN: {"daily": 999999, "monthly": 999999},
    UserRole.VIP: {"daily": 100, "monthly": 2000},
    UserRole.USER: {"daily": 20, "monthly": 300},
    UserRole.GUEST: {"daily": 5, "monthly": 50},
}


class AuthDB:
    """用戶認證資料庫"""

    def __init__(self, db_path: str = "./data/auth.db"):
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
            # 用戶表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    role TEXT DEFAULT 'user',
                    api_token TEXT UNIQUE,
                    daily_quota INTEGER DEFAULT 20,
                    monthly_quota INTEGER DEFAULT 300,
                    daily_used INTEGER DEFAULT 0,
                    monthly_used INTEGER DEFAULT 0,
                    last_quota_reset TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_login TEXT
                )
            """)

            # API Token 表（支援多 Token）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    name TEXT,
                    permissions TEXT DEFAULT 'read,download',
                    expires_at TEXT,
                    last_used TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # 下載記錄表（用於配額追蹤）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS download_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    task_id TEXT,
                    url TEXT,
                    file_size INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # 建立索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_api_token ON users(api_token)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_tokens_token ON api_tokens(token)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_download_logs_user ON download_logs(user_id, created_at)")

            # 建立預設管理員帳號（如果不存在）
            admin = conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
            if not admin:
                default_password = os.environ.get("YTIFY_ADMIN_PASSWORD", "admin123")
                self._create_user_internal(conn, "admin", default_password, "admin@localhost", UserRole.ADMIN)
                print(f"[認證] 已建立預設管理員帳號: admin / {default_password}")

    def _hash_password(self, password: str) -> str:
        """密碼雜湊"""
        salt = "ytify_salt_2024"  # 實際應用應使用隨機 salt
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

    def _generate_token(self) -> str:
        """生成 API Token"""
        return f"ytf_{secrets.token_urlsafe(32)}"

    def _create_user_internal(self, conn, username: str, password: str, email: str, role: UserRole) -> int:
        """內部用 - 建立用戶"""
        password_hash = self._hash_password(password)
        api_token = self._generate_token()
        quotas = ROLE_QUOTAS.get(role, ROLE_QUOTAS[UserRole.USER])

        cursor = conn.execute("""
            INSERT INTO users (username, password_hash, email, role, api_token, daily_quota, monthly_quota)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, password_hash, email, role.value, api_token, quotas["daily"], quotas["monthly"]))

        return cursor.lastrowid

    def create_user(self, username: str, password: str, email: str = None, role: UserRole = UserRole.USER) -> Dict[str, Any]:
        """建立新用戶"""
        with self._get_conn() as conn:
            # 檢查用戶名是否存在
            existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if existing:
                return {"success": False, "error": "用戶名已存在"}

            try:
                user_id = self._create_user_internal(conn, username, password, email, role)
                user = conn.execute("SELECT api_token FROM users WHERE id = ?", (user_id,)).fetchone()
                return {
                    "success": True,
                    "user_id": user_id,
                    "username": username,
                    "api_token": user["api_token"],
                    "message": "用戶建立成功"
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """驗證用戶登入"""
        with self._get_conn() as conn:
            password_hash = self._hash_password(password)
            row = conn.execute("""
                SELECT * FROM users WHERE username = ? AND password_hash = ? AND is_active = 1
            """, (username, password_hash)).fetchone()

            if not row:
                return None

            # 更新最後登入時間
            conn.execute("UPDATE users SET last_login = ? WHERE id = ?",
                        (datetime.now().isoformat(), row["id"]))

            return self._row_to_user(row)

    def get_user_by_token(self, token: str) -> Optional[User]:
        """透過 API Token 取得用戶"""
        with self._get_conn() as conn:
            # 先檢查主 Token
            row = conn.execute("""
                SELECT * FROM users WHERE api_token = ? AND is_active = 1
            """, (token,)).fetchone()

            if row:
                return self._row_to_user(row)

            # 檢查額外 Token
            token_row = conn.execute("""
                SELECT user_id FROM api_tokens
                WHERE token = ? AND is_active = 1
                AND (expires_at IS NULL OR expires_at > ?)
            """, (token, datetime.now().isoformat())).fetchone()

            if token_row:
                # 更新 Token 使用時間
                conn.execute("UPDATE api_tokens SET last_used = ? WHERE token = ?",
                            (datetime.now().isoformat(), token))

                row = conn.execute("SELECT * FROM users WHERE id = ? AND is_active = 1",
                                  (token_row["user_id"],)).fetchone()
                if row:
                    return self._row_to_user(row)

            return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """透過 ID 取得用戶"""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return self._row_to_user(row) if row else None

    def _row_to_user(self, row) -> User:
        """資料列轉換為 User 物件"""
        return User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            role=UserRole(row["role"]),
            api_token=row["api_token"],
            daily_quota=row["daily_quota"],
            monthly_quota=row["monthly_quota"],
            daily_used=row["daily_used"],
            monthly_used=row["monthly_used"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            last_login=row["last_login"]
        )

    def check_quota(self, user_id: int) -> Dict[str, Any]:
        """檢查用戶配額"""
        with self._get_conn() as conn:
            # 先重置過期的配額
            self._reset_quotas_if_needed(conn, user_id)

            row = conn.execute("""
                SELECT daily_quota, monthly_quota, daily_used, monthly_used
                FROM users WHERE id = ?
            """, (user_id,)).fetchone()

            if not row:
                return {"allowed": False, "error": "用戶不存在"}

            daily_remaining = row["daily_quota"] - row["daily_used"]
            monthly_remaining = row["monthly_quota"] - row["monthly_used"]

            return {
                "allowed": daily_remaining > 0 and monthly_remaining > 0,
                "daily": {
                    "quota": row["daily_quota"],
                    "used": row["daily_used"],
                    "remaining": max(0, daily_remaining)
                },
                "monthly": {
                    "quota": row["monthly_quota"],
                    "used": row["monthly_used"],
                    "remaining": max(0, monthly_remaining)
                }
            }

    def _reset_quotas_if_needed(self, conn, user_id: int):
        """重置過期配額"""
        row = conn.execute("SELECT last_quota_reset FROM users WHERE id = ?", (user_id,)).fetchone()

        now = datetime.now()
        last_reset = None
        if row and row["last_quota_reset"]:
            try:
                last_reset = datetime.fromisoformat(row["last_quota_reset"])
            except:
                pass

        updates = []

        # 檢查是否需要重置每日配額
        if last_reset is None or last_reset.date() < now.date():
            updates.append("daily_used = 0")

        # 檢查是否需要重置每月配額
        if last_reset is None or (last_reset.year < now.year or last_reset.month < now.month):
            updates.append("monthly_used = 0")

        if updates:
            updates.append("last_quota_reset = ?")
            conn.execute(f"UPDATE users SET {', '.join(updates[:-1])}, last_quota_reset = ? WHERE id = ?",
                        (now.isoformat(), user_id))

    def use_quota(self, user_id: int, count: int = 1) -> bool:
        """使用配額"""
        with self._get_conn() as conn:
            self._reset_quotas_if_needed(conn, user_id)

            # 檢查配額
            row = conn.execute("""
                SELECT daily_quota, monthly_quota, daily_used, monthly_used
                FROM users WHERE id = ?
            """, (user_id,)).fetchone()

            if not row:
                return False

            if row["daily_used"] + count > row["daily_quota"]:
                return False
            if row["monthly_used"] + count > row["monthly_quota"]:
                return False

            # 扣除配額
            conn.execute("""
                UPDATE users SET daily_used = daily_used + ?, monthly_used = monthly_used + ?
                WHERE id = ?
            """, (count, count, user_id))

            return True

    def log_download(self, user_id: int, task_id: str, url: str, file_size: int = None):
        """記錄下載"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO download_logs (user_id, task_id, url, file_size)
                VALUES (?, ?, ?, ?)
            """, (user_id, task_id, url, file_size))

    def list_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """列出用戶"""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, username, email, role, daily_quota, monthly_quota,
                       daily_used, monthly_used, is_active, created_at, last_login
                FROM users ORDER BY id DESC LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()

            return [dict(row) for row in rows]

    def update_user(self, user_id: int, **kwargs) -> bool:
        """更新用戶資料"""
        allowed_fields = ["email", "role", "daily_quota", "monthly_quota", "is_active"]
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        with self._get_conn() as conn:
            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values()) + [user_id]
            conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            return True

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """變更密碼"""
        with self._get_conn() as conn:
            old_hash = self._hash_password(old_password)
            row = conn.execute("SELECT id FROM users WHERE id = ? AND password_hash = ?",
                              (user_id, old_hash)).fetchone()
            if not row:
                return False

            new_hash = self._hash_password(new_password)
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
            return True

    def regenerate_token(self, user_id: int) -> Optional[str]:
        """重新生成 API Token"""
        with self._get_conn() as conn:
            new_token = self._generate_token()
            conn.execute("UPDATE users SET api_token = ? WHERE id = ?", (new_token, user_id))
            return new_token

    def create_api_token(self, user_id: int, name: str, permissions: str = "read,download",
                        expires_days: int = None) -> Dict[str, Any]:
        """建立額外的 API Token"""
        with self._get_conn() as conn:
            token = self._generate_token()
            expires_at = None
            if expires_days:
                expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()

            conn.execute("""
                INSERT INTO api_tokens (user_id, token, name, permissions, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, token, name, permissions, expires_at))

            return {
                "token": token,
                "name": name,
                "permissions": permissions,
                "expires_at": expires_at
            }

    def list_api_tokens(self, user_id: int) -> List[Dict[str, Any]]:
        """列出用戶的 API Tokens"""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, token, name, permissions, expires_at, last_used, created_at, is_active
                FROM api_tokens WHERE user_id = ?
            """, (user_id,)).fetchall()

            # 遮蔽 Token（只顯示前後幾位）
            result = []
            for row in rows:
                d = dict(row)
                token = d["token"]
                d["token_masked"] = f"{token[:8]}...{token[-4:]}"
                result.append(d)

            return result

    def revoke_api_token(self, token_id: int, user_id: int) -> bool:
        """撤銷 API Token"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                UPDATE api_tokens SET is_active = 0
                WHERE id = ? AND user_id = ?
            """, (token_id, user_id))
            return cursor.rowcount > 0

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """取得用戶統計"""
        with self._get_conn() as conn:
            # 總下載數
            total = conn.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(file_size), 0) as size
                FROM download_logs WHERE user_id = ?
            """, (user_id,)).fetchone()

            # 今日下載
            today = datetime.now().date().isoformat()
            today_stats = conn.execute("""
                SELECT COUNT(*) as count FROM download_logs
                WHERE user_id = ? AND created_at >= ?
            """, (user_id, today)).fetchone()

            return {
                "total_downloads": total["count"],
                "total_size": total["size"],
                "today_downloads": today_stats["count"]
            }


# 全域實例
auth_db = AuthDB()
