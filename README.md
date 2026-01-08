# ytify

YouTube 影片下載工具 - 在 YouTube 網頁上一鍵下載影片

## 功能

- 一鍵下載 YouTube 影片
- 支援多種畫質 (最佳/1080p/720p/480p)
- 支援僅下載音訊
- 即時下載進度
- 下載完成自動清理伺服器暫存
- PM2 守護進程支援

---

## 快速開始

### Windows

```bash
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
run.bat
```

### Ubuntu/Debian (一鍵安裝)

```bash
# 安裝 git
sudo apt install git

# 下載專案
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify

# 安裝系統依賴 (Python, FFmpeg, Node.js, PM2)
chmod +x install-deps.sh && ./install-deps.sh

# 啟動服務
chmod +x run.sh && ./run.sh
```

### Mac

```bash
# 安裝依賴
brew install python3 ffmpeg node

# 下載並啟動
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
chmod +x run.sh && ./run.sh
```

啟動腳本會自動檢查環境、安裝 Python 依賴、啟動服務。

---

## 啟動方式

| 平台 | 指令 | 說明 |
|------|------|------|
| Windows | `run.bat` | 一鍵啟動（含 PM2 守護） |
| Linux/Mac | `./run.sh` | 一鍵啟動（含 PM2 守護） |

### PM2 常用指令

```bash
pm2 status          # 查看狀態
pm2 logs ytify      # 查看日誌
pm2 restart ytify   # 重啟
pm2 stop ytify      # 停止
pm2 save && pm2 startup  # 設定開機自啟
```

---

## 使用方式

**網頁版：** 開啟 http://localhost:8765/download

**Tampermonkey（可選）：**
1. 安裝 [Tampermonkey](https://www.tampermonkey.net/)
2. 開啟 `scripts/ytify.user.js`，複製內容到新腳本
3. 在 YouTube 影片頁點擊「下載」按鈕

---

## 進階：遠端存取 (Cloudflare Tunnel)

想從外部網路使用？設定 Cloudflare Tunnel：

### 方法 A：全新設定

```bash
# Windows
winget install Cloudflare.cloudflared

# Linux
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install cloudflared

# 設定 Tunnel
cloudflared tunnel login
cloudflared tunnel create ytify
cloudflared tunnel route dns ytify ytify.your-domain.com
```

### 方法 B：共用現有 Tunnel

複製 `.cloudflared` 資料夾到新電腦，修改 `config.yml`：

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /home/你的帳號/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: ytify.your-domain.com
    service: http://localhost:8765
  - service: http_status:404
```

啟動：`start-all.bat` (Windows) 或 `cloudflared tunnel run ytify` (Linux)

---

## Docker 部署

```bash
docker-compose up -d

# 或使用預建映像
docker run -d --name ytify -p 8765:8765 ghcr.io/jeffrey0117/ytify:latest
```

---

## 專案結構

```
ytify/
├── run.bat / run.sh     # 一鍵啟動
├── install-deps.sh      # Linux 依賴安裝
├── ecosystem.config.js  # PM2 配置
├── main.py              # API 主程式
├── scripts/ytify.user.js  # Tampermonkey 腳本
├── static/              # 網頁前端
└── downloads/           # 暫存資料夾
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
