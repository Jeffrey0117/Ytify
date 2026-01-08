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

**需求：** [Python 3.8+](https://www.python.org/downloads/)、[FFmpeg](https://ffmpeg.org/)、[Node.js](https://nodejs.org/)（可選）

```bash
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
run.bat
```

`run.bat` 會自動檢查環境、安裝依賴、啟動服務。

### 安裝瀏覽器腳本（可選）

1. 安裝 [Tampermonkey](https://www.tampermonkey.net/)
2. 開啟 `scripts/ytify.user.js`
3. 複製內容到 Tampermonkey 新腳本，儲存

---

## 啟動方式

| 指令 | 說明 |
|------|------|
| `run.bat` | 一鍵啟動（推薦，含 PM2 守護進程） |
| `start.bat` | 直接啟動（無守護） |
| `setup.bat` | 僅安裝依賴 |

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

**Tampermonkey：**
1. 確保 ytify 服務在運行
2. 開啟任意 YouTube 影片
3. 點擊右下角「下載」按鈕
4. 選擇畫質，等待下載完成

---

## 進階：遠端存取 (Cloudflare Tunnel)

想從外部網路使用？設定 Cloudflare Tunnel：

### 方法 A：全新設定

```bash
winget install Cloudflare.cloudflared
cloudflared tunnel login
cloudflared tunnel create ytify
cloudflared tunnel route dns ytify ytify.your-domain.com
```

### 方法 B：共用現有 Tunnel

從原電腦複製 `C:\Users\帳號\.cloudflared\` 到新電腦，修改 `config.yml` 的路徑：

```yaml
tunnel: <TUNNEL_ID>
credentials-file: C:\Users\新帳號\.cloudflared\<TUNNEL_ID>.json

ingress:
  - hostname: ytify.your-domain.com
    service: http://localhost:8765
  - service: http_status:404
```

啟動：`start-all.bat`

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
├── run.bat              # 一鍵啟動（推薦）
├── setup.bat            # 安裝依賴
├── start.bat            # 直接啟動
├── start-all.bat        # 啟動 + Cloudflare Tunnel
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
→ 安裝 FFmpeg：`winget install FFmpeg`

**腳本沒反應？**
→ 確認 ytify 服務在運行，檢查 F12 Console

---

## License

MIT
