# ytify 實作規格書

## 開發啟動清單

### Phase 1：基礎防護（預估 4 小時）

- [ ] 1.1 Rate Limiting
- [ ] 1.2 URL 驗證
- [ ] 1.3 記憶體任務佇列

### Phase 2：使用體驗（預估 6 小時）

- [ ] 2.1 排隊狀態顯示
- [ ] 2.2 重試機制
- [ ] 2.3 前端 UI 更新

### Phase 3：進階功能（預估 1-2 天）

- [ ] 3.1 Token 認證
- [ ] 3.2 檔案生命週期管理
- [ ] 3.3 磁碟空間保護

---

## Phase 1：基礎防護

### 1.1 Rate Limiting

**目標**：限制每個 IP 的請求頻率

**安裝依賴**：
```bash
pip install slowapi
```

**修改檔案**：`main.py`

```python
# === 新增 import ===
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# === 初始化 limiter ===
limiter = Limiter(key_func=get_remote_address)

# === 在 app 建立後加入 ===
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**修改檔案**：`api/routes.py`

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

@router.post("/info")
@limiter.limit("30/minute")
async def get_info(request: Request, req: InfoRequest):
    # ... 原有邏輯
    pass

@router.post("/download")
@limiter.limit("10/minute")
async def download(request: Request, req: DownloadRequest):
    # ... 原有邏輯
    pass
```

**測試**：
```bash
# 連續發 11 次請求，第 11 次應該收到 429
for i in {1..11}; do curl -X POST http://localhost:8765/api/download -d '{"url":"..."}'; done
```

---

### 1.2 URL 驗證

**目標**：只接受合法 YouTube URL

**修改檔案**：`services/downloader.py`

```python
import re

# YouTube URL 驗證模式
YOUTUBE_URL_PATTERNS = [
    r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]{11}',
    r'^https?://(www\.)?youtube\.com/shorts/[\w-]{11}',
    r'^https?://youtu\.be/[\w-]{11}',
    r'^https?://(www\.)?youtube\.com/embed/[\w-]{11}',
    r'^https?://music\.youtube\.com/watch\?v=[\w-]{11}',
]

def is_valid_youtube_url(url: str) -> bool:
    """驗證是否為合法 YouTube URL"""
    if not url:
        return False
    # 移除多餘參數後驗證
    clean_url = clean_youtube_url(url)
    return any(re.match(pattern, clean_url) for pattern in YOUTUBE_URL_PATTERNS)
```

**修改檔案**：`api/routes.py`

```python
from services.downloader import is_valid_youtube_url

@router.post("/info")
async def get_info(req: InfoRequest):
    if not is_valid_youtube_url(req.url):
        raise HTTPException(400, "無效的 YouTube URL")
    # ... 原有邏輯

@router.post("/download")
async def download(req: DownloadRequest):
    if not is_valid_youtube_url(req.url):
        raise HTTPException(400, "無效的 YouTube URL")
    # ... 原有邏輯
```

---

### 1.3 記憶體任務佇列

**目標**：限制同時下載數量，超過的排隊等待

**新增檔案**：`services/queue.py`

