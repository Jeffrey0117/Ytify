# ytify

YouTube 影片下載 API 服務 + Tampermonkey 腳本

在 YouTube 網頁上一鍵下載影片，透過本地或遠端 API 服務完成下載。

## 功能

- 支援多種畫質 (最佳/1080p/720p/480p)
- 支援僅下載音訊 (MP3)
- 即時下載進度顯示
- Tampermonkey 腳本一鍵操作
- 支援 Cloudflare Tunnel 遠端存取
- 自動清理機制（下載後刪除 Server 檔案）

---

## 快速開始（本機使用）

### 1. 安裝依賴

```bash
cd ytify
pip install -r requirements.txt
```

### 2. 啟動服務

```bash
python main.py
# 或雙擊 start.bat
```

服務會在 `http://localhost:8765` 啟動

### 3. 安裝 Tampermonkey 腳本

1. 安裝 [Tampermonkey](https://www.tampermonkey.net/) 瀏覽器擴充套件
2. 點擊 Tampermonkey 圖示 → 建立新腳本
3. 複製 `scripts/ytify.user.js` 的內容貼上
4. 儲存腳本

### 4. 使用

1. 開啟任意 YouTube 影片頁面
2. 點擊右下角紅色「下載」按鈕
3. 選擇畫質，等待下載完成
4. 檔案會自動下載到你的電腦

---

## 遠端 Server 部署（Cloudflare Tunnel）

讓你可以在任何地方使用，透過遠端 Server 下載 YouTube 影片。

### Server 端設定

```powershell
# 1. Clone 專案
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify

# 2. 執行部署腳本（自動安裝依賴 + cloudflared）
powershell -ExecutionPolicy Bypass -File server-setup.ps1

# 3. 啟動（含 Tunnel）
.\start-with-tunnel.bat
# 或
powershell -ExecutionPolicy Bypass -File start-with-tunnel.ps1
```

啟動後會顯示類似這樣的網址：
```
https://xxxx-xxxx-xxxx.trycloudflare.com
```

### 使用者端設定

修改 Tampermonkey 腳本中的 `API_BASE`：

```javascript
const CONFIG = {
    API_BASE: 'https://xxxx-xxxx-xxxx.trycloudflare.com',  // ← 改成你的 Tunnel 網址
    ...
};
```

同時加上 `@connect`：

```javascript
// @connect      *.trycloudflare.com
```

---

## 專案結構

```
ytify/
├── main.py                  # FastAPI 入口
├── requirements.txt         # Python 依賴
├── start.bat                # 本地啟動
├── start-with-tunnel.bat    # 含 Tunnel 啟動 (Windows)
├── start-with-tunnel.ps1    # 含 Tunnel 啟動 (PowerShell)
├── server-setup.ps1         # Server 部署腳本
├── api/
│   └── routes.py            # API 路由
├── services/
│   └── downloader.py        # yt-dlp 下載邏輯
├── scripts/
│   └── ytify.user.js        # Tampermonkey 腳本
└── downloads/               # 下載檔案暫存
```

---

## API 文件

| 端點 | 方法 | 說明 |
|------|------|------|
| `/health` | GET | 健康檢查 |
| `/api/info` | POST | 取得影片資訊 |
| `/api/download` | POST | 開始下載 |
| `/api/status/{task_id}` | GET | 查詢下載狀態 |
| `/api/download-file/{filename}` | GET | 下載檔案到使用者電腦 |
| `/api/files` | GET | 列出已下載檔案 |
| `/api/files/{filename}` | DELETE | 刪除檔案 |
| `/api/history` | GET | 取得下載歷史 |

### 範例

**取得影片資訊：**
```bash
curl -X POST http://localhost:8765/api/info \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=xxxxx"}'
```

**開始下載：**
```bash
curl -X POST http://localhost:8765/api/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=xxxxx", "format": "720p", "audio_only": false}'
```

---

## 自動清理機制

| 機制 | 時機 | 說明 |
|------|------|------|
| 即時清理 | 使用者下載完成後 | 檔案串流完成後自動刪除 |
| 定時清理 | 每小時 | 刪除超過 24 小時的舊檔案 |

---

## 注意事項

- 需要安裝 [FFmpeg](https://ffmpeg.org/) 才能合併影片和音訊
  - Windows: `winget install FFmpeg`
  - Mac: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`
- 服務預設監聽 `0.0.0.0:8765`
- Cloudflare Tunnel 的網址每次啟動會變，需重新複製

---

## License

MIT
