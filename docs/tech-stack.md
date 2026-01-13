# Ytify 技術筆記

## 專案概覽

| 項目 | 說明 |
|------|------|
| 類型 | 自架 YouTube 下載伺服器 |
| 語言 | Python (後端) + JavaScript (前端) |
| 代碼量 | ~9,400 行 |

---

## 1. 後端技術

### Web 框架
| 技術 | 版本 | 用途 |
|------|------|------|
| **FastAPI** | ≥0.104.0 | 非同步 Web 框架，自動產生 API 文檔 |
| **Uvicorn** | ≥0.24.0 | ASGI 伺服器 |
| **Pydantic** | ≥2.0.0 | 請求/回應資料驗證 |

### 核心功能
| 技術 | 用途 |
|------|------|
| **yt-dlp** | YouTube 下載核心，支援多格式 |
| **slowapi** | API 限流中間件 (基於 IP) |
| **aiohttp** | 非同步 HTTP 客戶端 |
| **supervisor** | 進程監控與自動重啟 |

### 學習重點
```python
# FastAPI 非同步路由
@router.post("/download")
@limiter.limit("10/minute")  # Rate Limit 裝飾器
async def start_download(request: Request, req: DownloadRequest):
    ...

# 生命週期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時初始化
    cleanup_task = asyncio.create_task(cleanup_old_files())
    yield
    # 關閉時清理
    cleanup_task.cancel()
```

---

## 2. 前端技術

### 技術選型
- **純 HTML/CSS/JavaScript**（無框架）
- **ES6+ 語法**：async/await、Fetch API、Classes
- **WebSocket**：實時進度推送

### 頁面結構
| 頁面 | 功能 |
|------|------|
| index.html | 首頁 |
| download.html | 單影片下載 |
| playlist.html | 播放清單下載 |
| history.html | 下載歷史 |
| files.html | 檔案管理 |
| dashboard.html | 系統監控 |
| admin.html | 用戶管理 |

### Tampermonkey 腳本
```javascript
// ytify.user.js - 在 YouTube 頁面注入下載按鈕
// @match *://www.youtube.com/*
// 使用 GM_xmlhttpRequest 跨域請求
```

---

## 3. 資料庫

### SQLite3
輕量級檔案資料庫，無需獨立伺服器。

| 資料庫 | 用途 |
|--------|------|
| data/history.db | 下載歷史 |
| data/auth.db | 用戶認證 |
| data/monitor.db | 監控日誌 |

### 表結構設計
```sql
-- 下載歷史（多租戶隔離）
CREATE TABLE download_history (
    task_id TEXT UNIQUE,
    video_id TEXT,
    title TEXT,
    status TEXT,
    client_ip TEXT,      -- IP 隔離
    session_id TEXT,     -- Session 隔離
    user_id INTEGER,     -- 用戶隔離
    ...
);

-- 索引優化
CREATE INDEX idx_session_id ON download_history(session_id);
```

---

## 4. 部署技術

### Docker
```dockerfile
# 多階段構建
FROM python:3.11-slim
RUN apt-get install ffmpeg  # 影音處理
```

### Docker Compose
```yaml
services:
  ytify:
    ports: ["8765:8765"]
    volumes:
      - ./downloads:/app/downloads
      - ./data:/app/data

  watchtower:  # 自動更新
    command: --interval 300
```

### Cloudflare Tunnel
```yaml
# 穿透 NAT/防火牆，無需公網 IP
tunnel: ytify
ingress:
  - hostname: ytify.example.com
    service: http://localhost:8765
```

---

## 5. 設計模式

### 非同步任務佇列
```python
# services/queue.py
class TaskQueue:
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent
        self.queue = []

    async def submit(self, task_id, func, *args):
        # 控制併發數量
```

### WebSocket 事件推送
```python
# services/websocket_manager.py
class ConnectionManager:
    async def broadcast(self, task_id, message):
        # 向訂閱者推送進度
```

### 中間件鏈
```python
# main.py
app.add_middleware(CORSMiddleware, ...)      # 跨域
app.add_middleware(SessionMiddleware)         # Session
app.state.limiter = limiter                   # Rate Limit
```

### 多租戶隔離
```python
# 查詢優先級: user_id > session_id > client_ip
def list(self, session_id=None, client_ip=None, user_id=None):
    if user_id:
        conditions.append("user_id = ?")
    elif session_id:
        conditions.append("session_id = ?")
    elif client_ip:
        conditions.append("client_ip = ?")
```

---

## 6. API 設計

### RESTful 路由
```
POST /api/download          下載影片
GET  /api/status/{task_id}  查詢狀態
GET  /api/history           歷史記錄
DELETE /api/task/{task_id}  取消任務

WebSocket /ws/progress/{task_id}  實時進度
```

### Rate Limit 配置
| 端點 | 限制 |
|------|------|
| /api/info | 30/分鐘 |
| /api/download | 10/分鐘 |
| /api/playlist/download | 5/分鐘 |
| /api/ytdlp/update | 2/小時 |

---

## 7. 安全機制

| 機制 | 實作 |
|------|------|
| CORS | 允許 Tampermonkey 跨域 |
| Rate Limit | slowapi 基於 IP |
| Session 隔離 | Cookie + IP 識別 |
| 密碼雜湊 | hashlib |
| 路徑驗證 | 防目錄遍歷 |

---

## 8. 效能優化

| 優化項 | 方式 |
|--------|------|
| 併發控制 | 最多 3 個同時下載 |
| 非同步 I/O | asyncio + aiohttp |
| 版本快取 | yt-dlp 檢查快取 10 分鐘 |
| 資料庫索引 | 多欄位索引加速查詢 |
| 自動清理 | 24 小時過期檔案刪除 |

---

## 技術棧總覽

```
┌─────────────────────────────────────┐
│         Cloudflare Tunnel           │  遠端訪問
├─────────────────────────────────────┤
│      Docker + Docker Compose        │  容器化部署
├─────────────────────────────────────┤
│    FastAPI + Uvicorn (ASGI)         │  Web 框架
├─────────────────────────────────────┤
│  ├─ routes.py      API 路由         │
│  ├─ downloader.py  下載核心         │
│  ├─ queue.py       任務佇列         │
│  ├─ websocket.py   實時推送         │
│  └─ session.py     會話管理         │
├─────────────────────────────────────┤
│           SQLite3                   │  資料持久化
├─────────────────────────────────────┤
│    HTML/CSS/JS + Tampermonkey       │  前端 UI
└─────────────────────────────────────┘
```

---

## 可延伸學習

1. **FastAPI 進階**：Dependency Injection、Background Tasks
2. **WebSocket**：雙向通訊、心跳機制
3. **Docker**：多階段構建、健康檢查
4. **SQLite**：索引優化、WAL 模式
5. **asyncio**：事件循環、併發控制
