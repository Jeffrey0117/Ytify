# ytify

自架 YouTube 下載伺服器 — 透過自己的伺服器下載 YouTube 影片

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

## 功能

- 支援多種畫質 (最佳/1080p/720p/480p)
- 支援僅下載音訊 (MP3)
- 即時下載進度顯示
- 網頁介面 + Tampermonkey 腳本
- 下載完成自動清理暫存

---

## 快速開始

### Windows

```bash
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
run.bat
```

### Ubuntu/Debian

```bash
sudo apt install git python3 python3-pip ffmpeg
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
chmod +x run.sh && ./run.sh
```

### Mac

```bash
brew install python3 ffmpeg
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
chmod +x run.sh && ./run.sh
```

### Docker（推薦，含自動更新）

```bash
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
docker-compose up -d
```

Docker 模式包含 **Watchtower 自動更新**：
- 每 5 分鐘檢查 GitHub 是否有新版本
- 自動拉取並重啟服務
- 無需手動 `git pull`

---

## 使用方式

啟動服務後，有兩種使用方式：

### 方式一：網頁介面

開啟 http://localhost:8765/download，貼上 YouTube 網址即可下載

### 方式二：Tampermonkey 腳本（推薦）

1. 安裝 [Tampermonkey](https://www.tampermonkey.net/)
2. 將 `scripts/ytify.user.js` 的內容複製到新腳本
3. 在 YouTube 影片頁面會出現「下載」按鈕

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
├── Dockerfile               # Docker 映像
└── downloads/               # 暫存資料夾
```

---

## 網頁介面

| 路徑 | 說明 |
|------|------|
| `/download` | 下載介面 |
| `/history` | 下載歷史 |
| `/files` | 檔案管理 |

---

## 常見問題

**下載的影片沒有聲音？**
→ 安裝 FFmpeg：`winget install FFmpeg` (Windows) 或 `sudo apt install ffmpeg` (Linux)

**Tampermonkey 腳本沒反應？**
→ 確認 ytify 服務在運行，開啟 F12 Console 檢查錯誤訊息

**想從手機下載？**
→ 設定 Cloudflare Tunnel 後，手機瀏覽器開啟你的網址即可使用網頁介面

---

## License

MIT