```python
"""
任務佇列系統
限制同時執行的下載任務數量
"""
import asyncio
from collections import deque
from typing import Callable, Any, Optional
from datetime import datetime
import uuid


class TaskQueue:
    def __init__(self, max_concurrent: int = 3):
        """
        Args:
            max_concurrent: 最大同時執行數量
        """
        self.max_concurrent = max_concurrent
        self.running_count = 0
        self.queue: deque = deque()
        self.lock = asyncio.Lock()
        self.tasks: dict = {}  # task_id -> task_info

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
        # 記錄任務資訊
        self.tasks[task_id] = {
            "id": task_id,
            "status": "queued",
            "queue_position": self.queue_length + 1,
            "submitted_at": datetime.now().isoformat(),
        }

        # 加入佇列
        self.queue.append((task_id, coro_func, args, kwargs))

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
            for i, (tid, _, _, _) in enumerate(self.queue):
                if tid in self.tasks:
                    self.tasks[tid]["queue_position"] = i + 1

        # 更新狀態為執行中
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "running"
            self.tasks[task_id]["started_at"] = datetime.now().isoformat()

        try:
            # 執行任務
            await coro_func(*args, **kwargs)
        finally:
            # 完成後減少計數
            async with self.lock:
                self.running_count -= 1
                if task_id in self.tasks:
                    del self.tasks[task_id]

            # 嘗試執行下一個任務
            asyncio.create_task(self._try_process())

    def get_queue_info(self, task_id: str) -> Optional[dict]:
        """取得任務的佇列資訊"""
        return self.tasks.get(task_id)

    def get_stats(self) -> dict:
        """取得佇列統計"""
        return {
            "running": self.running_count,
            "queued": self.queue_length,
            "max_concurrent": self.max_concurrent,
        }


# 全域佇列實例
download_queue = TaskQueue(max_concurrent=3)
```

**修改檔案**：`services/downloader.py`

```python
from services.queue import download_queue

class Downloader:
    # ... 其他程式碼 ...

    async def download(self, url: str, format: str = "best", audio_only: bool = False) -> str:
        """開始下載（加入佇列）"""
        task_id = str(uuid.uuid4())

        # 初始化任務狀態
        self.tasks[task_id] = {
            "status": "queued",
            "progress": 0,
            "message": "排隊中...",
        }

        # 提交到佇列
        await download_queue.submit(
            task_id,
            self._do_download,
            task_id, url, format, audio_only
        )

        return task_id

    async def _do_download(self, task_id: str, url: str, format: str, audio_only: bool):
        """實際執行下載（由佇列呼叫）"""
        # 原本 download 方法的邏輯移到這裡
        self.tasks[task_id]["status"] = "downloading"
        self.tasks[task_id]["message"] = "下載中..."
        # ... 原有下載邏輯 ...
```

**修改檔案**：`api/routes.py`

```python
from services.queue import download_queue

@router.get("/queue-stats")
async def get_queue_stats():
    """取得佇列狀態"""
    return download_queue.get_stats()

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    # 先檢查佇列狀態
    queue_info = download_queue.get_queue_info(task_id)
    if queue_info and queue_info["status"] == "queued":
        return {
            "status": "queued",
            "queue_position": queue_info["queue_position"],
            "message": f"排隊中（第 {queue_info['queue_position']} 位）"
        }

    # 原有的狀態查詢
    task = downloader.get_task_status(task_id)
    # ...
```

---

## Phase 2：使用體驗

### 2.1 排隊狀態顯示

**修改檔案**：`scripts/ytify.user.js`

```javascript
// 在 pollYtifyStatus 中處理 queued 狀態
if (status.status === 'queued') {
    onProgress(0, null, 'queued', `排隊中（第 ${status.queue_position} 位）`);
    pollTimer = setTimeout(poll, CONFIG.POLL_INTERVAL);
    return;
}
```

```javascript
// 在 downloadViaYtify 中顯示排隊狀態
pollYtifyStatus(
    result.task_id,
    (progress, speed, status, message) => {
        if (status === 'queued') {
            showToast({
                title: '⏳ 排隊中',
                sub: message,
                progress: 'loading',
                buttons: [{ text: '取消', onClick: cancelDownload }]
            });
            return;
        }
        // ... 原有邏輯
    },
    // ...
);
```

---

### 2.2 重試機制

**修改檔案**：`services/downloader.py`

