# ytify

YouTube 影片下載工具 - 在 YouTube 網頁上一鍵下載影片

## 功能

- 一鍵下載 YouTube 影片
- 支援多種畫質 (最佳/1080p/720p/480p)
- 支援僅下載音訊
- 即時下載進度
- 下載完成自動清理伺服器暫存

---

## 安裝 (3 步驟)

### 1. 安裝依賴

**需求：**
- [Python 3.8+](https://www.python.org/downloads/) (安裝時勾選 "Add to PATH")
- [FFmpeg](https://ffmpeg.org/) (影音合併)

```bash
# 下載專案
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify

# Windows 一鍵安裝
install.bat

# 或手動安裝
pip install -r requirements.txt
winget install FFmpeg   # Windows
brew install ffmpeg     # Mac
```

### 2. 安裝瀏覽器腳本

1. 安裝 [Tampermonkey](https://www.tampermonkey.net/)
2. 開啟 `scripts/ytify.user.js`
3. 複製內容到 Tampermonkey 新腳本，儲存

### 3. 啟動服務

```bash
# Windows
start.bat

# 或直接執行
python main.py
```

---

## 使用方式

1. 確保 ytify 服務在運行 (`start.bat`)
2. 開啟任意 YouTube 影片
3. 點擊右下角「下載」按鈕
4. 選擇 YTIFY 區塊的畫質選項
5. 等待下載完成，檔案自動儲存到電腦

---

## 進階：遠端存取 (Cloudflare Tunnel)

想從外部網路使用？設定 Cloudflare Tunnel：

```bash
# 1. 安裝 cloudflared
winget install Cloudflare.cloudflared

# 2. 登入 Cloudflare
cloudflared tunnel login

# 3. 建立 Tunnel（只需一次）
cloudflared tunnel create ytify
cloudflared tunnel route dns ytify your-domain.com

# 4. 啟動時選擇 [2] 即可
start.bat
```

設定好後，修改 Tampermonkey 腳本中的 `YTIFY_API_URL` 為你的網域。

---

## 專案結構

```
ytify/
├── install.bat          # 安裝依賴
├── start.bat            # 啟動服務
├── main.py              # API 主程式
├── api/routes.py        # API 路由
├── services/downloader.py
├── scripts/ytify.user.js  # Tampermonkey 腳本
└── downloads/           # 暫存資料夾
```

---

## API

| 端點 | 方法 | 說明 |
|------|------|------|
| `/health` | GET | 健康檢查 |
| `/api/info` | POST | 取得影片資訊 |
| `/api/download` | POST | 開始下載 |
| `/api/status/{task_id}` | GET | 查詢狀態 |
| `/api/download-file/{filename}` | GET | 下載檔案 |

---

## 常見問題

**下載的影片沒有聲音？**
→ 安裝 FFmpeg：`winget install FFmpeg`

**腳本沒反應？**
→ 確認 ytify 服務在運行，檢查 F12 Console

**Rate limit 錯誤？**
→ YouTube 暫時限制，等一小時或換影片試試

---

## License

MIT
