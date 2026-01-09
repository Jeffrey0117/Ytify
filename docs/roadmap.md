# ytify 功能路線圖

> 最後更新：2025-01-09
> 版本：1.0.0

---

## 目錄

- [現狀總覽](#現狀總覽)
- [短期功能 (1-2 週)](#短期功能-1-2-週)
- [中期功能 (1-2 月)](#中期功能-1-2-月)
- [長期願景](#長期願景)
- [維護計畫](#維護計畫)
- [技術債清理](#技術債清理)
- [效能優化方向](#效能優化方向)
- [優先序總覽](#優先序總覽)

---

## 現狀總覽

### 技術架構

| 層級 | 技術 |
|------|------|
| 後端框架 | FastAPI + Uvicorn |
| 下載引擎 | yt-dlp |
| 任務管理 | 自建 TaskQueue (asyncio) |
| 限流 | slowapi |
| 前端 | 純 HTML/CSS/JS (復古終端風格) |
| 瀏覽器擴充 | Tampermonkey UserScript |
| 容器化 | Docker + Docker Compose |
| 遠端存取 | Cloudflare Tunnel |
| 背景服務 | Supervisor |

### 已實現功能

- [x] YouTube 影片下載 (最佳/1080p/720p/480p)
- [x] 音訊下載 (AAC 格式)
- [x] 網頁介面 (/download, /history, /files)
- [x] Tampermonkey 一鍵下載腳本
- [x] 任務佇列 (最多 3 並行)
- [x] Rate Limiting (30次/分鐘 info, 10次/分鐘 download)
- [x] 自動清理 (24 小時過期檔案)
- [x] 代理池支援 (含自動壞代理檢測)
- [x] Cookies 繞過機制
- [x] Docker 部署
- [x] Cloudflare Tunnel 整合
- [x] Supervisor 背景執行

---

## 短期功能 (1-2 週)

### P0 - 立即處理

#### 1. yt-dlp 版本自動更新機制
**問題**：YouTube 經常更新，導致 yt-dlp 失效
**方案**：
```python
# 新增 /api/update-ytdlp endpoint
@router.post("/update-ytdlp")
async def update_ytdlp():
    # pip install -U yt-dlp
    pass

# 或定時自動檢查更新
async def auto_update_ytdlp():
    # 每週檢查一次新版本
    pass
```
**工時**：2-3 天

#### 2. 下載進度 WebSocket 推送
**問題**：目前用 polling，效率低且延遲高
**方案**：
```python
from fastapi import WebSocket

@router.websocket("/ws/progress/{task_id}")
async def progress_websocket(websocket: WebSocket, task_id: str):
    await websocket.accept()
    while task_active:
        progress = get_progress(task_id)
        await websocket.send_json(progress)
        await asyncio.sleep(0.5)
```
**工時**：3-4 天

#### 3. 下載錯誤分類與重試策略
**問題**：錯誤訊息不夠明確，重試邏輯單一
**方案**：
```python
class DownloadError(Enum):
    RATE_LIMITED = "rate_limited"      # 等待後重試
    GEO_BLOCKED = "geo_blocked"        # 需要代理
    PRIVATE_VIDEO = "private_video"    # 無法下載
    NETWORK_ERROR = "network_error"    # 立即重試
    FORMAT_ERROR = "format_error"      # 降級畫質
```
**工時**：2 天

### P1 - 本週完成

#### 4. 播放清單批次下載
**需求**：支援下載整個 YouTube 播放清單
**方案**：
```python
class PlaylistDownloadRequest(BaseModel):
    url: str
    format: str = "720p"
    max_videos: int = 50  # 限制數量

@router.post("/api/playlist")
async def download_playlist(req: PlaylistDownloadRequest):
    # 解析播放清單，建立多個任務
    pass
```
**工時**：3-4 天

#### 5. 下載任務取消功能
**需求**：允許使用者取消進行中的下載
**方案**：
```python
@router.delete("/api/task/{task_id}")
async def cancel_task(task_id: str):
    # 終止下載進程
    # 清理暫存檔案
    pass
```
**工時**：2 天

#### 6. 系統狀態儀表板
**需求**：顯示佇列狀態、磁碟空間、CPU 使用率
**方案**：
- 新增 `/status` 頁面
- 顯示：執行中任務、佇列長度、磁碟用量、最近錯誤
**工時**：2 天

---

## 中期功能 (1-2 月)

### 功能增強

#### 1. 多平台支援
**目標**：支援更多影音平台
```python
SUPPORTED_PLATFORMS = {
    "youtube": ["youtube.com", "youtu.be"],
    "bilibili": ["bilibili.com"],
    "twitter": ["twitter.com", "x.com"],
    "tiktok": ["tiktok.com"],
    "instagram": ["instagram.com"],
}
```
**考量**：
- yt-dlp 已支援 1000+ 網站
- 主要工作在 URL 驗證和 UI 調整
- 注意各平台的特殊限制

**工時**：1-2 週

#### 2. 使用者認證系統
**目標**：保護私人部署的服務
```python
# 簡易 API Key 認證
@router.post("/api/download")
async def download(req: DownloadRequest, api_key: str = Header(...)):
    if not verify_api_key(api_key):
        raise HTTPException(401, "Invalid API key")
```
**功能**：
- API Key 認證
- 可選的密碼保護
- 單一使用者 / 多使用者模式

**工時**：1 週

#### 3. 下載排程功能
**目標**：設定定時下載
```python
class ScheduledTask(BaseModel):
    url: str
    cron: str  # "0 2 * * *" 每天凌晨 2 點
    format: str
    enabled: bool

# 使用 APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler()
```
**工時**：1 週

#### 4. 訂閱頻道自動下載
**目標**：追蹤頻道並自動下載新影片
```python
class ChannelSubscription(BaseModel):
    channel_url: str
    format: str
    check_interval: int = 3600  # 每小時檢查
    max_videos_per_check: int = 5
```
**工時**：2 週

#### 5. 進階格式選項
**目標**：更細緻的格式控制
```python
class AdvancedDownloadRequest(BaseModel):
    url: str
    video_format: str = "bestvideo"
    audio_format: str = "bestaudio"
    merge_format: str = "mp4"
    video_codec: Optional[str] = None  # h264, h265, av1
    audio_codec: Optional[str] = None  # aac, opus
    subtitle: bool = False
    subtitle_lang: List[str] = ["zh-TW", "en"]
```
**工時**：1 週

### UI/UX 改進

#### 6. 響應式設計重構
**目標**：優化行動裝置體驗
- 觸控友善的按鈕
- 自適應佈局
- PWA 支援 (可加到主畫面)

**工時**：1 週

#### 7. 深色/淺色主題切換
**目標**：支援主題偏好
```css
:root {
    --bg-primary: #0a1628;
    --text-primary: #ffffff;
}
[data-theme="light"] {
    --bg-primary: #f5f5f5;
    --text-primary: #333333;
}
```
**工時**：3 天

#### 8. 通知系統
**目標**：下載完成通知
- 瀏覽器推送通知
- 可選的 Telegram/Discord webhook
```python
async def send_notification(task: dict):
    if settings.telegram_bot_token:
        await send_telegram(f"下載完成: {task['title']}")
```
**工時**：1 週

---

## 長期願景

### 架構演進

#### 1. 微服務化架構
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   API 閘道   │────→│  下載服務 x3  │────→│  儲存服務    │
│   (FastAPI)  │     │  (Workers)   │     │  (MinIO/S3)  │
└──────────────┘     └──────────────┘     └──────────────┘
        │                   │
        ↓                   ↓
┌──────────────┐     ┌──────────────┐
│   訊息佇列   │     │   Redis      │
│   (RabbitMQ) │     │   (Cache)    │
└──────────────┘     └──────────────┘
```

#### 2. 分散式下載
- 多 Worker 節點
- 負載均衡
- 故障轉移
- 地理分散 (不同地區節點繞過地區限制)

#### 3. 企業級功能
- LDAP/SSO 整合
- 完整審計日誌
- 用量配額管理
- 多租戶支援

### 進階功能

#### 4. AI 輔助功能
- 影片摘要生成
- 自動字幕翻譯
- 內容分類標籤
- 智慧推薦

#### 5. 媒體處理
- 影片裁切/合併
- 音訊提取與編輯
- 縮圖自動生成
- 浮水印移除

#### 6. 社群功能
- 分享下載連結
- 公開收藏庫
- 評論系統

---

## 維護計畫

### 定期維護任務

| 週期 | 任務 | 自動化程度 |
|------|------|-----------|
| 每日 | 檢查服務健康狀態 | 自動 (healthcheck) |
| 每日 | 清理過期檔案 | 自動 (已實現) |
| 每週 | 更新 yt-dlp | 半自動 (需實現) |
| 每月 | 檢查 Python 依賴更新 | 手動 |
| 每月 | 審視錯誤日誌 | 手動 |
| 每季 | 安全性審計 | 手動 |

### yt-dlp 更新策略

```bash
# 自動更新腳本 (建議加入 cron)
#!/bin/bash
pip install -U yt-dlp
# 測試下載功能
python -c "import yt_dlp; yt_dlp.YoutubeDL().download(['https://www.youtube.com/watch?v=dQw4w9WgXcQ'])" && \
    echo "Update successful" || \
    echo "Update failed, rolling back" && pip install yt-dlp==<previous_version>
```

**建議更新頻率**：每週一次或發現下載失敗時

### 安全性維護

#### 1. 依賴更新
```bash
# 檢查安全漏洞
pip install safety
safety check -r requirements.txt

# 更新依賴
pip install pip-tools
pip-compile --upgrade requirements.in
```

#### 2. 安全性檢查清單

| 項目 | 說明 | 狀態 |
|------|------|------|
| CORS 設定 | 目前允許所有來源 | 需評估 |
| Rate Limiting | 已實現 | OK |
| 輸入驗證 | YouTube URL 驗證 | OK |
| 路徑遍歷防護 | 已實現 | OK |
| API 認證 | 無 | 待實現 |
| HTTPS | 透過 Cloudflare | OK |
| SQL Injection | 無資料庫 | N/A |

#### 3. 安全性建議

1. **CORS 限縮**：生產環境應限制允許的來源
```python
# 建議
allow_origins=["https://youtube.com", "https://www.youtube.com"]
```

2. **新增 API 認證**：防止未授權存取
```python
# 簡易方案
API_KEY = os.getenv("YTIFY_API_KEY")
```

3. **下載目錄隔離**：確保無法存取系統檔案
4. **日誌記錄**：記錄所有下載請求以供審計

### 備份策略

```bash
# 備份設定與歷史
#!/bin/bash
BACKUP_DIR="/backup/ytify/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 複製設定檔
cp cloudflared-config.yml $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/

# 匯出下載歷史 (如果有持久化)
# 目前歷史存在記憶體，重啟會消失
```

---

## 技術債清理

### 高優先序

#### 1. 下載歷史持久化
**現況**：歷史記錄存在記憶體，重啟後消失
**方案**：
```python
# 方案 A: SQLite
import sqlite3
history_db = sqlite3.connect("history.db")

# 方案 B: JSON 檔案
import json
HISTORY_FILE = Path("data/history.json")

def save_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump(self.history, f)
```
**建議**：使用 SQLite，方便未來擴充
**工時**：2 天

#### 2. 設定檔外部化
**現況**：設定值硬編碼在程式碼中
**方案**：
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    download_path: Path = Path("./downloads")
    max_concurrent: int = 3
    file_max_age_hours: int = 24
    rate_limit_info: str = "30/minute"
    rate_limit_download: str = "10/minute"

    class Config:
        env_file = ".env"

settings = Settings()
```
**工時**：1 天

#### 3. 日誌系統標準化
**現況**：使用 print() 輸出
**方案**：
```python
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        RotatingFileHandler("logs/ytify.log", maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
```
**工時**：0.5 天

### 中優先序

#### 4. 單元測試覆蓋
**現況**：無測試
**目標**：核心功能 80% 覆蓋率
```python
# tests/test_downloader.py
import pytest
from services.downloader import is_valid_youtube_url, clean_youtube_url

def test_valid_youtube_url():
    assert is_valid_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert is_valid_youtube_url("https://youtu.be/dQw4w9WgXcQ")
    assert not is_valid_youtube_url("https://example.com")

def test_clean_youtube_url():
    assert clean_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=xxx") == \
           "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```
**工時**：3-5 天

#### 5. API 文件完善
**現況**：僅有 FastAPI 自動生成的 Swagger
**方案**：
- 增加 API 描述和範例
- 撰寫使用教學
```python
@router.post("/info",
    summary="取得影片資訊",
    description="解析 YouTube 影片 URL，返回標題、時長、縮圖等資訊",
    response_description="影片資訊物件")
async def get_video_info(req: InfoRequest):
    """
    ## 範例請求
    ```json
    {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    ```
    """
    pass
```
**工時**：1 天

#### 6. 錯誤處理統一
**現況**：錯誤回傳格式不一致
**方案**：
```python
class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "code": exc.code,
            "message": exc.message
        }
    )
```
**工時**：1 天

### 低優先序

#### 7. 程式碼重構
- 拆分過長的函數 (如 `_sync_execute_download`)
- 引入 Repository 模式管理資料
- 使用 Dependency Injection

#### 8. 型別標註完善
```python
# 增加完整型別標註
async def execute_task(self, task_id: str) -> dict[str, Any]:
    ...
```

---

## 效能優化方向

### 短期優化

#### 1. 快取影片資訊
**問題**：重複查詢相同影片資訊
**方案**：
```python
from functools import lru_cache
from cachetools import TTLCache

# 10 分鐘快取，最多 100 筆
info_cache = TTLCache(maxsize=100, ttl=600)

async def get_video_info(self, url: str) -> dict:
    cache_key = extract_video_id(url)
    if cache_key in info_cache:
        return info_cache[cache_key]

    info = await self._fetch_info(url)
    info_cache[cache_key] = info
    return info
```
**效果**：減少 YouTube API 請求，加快重複查詢
**工時**：0.5 天

#### 2. 下載目錄優化
**問題**：大量檔案在同一目錄會拖慢列表
**方案**：
```python
# 按日期分目錄
def get_download_path(self) -> Path:
    today = datetime.now().strftime("%Y-%m/%d")
    path = self.base_path / today
    path.mkdir(parents=True, exist_ok=True)
    return path
```
**工時**：0.5 天

#### 3. 串流下載
**問題**：大檔案下載到伺服器後再傳給使用者，佔用大量空間
**方案**：研究 yt-dlp 的串流輸出功能，直接串流給使用者
```python
# 概念 (需要進一步研究可行性)
from fastapi.responses import StreamingResponse

async def stream_download():
    # 使用 yt-dlp stdout 直接串流
    process = await asyncio.create_subprocess_exec(
        "yt-dlp", "-o", "-", url,
        stdout=asyncio.subprocess.PIPE
    )
    return StreamingResponse(process.stdout)
```
**工時**：3-5 天 (需研究)

### 中期優化

#### 4. 並行下載同一影片
**場景**：多人同時下載同一影片
**方案**：
```python
# 下載鎖 + 共享結果
download_locks: dict[str, asyncio.Lock] = {}
download_results: dict[str, Future] = {}

async def download_with_dedup(video_id: str):
    if video_id in download_results:
        return await download_results[video_id]

    async with download_locks.setdefault(video_id, asyncio.Lock()):
        if video_id not in download_results:
            download_results[video_id] = asyncio.create_task(do_download())
        return await download_results[video_id]
```
**效果**：避免重複下載相同影片
**工時**：2 天

#### 5. 下載優先序佇列
**場景**：VIP 使用者或小檔案優先
**方案**：
```python
from queue import PriorityQueue

class PriorityTask:
    def __init__(self, priority: int, task_id: str):
        self.priority = priority
        self.task_id = task_id

    def __lt__(self, other):
        return self.priority < other.priority

priority_queue = PriorityQueue()
```
**工時**：1 天

#### 6. 靜態資源 CDN
**問題**：靜態檔案 (HTML/CSS/JS) 每次都從伺服器讀取
**方案**：
- 使用 Cloudflare 快取靜態資源
- 設定適當的 Cache-Control header
```python
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 或者用 nginx 反向代理
```
**工時**：1 天

### 監控與可觀測性

#### 7. 效能指標收集
```python
from prometheus_client import Counter, Histogram, generate_latest

download_counter = Counter('ytify_downloads_total', 'Total downloads')
download_duration = Histogram('ytify_download_duration_seconds', 'Download duration')

@router.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### 8. 健康檢查增強
```python
@router.get("/health/detailed")
async def detailed_health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "yt_dlp_version": yt_dlp.version.__version__,
        "queue_stats": download_queue.get_stats(),
        "disk_usage": get_disk_usage(),
        "uptime": get_uptime(),
    }
```

---

## 優先序總覽

### Phase 1: 穩定性 (1-2 週)
| 優先序 | 任務 | 類型 | 工時 |
|--------|------|------|------|
| P0 | yt-dlp 自動更新機制 | 維護 | 2-3 天 |
| P0 | WebSocket 進度推送 | 功能 | 3-4 天 |
| P0 | 錯誤分類與重試策略 | 優化 | 2 天 |
| P1 | 任務取消功能 | 功能 | 2 天 |
| P1 | 下載歷史持久化 | 技術債 | 2 天 |

### Phase 2: 功能增強 (1-2 月)
| 優先序 | 任務 | 類型 | 工時 |
|--------|------|------|------|
| P1 | 播放清單批次下載 | 功能 | 3-4 天 |
| P1 | 系統狀態儀表板 | 功能 | 2 天 |
| P2 | 多平台支援 | 功能 | 1-2 週 |
| P2 | 使用者認證 | 功能 | 1 週 |
| P2 | 設定檔外部化 | 技術債 | 1 天 |
| P2 | 單元測試覆蓋 | 技術債 | 3-5 天 |

### Phase 3: 擴展 (長期)
| 優先序 | 任務 | 類型 | 工時 |
|--------|------|------|------|
| P3 | 訂閱頻道自動下載 | 功能 | 2 週 |
| P3 | 下載排程功能 | 功能 | 1 週 |
| P3 | 串流下載 | 優化 | 3-5 天 |
| P3 | 效能指標監控 | 維護 | 1 週 |

---

## 版本規劃

| 版本 | 目標 | 預計時間 |
|------|------|---------|
| v1.1.0 | 穩定性改善 (Phase 1) | 2 週後 |
| v1.2.0 | 播放清單 + 儀表板 | 1 個月後 |
| v1.5.0 | 多平台 + 認證 | 2 個月後 |
| v2.0.0 | 訂閱系統 + 排程 | 3-4 個月後 |

---

## 貢獻指南

### 開發環境設定
```bash
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 程式碼風格
- 使用 Python 3.11+
- 遵循 PEP 8
- 函數/類別加上 docstring
- 新功能必須有對應測試

### 提交 PR 前
1. 確保測試通過
2. 更新相關文件
3. 填寫完整的 PR 描述

---

*此路線圖會隨專案發展持續更新*