```python
class Downloader:
    MAX_RETRIES = 3
    RETRY_DELAY = [2, 5, 10]  # 重試間隔秒數

    async def _do_download(self, task_id: str, url: str, format: str, audio_only: bool):
        """實際執行下載，含重試機制"""
        last_error = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                if attempt > 0:
                    delay = self.RETRY_DELAY[min(attempt - 1, len(self.RETRY_DELAY) - 1)]
                    self.tasks[task_id].update({
                        "status": "retrying",
                        "retry_count": attempt,
                        "message": f"重試中 ({attempt}/{self.MAX_RETRIES})，等待 {delay} 秒..."
                    })
                    await asyncio.sleep(delay)

                # 執行下載
                await self._execute_download(task_id, url, format, audio_only)
                return  # 成功就結束

            except Exception as e:
                last_error = str(e)
                # 判斷是否值得重試
                if not self._should_retry(e):
                    break

        # 所有重試都失敗
        self.tasks[task_id].update({
            "status": "failed",
            "error": last_error,
            "message": f"下載失敗：{last_error}"
        })

    def _should_retry(self, error: Exception) -> bool:
        """判斷錯誤是否值得重試"""
        error_msg = str(error).lower()
        # 這些錯誤值得重試
        retry_keywords = ['rate limit', 'timeout', 'connection', 'temporary', '429', '503']
        return any(kw in error_msg for kw in retry_keywords)
```

---

### 2.3 前端 UI 更新

**修改檔案**：`scripts/ytify.user.js`

```javascript
// 完整的狀態處理
pollYtifyStatus(
    result.task_id,
    (progress, speed, status, message) => {
        let toastConfig = {
            buttons: [{ text: '取消', onClick: cancelDownload }]
        };

        switch (status) {
            case 'queued':
                toastConfig.title = '⏳ 排隊中';
                toastConfig.sub = message;
                toastConfig.progress = 'loading';
                break;

            case 'retrying':
                toastConfig.title = '🔄 重試中';
                toastConfig.sub = message;
                toastConfig.progress = 'loading';
                toastConfig.state = 'warn';
                break;

            case 'downloading':
                toastConfig.title = `下載中 ${Math.round(progress)}%`;
                toastConfig.sub = `${info.title || title}${speed ? '　' + speed : ''}`;
                toastConfig.progress = progress;
                break;

            case 'processing':
                toastConfig.title = '🔄 處理中...';
                toastConfig.sub = message || '正在轉換格式...';
                toastConfig.progress = 'loading';
                break;

            default:
                toastConfig.title = '處理中...';
                toastConfig.sub = message || '';
                toastConfig.progress = 'loading';
        }

        showToast(toastConfig);
    },
    // onComplete, onError ...
);
```

**修改檔案**：`static/download.html`

```javascript
// 網頁版也要支援新狀態
function updateProgress(status) {
    const statusText = document.getElementById('status-text');
    const progressBar = document.getElementById('progress-bar');

    switch (status.status) {
        case 'queued':
            statusText.textContent = `排隊中（第 ${status.queue_position} 位）`;
            progressBar.style.width = '0%';
            progressBar.classList.add('indeterminate');
            break;

        case 'retrying':
            statusText.textContent = status.message;
            progressBar.classList.add('warning');
            break;

        case 'downloading':
            statusText.textContent = `下載中 ${status.progress}%`;
            progressBar.style.width = status.progress + '%';
            progressBar.classList.remove('indeterminate', 'warning');
            break;

        case 'processing':
            statusText.textContent = '轉換格式中...';
            progressBar.classList.add('indeterminate');
            break;

        // ...
    }
}
```

---

## Phase 3：進階功能

### 3.1 Token 認證

**新增檔案**：`.env`
```
API_TOKEN=your-secret-token-here
ENABLE_AUTH=true
```

**新增檔案**：`services/auth.py`

```python
import os
from fastapi import Header, HTTPException, Depends
from typing import Optional

# 從環境變數讀取
API_TOKEN = os.getenv("API_TOKEN", "")
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"


async def verify_token(x_api_token: Optional[str] = Header(None)):
    """驗證 API Token"""
    if not ENABLE_AUTH:
        return True

    if not API_TOKEN:
        # 沒設定 token 就不驗證
        return True

    if x_api_token != API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="無效的 API Token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return True


# 用於保護路由的依賴
require_auth = Depends(verify_token)
```

