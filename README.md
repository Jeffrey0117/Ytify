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

### 方法 A：全新設定（在新電腦建立 Tunnel）

```bash
# 1. 安裝 cloudflared
winget install Cloudflare.cloudflared

# 2. 登入 Cloudflare（會開啟瀏覽器授權）
cloudflared tunnel login

# 3. 建立 Tunnel（只需一次）
cloudflared tunnel create ytify

# 4. 設定 DNS 指向你的網域
cloudflared tunnel route dns ytify ytify.your-domain.com
```

建立完成後，會在 `C:\Users\你的帳號\.cloudflared\` 產生：
- `cert.pem` - 憑證檔
- `<TUNNEL_ID>.json` - Tunnel 認證檔（一串 UUID）

### 方法 B：共用現有 Tunnel（複製到其他電腦）

如果已經有設定好的 Tunnel，要在其他電腦使用**同一個網域**：

1. **從原電腦複製整個 `.cloudflared` 資料夾**
   ```
   C:\Users\原帳號\.cloudflared\
   ```
   複製到新電腦的：
   ```
   C:\Users\新帳號\.cloudflared\
   ```

2. **修改 `config.yml` 的路徑**

   開啟 `C:\Users\新帳號\.cloudflared\config.yml`，修改 `credentials-file` 為新電腦的完整路徑：
   ```yaml
   tunnel: <TUNNEL_ID>
   credentials-file: C:\Users\新帳號\.cloudflared\<TUNNEL_ID>.json  # ← 改這裡！

   ingress:
     - hostname: ytify.your-domain.com
       service: http://localhost:8765
     - service: http_status:404
   ```

   ⚠️ **注意**：`credentials-file` 必須是**完整路徑**，不能用相對路徑！

### 啟動服務

設定完成後：

```bash
# 使用 start-all.bat 同時啟動 ytify + Tunnel
start-all.bat
```

### 設定 Tampermonkey

修改 `scripts/ytify.user.js` 中的 API 網址：

```javascript
const YTIFY_API_URL = 'https://ytify.your-domain.com';  // 改成你的網域（不要加結尾斜線！）
```

並確認 `@connect` 包含你的網域：
```javascript
// @connect      your-domain.com
// @connect      ytify.your-domain.com
```

---

## 專案結構

```
ytify/
├── install.bat          # 安裝依賴
├── start.bat            # 啟動本地服務
├── start-all.bat        # 啟動服務 + Cloudflare Tunnel
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
