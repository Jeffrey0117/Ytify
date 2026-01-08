# ytify

YouTube 影片下載工具 - 在 YouTube 網頁上一鍵下載影片

## 功能

- 一鍵下載 YouTube 影片
- 支援多種畫質 (最佳/1080p/720p/480p)
- 支援僅下載音訊
- 即時下載進度
- 下載完成自動清理伺服器暫存
- Supervisor 守護進程支援

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
# 安裝 git 和依賴
sudo apt install git python3 python3-pip ffmpeg

# 下載專案
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify

# 啟動服務
chmod +x run.sh && ./run.sh
```

### Mac

```bash
brew install python3 ffmpeg
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
chmod +x run.sh && ./run.sh
```

---

## 啟動方式

| 模式 | Windows | Linux/Mac | 說明 |
|------|---------|-----------|------|
| 前台 | `run.bat` | `./run.sh` | 直接啟動，關閉視窗停止 |
| 背景 | `run-daemon.bat` | `./run-daemon.sh start` | Supervisor 守護進程 |

### 守護進程指令 (Supervisor)

```bash
# Linux/Mac
./run-daemon.sh start    # 啟動
./run-daemon.sh stop     # 停止
./run-daemon.sh restart  # 重啟
./run-daemon.sh status   # 狀態
./run-daemon.sh logs     # 日誌

# Windows
run-daemon.bat           # 互動式選單
```

---

## 使用方式

**網頁版：** http://localhost:8765/download

**Tampermonkey（可選）：**
1. 安裝 [Tampermonkey](https://www.tampermonkey.net/)
2. 開啟 `scripts/ytify.user.js`，複製內容到新腳本
3. 在 YouTube 影片頁點擊「下載」按鈕

---

## 進階：遠端存取 (Cloudflare Tunnel)

### Windows

```bash
winget install Cloudflare.cloudflared
cloudflared tunnel login
cloudflared tunnel create ytify
cloudflared tunnel route dns ytify ytify.your-domain.com

# 啟動
start-all.bat
```

### Linux

```bash
# 安裝 cloudflared
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install cloudflared

# 設定
cloudflared tunnel login
cloudflared tunnel create ytify
cloudflared tunnel route dns ytify ytify.your-domain.com

# 啟動
./run-daemon.sh start
cloudflared tunnel run ytify
```

---

## Docker 部署

```bash
docker-compose up -d

# 或
docker run -d --name ytify -p 8765:8765 ghcr.io/jeffrey0117/ytify:latest
```

---

## 專案結構

```
ytify/
├── run.bat / run.sh         # 前台啟動
├── run-daemon.bat / .sh     # 背景啟動 (Supervisor)
├── start-all.bat            # Windows + Tunnel
├── supervisord.conf         # Supervisor 配置
├── main.py                  # API 主程式
├── scripts/ytify.user.js    # Tampermonkey 腳本
├── static/                  # 網頁前端
└── downloads/               # 暫存資料夾
```

---

## 網頁介面

| 頁面 | 說明 |
|------|------|
| `/home` | 首頁 |
| `/download` | 網頁版下載介面 |
| `/history` | 下載歷史 |
| `/files` | 檔案管理 |

---

## 常見問題

**下載的影片沒有聲音？**
→ Windows: `winget install FFmpeg`
→ Ubuntu: `sudo apt install ffmpeg`

**腳本沒反應？**
→ 確認 ytify 服務在運行，檢查 F12 Console

---

## License

MIT