**修改檔案**：`api/routes.py`

```python
from services.auth import require_auth

@router.post("/download")
async def download(req: DownloadRequest, _: bool = require_auth):
    # ... 原有邏輯
    pass
```

**修改檔案**：`scripts/ytify.user.js`

```javascript
// 設定區增加 Token
const YTIFY_API_TOKEN = '';  // 如果服務需要認證，填入 Token

// 修改 ytifyRequest 函數
function ytifyRequest(method, path, data = null, timeout = 30000) {
    return new Promise((resolve, reject) => {
        const headers = { 'Content-Type': 'application/json' };
        if (YTIFY_API_TOKEN) {
            headers['X-API-Token'] = YTIFY_API_TOKEN;
        }

        GM_xmlhttpRequest({
            method,
            url: CONFIG.YTIFY_API + path,
            headers,
            // ... 其他設定
        });
    });
}
```

---

### 3.2 檔案生命週期管理

**修改檔案**：`services/downloader.py`

```python
from datetime import datetime, timedelta

class FileLifecycle:
    """檔案生命週期管理"""

    def __init__(self, download_path: Path):
        self.download_path = download_path
        self.download_times: dict = {}  # filename -> first_download_time
        self.expire_hours = 2  # 下載後 2 小時刪除

    def mark_downloaded(self, filename: str):
        """標記檔案已被下載"""
        if filename not in self.download_times:
            self.download_times[filename] = datetime.now()

    def get_expire_time(self, filename: str) -> Optional[datetime]:
        """取得檔案過期時間"""
        if filename in self.download_times:
            return self.download_times[filename] + timedelta(hours=self.expire_hours)
        return None

    async def cleanup_expired(self):
        """清理過期檔案"""
        now = datetime.now()
        cleaned = []

        for filename, downloaded_at in list(self.download_times.items()):
            if now - downloaded_at > timedelta(hours=self.expire_hours):
                filepath = self.download_path / filename
                if filepath.exists():
                    filepath.unlink()
                    cleaned.append(filename)
                del self.download_times[filename]

        return cleaned

    async def cleanup_orphaned(self, max_age_hours: int = 24):
        """清理孤立檔案（未被下載但超過時間的）"""
        now = datetime.now()
        cleaned = []

        for filepath in self.download_path.iterdir():
            if not filepath.is_file():
                continue
            if filepath.suffix == '.gitkeep':
                continue
            if filepath.name in self.download_times:
                continue  # 已被追蹤的跳過

            file_age = now - datetime.fromtimestamp(filepath.stat().st_mtime)
            if file_age > timedelta(hours=max_age_hours):
                filepath.unlink()
                cleaned.append(filepath.name)

        return cleaned
```

**修改 API**：

```python
@router.get("/download-file/{filename}")
async def download_file(filename: str):
    # ... 原有邏輯 ...

    # 標記檔案已被下載
    file_lifecycle.mark_downloaded(filename)

    return FileResponse(filepath, filename=filename)
```

---

### 3.3 磁碟空間保護

**修改檔案**：`services/downloader.py`

