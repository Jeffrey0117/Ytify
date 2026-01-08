# ytify 擴展性與安全性技術報告

## 目錄
1. [現況分析](#現況分析)
2. [優先級 1：100 人同時使用](#優先級-1100-人同時使用)
3. [優先級 2：惡意請求防護](#優先級-2惡意請求防護)
4. [優先級 3：使用體驗優化](#優先級-3使用體驗優化)
5. [實作建議](#實作建議)

---

## 現況分析

### 目前架構
```
使用者 → Tampermonkey 腳本 → Cloudflare Tunnel → ytify API → yt-dlp → YouTube
```

### 現有問題

| 問題 | 影響 | 嚴重度 |
|------|------|--------|
| 無任務佇列 | 同時下載過多會卡死 | 🔴 高 |
| 無速率限制 | 惡意用戶可癱瘓服務 | 🔴 高 |
| 無認證機制 | 任何人都能用 API | 🟡 中 |
| 任務無重試 | 失敗就失敗 | 🟡 中 |
| 檔案僅時間清理 | 可能佔滿磁碟 | 🟡 中 |
| 單機單進程 | 無法水平擴展 | 🟡 中 |

---

## 優先級 1：100 人同時使用

### 問題描述
目前每個下載請求都會直接執行 yt-dlp，100 人同時請求 = 100 個 yt-dlp 進程，會導致：
- CPU/記憶體爆炸
- 網路頻寬耗盡
- YouTube rate limit

### 解決方案：任務佇列系統

#### 方案 A：記憶體佇列（簡單，適合 < 50 人）

```python
# services/queue.py
import asyncio
from collections import deque

class TaskQueue:
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent
        self.running = 0
        self.queue = deque()
        self.lock = asyncio.Lock()

    async def submit(self, task_func, *args):
        """提交任務到佇列"""
        future = asyncio.Future()
        await self.queue.append((task_func, args, future))
        asyncio.create_task(self._process())
        return future

    async def _process(self):
        async with self.lock:
            if self.running >= self.max_concurrent:
                return
            if not self.queue:
                return

            self.running += 1

        task_func, args, future = self.queue.popleft()
        try:
            result = await task_func(*args)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            async with self.lock:
                self.running -= 1
            asyncio.create_task(self._process())
```

**優點：** 簡單、無額外依賴
**缺點：** 重啟後佇列消失、無法跨進程

#### 方案 B：Redis 佇列（推薦，適合 50-500 人）

```python
# 使用 Redis + RQ (Redis Queue)
from redis import Redis
from rq import Queue

redis_conn = Redis()
task_queue = Queue(connection=redis_conn)

# 提交任務
job = task_queue.enqueue(download_video, url, format)

# 查詢狀態
job.get_status()  # queued, started, finished, failed
```

**架構：**
```
API Server (接收請求)
     ↓
Redis (任務佇列)
     ↓
Worker 1, Worker 2, Worker 3 (各自處理下載)
```

**優點：**
- 任務持久化（重啟不丟失）
- 可多 worker 水平擴展
- 內建重試機制

**缺點：** 需要額外安裝 Redis

#### 方案 C：Celery（適合 500+ 人）

更完整的分散式任務系統，支援排程、監控面板等。

### 建議

| 用戶規模 | 推薦方案 | 預估成本 |
|----------|----------|----------|
| < 50 人 | 方案 A（記憶體佇列）| 0 |
| 50-500 人 | 方案 B（Redis）| Redis 雲服務 ~$5/月 |
| 500+ 人 | 方案 C（Celery）| 需要多台機器 |

---

## 優先級 2：惡意請求防護

### 威脅模型

| 攻擊類型 | 影響 | 防護方式 |
|----------|------|----------|
| 大量請求（DDoS）| 服務癱瘓 | Rate Limiting |
| 假 URL 轟炸 | 資源耗盡 | URL 驗證 + 黑名單 |
| 下載超大檔案 | 磁碟爆滿 | 檔案大小限制 |
| 盜用 API | 流量費用 | Token 認證 |

### 解決方案

#### 2.1 Rate Limiting（速率限制）

```python
# 使用 slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/download")
@limiter.limit("10/minute")  # 每分鐘最多 10 次
async def download(request: Request, ...):
    ...
```

**建議限制：**
| 端點 | 限制 | 理由 |
|------|------|------|
| `/api/info` | 30/分鐘 | 查詢資訊較輕量 |
| `/api/download` | 10/分鐘 | 下載消耗大量資源 |
| `/health` | 無限制 | 健康檢查 |

#### 2.2 Token 認證系統

**簡單方案：靜態 Token**
```python
# .env
API_TOKEN=your-secret-token-here

# main.py
from fastapi import Header, HTTPException

async def verify_token(x_api_token: str = Header(None)):
    if x_api_token != os.getenv("API_TOKEN"):
        raise HTTPException(401, "Invalid token")

@app.post("/api/download")
async def download(token: str = Depends(verify_token), ...):
    ...
```

**進階方案：用戶 Token 系統**
```python
# 每個用戶有獨立 token，可追蹤用量
tokens = {
    "user-abc-123": {"name": "User A", "quota": 100, "used": 0},
    "user-def-456": {"name": "User B", "quota": 50, "used": 0},
}
```

#### 2.3 Cloudflare 防護（免費）

在 Cloudflare Dashboard 設定：
- **Rate Limiting Rules**：每 IP 每分鐘最多 60 請求
- **Bot Fight Mode**：自動擋機器人
- **Under Attack Mode**：遭攻擊時啟用挑戰頁

#### 2.4 URL 驗證

```python
import re

def is_valid_youtube_url(url: str) -> bool:
    patterns = [
        r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]{11}',
        r'^https?://youtu\.be/[\w-]{11}',
    ]
    return any(re.match(p, url) for p in patterns)

@app.post("/api/download")
async def download(request: DownloadRequest):
    if not is_valid_youtube_url(request.url):
        raise HTTPException(400, "Invalid YouTube URL")
```

---

## 優先級 3：使用體驗優化

### 3.1 任務狀態系統

**目前狀態：**
```
pending → downloading → processing → completed
                                  ↘ failed
```

**建議增加：**
```
pending → queued → downloading → processing → completed
   ↓         ↓          ↓            ↓            ↓
 failed   failed     failed      failed     (auto cleanup)
   ↓
 retry (max 3 times)
```

**實作：**
```python
class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"        # 新增：排隊中
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"    # 新增：重試中

class Task:
    status: TaskStatus
    retry_count: int = 0
    max_retries: int = 3
    error_message: str = None
    queue_position: int = None  # 新增：顯示排隊位置
```

### 3.2 重試機制

```python
async def download_with_retry(task_id: str, url: str, format: str):
    task = tasks[task_id]

    for attempt in range(task.max_retries + 1):
        try:
            task.retry_count = attempt
            if attempt > 0:
                task.status = "retrying"
                await asyncio.sleep(2 ** attempt)  # 指數退避

            await do_download(url, format)
            task.status = "completed"
            return

        except RateLimitError:
            task.error_message = "YouTube 暫時限制，稍後重試"
            continue
        except Exception as e:
            task.error_message = str(e)
            continue

    task.status = "failed"
```

### 3.3 檔案生命週期管理

**目前：** 24 小時後刪除

**建議：**
```python
FILE_LIFECYCLE = {
    "download_complete": 0,      # 下載完成
    "user_downloaded": 1,        # 用戶已下載（開始計時）
    "expire_warning": 3600,      # 1 小時後警告
    "auto_delete": 7200,         # 2 小時後刪除
}

class FileManager:
    def mark_downloaded(self, filename: str):
        """用戶下載檔案時呼叫"""
        self.download_times[filename] = datetime.now()

    async def cleanup(self):
        """清理已下載超過 2 小時的檔案"""
        for filename, downloaded_at in self.download_times.items():
            if datetime.now() - downloaded_at > timedelta(hours=2):
                self.delete(filename)
```

**磁碟保護：**
```python
MAX_STORAGE_GB = 50

async def check_storage():
    usage = get_disk_usage()
    if usage > MAX_STORAGE_GB * 0.9:  # 90% 警戒線
        # 刪除最舊的檔案
        delete_oldest_files(count=10)
```

### 3.4 前端進度優化

```javascript
// 顯示排隊位置
if (status.status === 'queued') {
    showToast({
        title: `排隊中 #${status.queue_position}`,
        sub: `預計等待 ${status.estimated_wait} 秒`,
        progress: 'loading'
    });
}

// 顯示重試狀態
if (status.status === 'retrying') {
    showToast({
        title: `重試中 (${status.retry_count}/${status.max_retries})`,
        sub: status.error_message,
        progress: 'loading',
        state: 'warn'
    });
}
```

---

## 實作建議

### 階段 1：立即可做（1-2 天）

| 項目 | 複雜度 | 效果 |
|------|--------|------|
| 記憶體佇列（限制同時 3 個下載）| 低 | 🔴 高 |
| URL 驗證 | 低 | 🟡 中 |
| 簡單 Rate Limit | 低 | 🔴 高 |
| 磁碟空間檢查 | 低 | 🟡 中 |

### 階段 2：短期優化（1 週）

| 項目 | 複雜度 | 效果 |
|------|--------|------|
| 靜態 Token 認證 | 低 | 🟡 中 |
| 重試機制 | 中 | 🟡 中 |
| 排隊位置顯示 | 中 | 🟡 中 |
| Cloudflare 防護設定 | 低 | 🔴 高 |

### 階段 3：長期擴展（2-4 週）

| 項目 | 複雜度 | 效果 |
|------|--------|------|
| Redis 佇列 | 中 | 🔴 高 |
| 用戶 Token 系統 | 高 | 🟡 中 |
| Docker 化 | 中 | 🟡 中 |
| 多 Worker 部署 | 高 | 🔴 高 |

---

## 快速開始

如果現在只能做一件事，建議先實作 **記憶體佇列 + Rate Limit**：

```python
# 1. 安裝依賴
pip install slowapi

# 2. 修改 main.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"error": "請求過於頻繁，請稍後再試"}
    )

# 3. 加到路由
@app.post("/api/download")
@limiter.limit("10/minute")
async def download(...):
    ...
```

這樣可以在最短時間內解決最嚴重的問題。

---

## 結論

| 優先級 | 問題 | 建議方案 | 預估工時 |
|--------|------|----------|----------|
| 1 | 100 人同時使用 | 記憶體佇列 → Redis 佇列 | 4h → 1d |
| 2 | 惡意請求 | Rate Limit + Cloudflare | 2h |
| 3 | 使用體驗 | 重試機制 + 排隊顯示 | 1d |

建議先做 **Rate Limit**（2 小時內可完成），再做 **記憶體佇列**（半天），這樣就能安全地讓 50 人同時使用了。
