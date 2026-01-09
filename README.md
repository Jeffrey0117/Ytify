# ytify

自架 YouTube 下載伺服器 — 透過自己的伺服器下載 YouTube 影片

[![GitHub](https://img.shields.io/badge/GitHub-Jeffrey0117%2FYtify-blue?logo=github)](https://github.com/Jeffrey0117/Ytify)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 這是什麼？

ytify 是一個**自架式** YouTube 下載解決方案。你在自己的電腦或伺服器上架設 ytify 服務，然後透過網頁介面或瀏覽器腳本來下載影片。

### 運作原理

```
┌─────────────┐     請求下載      ┌──────────────┐     yt-dlp     ┌─────────┐
│   瀏覽器     │ ───────────────→ │  ytify 伺服器 │ ─────────────→ │ YouTube │
│ (你的電腦)   │ ←─────────────── │  (你的電腦)   │ ←───────────── │         │
└─────────────┘     回傳檔案      └──────────────┘     影片資料     └─────────┘
```

1. 你在瀏覽器點擊下載
2. ytify 伺服器收到請求，使用 yt-dlp 從 YouTube 抓取影片
3. 影片下載到伺服器後，再傳回你的瀏覽器

### 為什麼要自架？

- **隱私**：不經過第三方服務，資料不外流
- **穩定**：不受公共服務限制或關站影響
- **可控**：自訂畫質、格式、儲存位置
- **遠端**：搭配 Cloudflare Tunnel 可從任何地方使用

---

## 功能特色

### 核心功能
- 支援多種畫質 (最佳/1080p/720p/480p)
- 支援僅下載音訊 (MP3)
- 即時下載進度顯示
- 網頁介面 + Tampermonkey 腳本
- 下載完成自動清理暫存

### 進階功能
- **併發下載** - 同時下載最多 3 個影片，不用排隊等待
- **智慧重試** - 下載失敗自動降級畫質重試
- **代理支援** - 支援單一代理或代理池 API
- **播放清單** - 批次下載整個播放清單
- **即時狀態** - WebSocket 即時推送下載進度
- **優雅重啟** - 自動更新時等待任務完成才重啟

### Userscript 功能 (v10.6)
- 在 YouTube 頁面一鍵下載
- 多任務同時顯示進度
- 連線狀態即時檢測
- 離線時友善提示 + 修改伺服器位置
- Info 按鈕顯示版本與官網連結

---

## 快速開始

```bash
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
run.bat      # Windows
./run.sh     # Linux/Mac
```

執行後會出現選單：

| 選項 | 說明 | 適合 |
|------|------|------|
| **1. Docker** | 需 4GB+ RAM，自動更新 | 高規格電腦 |
| **2. Python** | 最輕量，手動更新 | 低規格/臨時使用 |
| **3. Python + 自動更新** | 輕量且自動同步 | **推薦大多數人** |

> 不確定選哪個？直接按 Enter 選 3

---

## 使用方式

啟動服務後，有兩種使用方式：

### 方式一：網頁介面

開啟 `http://localhost:8765/download`，貼上 YouTube 網址即可下載

### 方式二：Tampermonkey 腳本（推薦）

1. 安裝 [Tampermonkey](https://www.tampermonkey.net/)
2. 將 `scripts/ytify.user.js` 的內容複製到新腳本
3. 在 YouTube 影片頁面會出現「下載」按鈕

---

## 網頁介面

| 路徑 | 說明 |
|------|------|
| `/download` | 下載介面 |
| `/playlist` | 播放清單下載 |
| `/history` | 下載歷史 |
| `/files` | 檔案管理 |
| `/dashboard` | 系統狀態儀表板 |

---

## 進階設定

### 背景執行 (Supervisor)

```bash
# Linux/Mac
./run-daemon.sh start    # 啟動
./run-daemon.sh stop     # 停止
./run-daemon.sh status   # 狀態

# Windows
run-daemon.bat           # 互動式選單
```

### 遠端存取 (Cloudflare Tunnel)

讓你從外網存取家裡的 ytify 服務：

```bash
# 安裝
winget install Cloudflare.cloudflared   # Windows
# 或 sudo apt install cloudflared       # Linux

# 設定（只需做一次）
cloudflared tunnel login
cloudflared tunnel create ytify
cloudflared tunnel route dns ytify ytify.your-domain.com

# 啟動（Windows）
start-all.bat
```

設定完成後，可從 `https://ytify.your-domain.com` 存取你的服務

### 代理設定

```bash
# 設定單一代理
curl -X POST http://localhost:8765/api/proxy \
  -H "Content-Type: application/json" \
  -d '{"proxy": "http://127.0.0.1:7890"}'

# 設定代理池 API
curl -X POST http://localhost:8765/api/proxy \
  -H "Content-Type: application/json" \
  -d '{"proxy_pool_api": "http://localhost:5010/get"}'
```

---

## API 文檔

### 下載相關

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/download` | 開始下載 |
| GET | `/api/status/{task_id}` | 查詢任務狀態 |
| DELETE | `/api/task/{task_id}` | 取消任務 |
| GET | `/api/queue-stats` | 佇列統計 |
| GET | `/api/can-restart` | 檢查是否可安全重啟 |

### 播放清單

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/playlist/info` | 取得播放清單資訊 |
| POST | `/api/playlist/download` | 批次下載播放清單 |
| GET | `/api/playlist/status/{id}` | 播放清單下載進度 |

### WebSocket

| 路徑 | 說明 |
|------|------|
| `/api/ws/progress/{task_id}` | 訂閱單一任務進度 |
| `/api/ws/all` | 訂閱所有任務進度 |

---

## 專案結構

```
ytify/
├── main.py                  # API 主程式
├── api/                     # API 路由
├── services/                # 下載服務 & 任務佇列
├── static/                  # 網頁前端
├── scripts/ytify.user.js    # Tampermonkey 腳本
├── run.bat / run.sh         # 前台啟動
├── run-daemon.bat / .sh     # 背景啟動
├── auto-update.bat          # 自動更新（優雅重啟）
├── Dockerfile               # Docker 映像
└── downloads/               # 暫存資料夾
```

---

## 常見問題

**下載的影片沒有聲音？**
→ 安裝 FFmpeg：`winget install FFmpeg` (Windows) 或 `sudo apt install ffmpeg` (Linux)

**Tampermonkey 腳本沒反應？**
→ 確認 ytify 服務在運行，點擊 Info 按鈕檢查連線狀態

**想從手機下載？**
→ 設定 Cloudflare Tunnel 後，手機瀏覽器開啟你的網址即可使用網頁介面

**自動更新會中斷下載嗎？**
→ 不會！優雅重啟機制會等待所有任務完成後才重啟

---

## 版本歷史

### v10.6 (2025-01)
- 新增：併發下載支援（最多 3 個同時）
- 新增：「合併中」狀態顯示（FFmpeg 處理階段）
- 新增：優雅重啟機制（自動更新不中斷下載）
- 新增：Info 按鈕顯示版本與官網連結
- 新增：離線時可直接修改伺服器位置
- 優化：進度回調改用閉包，支援多任務獨立追蹤

### v10.5 (2025-01)
- 新增：連線狀態即時檢測
- 新增：離線友善提示 popup
- 優化：Info popup 伺服器網址動態更新

### v10.0 (2024-12)
- 新增：WebSocket 即時進度推送
- 新增：播放清單批次下載
- 新增：下載歷史持久化
- 新增：代理池支援

---

## License

MIT