```python
import shutil

class DiskProtection:
    """磁碟空間保護"""

    def __init__(self, download_path: Path, max_gb: float = 50):
        self.download_path = download_path
        self.max_bytes = max_gb * 1024 * 1024 * 1024
        self.warning_threshold = 0.9  # 90% 警告

    def get_usage(self) -> dict:
        """取得磁碟使用狀況"""
        total_size = sum(
            f.stat().st_size
            for f in self.download_path.iterdir()
            if f.is_file()
        )
        return {
            "used_bytes": total_size,
            "used_gb": total_size / (1024 * 1024 * 1024),
            "max_gb": self.max_bytes / (1024 * 1024 * 1024),
            "usage_percent": (total_size / self.max_bytes) * 100 if self.max_bytes else 0
        }

    def is_space_available(self, required_bytes: int = 0) -> bool:
        """檢查是否有足夠空間"""
        usage = self.get_usage()
        return (usage["used_bytes"] + required_bytes) < self.max_bytes

    def is_warning(self) -> bool:
        """是否達到警告閾值"""
        usage = self.get_usage()
        return usage["usage_percent"] >= (self.warning_threshold * 100)

    async def emergency_cleanup(self, target_free_percent: float = 0.3):
        """緊急清理：刪除最舊的檔案直到達到目標空間"""
        files = sorted(
            [f for f in self.download_path.iterdir() if f.is_file() and f.suffix != '.gitkeep'],
            key=lambda f: f.stat().st_mtime
        )

        target_bytes = self.max_bytes * (1 - target_free_percent)
        current_size = self.get_usage()["used_bytes"]
        deleted = []

        for filepath in files:
            if current_size <= target_bytes:
                break
            file_size = filepath.stat().st_size
            filepath.unlink()
            current_size -= file_size
            deleted.append(filepath.name)

        return deleted
```

**修改 API**：

```python
@router.post("/download")
async def download(req: DownloadRequest):
    # 檢查磁碟空間
    if not disk_protection.is_space_available():
        # 嘗試緊急清理
        await disk_protection.emergency_cleanup()
        if not disk_protection.is_space_available():
            raise HTTPException(503, "伺服器儲存空間不足，請稍後再試")

    # ... 原有邏輯
```

---

## API 變更摘要

### 新增端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/queue-stats` | GET | 取得佇列狀態 |

### 修改回應格式

**`/api/status/{task_id}` 新增欄位：**

```json
{
    "status": "queued | retrying | downloading | processing | completed | failed",
    "queue_position": 3,
    "retry_count": 1,
    "message": "排隊中（第 3 位）"
}
```

### 新增 Header

| Header | 說明 |
|--------|------|
| `X-API-Token` | API 認證 Token（選用） |

### 新增錯誤碼

| 狀態碼 | 說明 |
|--------|------|
| 400 | 無效的 YouTube URL |
| 401 | 無效的 API Token |
| 429 | 請求過於頻繁 |
| 503 | 伺服器儲存空間不足 |

---

## 測試清單

### Phase 1 測試

- [ ] Rate Limit：連續發 11 次下載請求，第 11 次應返回 429
- [ ] URL 驗證：發送非 YouTube URL，應返回 400
- [ ] 佇列：同時發 5 個下載請求，應只有 3 個在執行，2 個排隊

### Phase 2 測試

- [ ] 排隊顯示：前端正確顯示「排隊中（第 N 位）」
- [ ] 重試：模擬網路錯誤，確認自動重試
- [ ] 狀態流轉：queued → downloading → processing → completed

### Phase 3 測試

- [ ] Token：未帶 Token 時返回 401（如果啟用認證）
- [ ] 檔案清理：下載 2 小時後檔案自動刪除
- [ ] 磁碟保護：達到容量上限時拒絕新下載

---

## 部署注意事項

1. **安裝新依賴**：
   ```bash
   pip install slowapi python-dotenv
   ```

2. **建立 .env 檔案**（選用）：
   ```
   API_TOKEN=your-secret-token
   ENABLE_AUTH=false
   MAX_CONCURRENT_DOWNLOADS=3
   MAX_STORAGE_GB=50
   ```

3. **更新 requirements.txt**：
   ```
   slowapi>=0.1.9
   python-dotenv>=1.0.0
   ```

4. **前端腳本更新**：
   使用者需要更新 Tampermonkey 腳本以支援新狀態

---

## 下一步行動

準備好開始實作了嗎？建議順序：

1. **先做 Phase 1.1 Rate Limiting**（最簡單，效果最大）
2. **再做 Phase 1.3 佇列**（核心功能）
3. **最後做 Phase 1.2 URL 驗證**（簡單收尾）

告訴我要從哪個開始，我就直接改 code！
