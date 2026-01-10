<p align="center">
  <img src="static/logo.png" alt="Ytify Logo" width="100">
  <br>
  <b>Ytify</b>
</p>

<p align="center">
  <b>自架 YouTube 下載伺服器 — 隱私、穩定、可控</b>
  <br>
  厭倦了公共下載站的廣告、限速、關站？自己架一個，永久免費用。
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
  <a href="https://github.com/Jeffrey0117/Ytify/stargazers"><img src="https://img.shields.io/github/stars/Jeffrey0117/Ytify" alt="GitHub stars"></a>
</p>

<p align="center">
  <a href="#-30-秒快速開始">快速開始</a> ·
  <a href="https://jeffrey0117.github.io/Ytify/#tampermonkey">腳本安裝</a> ·
  <a href="https://jeffrey0117.github.io/Ytify/">官方網站</a>
</p>

## 🔍 運作原理

```
┌─────────────┐     請求下載      ┌──────────────┐     yt-dlp     ┌─────────┐
│   瀏覽器     │ ───────────────→ │  Ytify 伺服器 │ ─────────────→ │ YouTube │
│ (你的電腦)   │ ←─────────────── │  (你的電腦)   │ ←───────────── │         │
└─────────────┘     回傳檔案      └──────────────┘     影片資料     └─────────┘
```

1. 你在瀏覽器點擊下載
2. Ytify 伺服器收到請求，使用 yt-dlp 從 YouTube 抓取影片
3. 影片下載到伺服器後，再傳回你的瀏覽器

---

## ✨ 為什麼選 Ytify？

| 公共下載站 | Ytify |
|:---:|:---:|
| 🐌 限速、排隊 | ⚡ 滿速下載 |
| 🚫 隨時關站 | 🏠 自己的伺服器永遠在 |
| 👀 下載記錄被追蹤 | 🔒 100% 隱私 |
| 📺 只能網頁操作 | 🖱️ YouTube 頁面一鍵下載 |
| 💸 付費解鎖功能 | 🆓 完全免費開源 |

### 為什麼要自架？

- **隱私**：不經過第三方服務，資料不外流
- **穩定**：不受公共服務限制或關站影響
- **可控**：自訂畫質、格式、儲存位置
- **遠端**：搭配 Cloudflare Tunnel 可從任何地方使用

---

## 🚀 30 秒快速開始

```bash
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
run.bat    # Windows 雙擊執行也可以
```

就這樣！按 Enter 選預設選項，服務就啟動了。

👉 開啟 http://localhost:8765 開始下載

---

## 🎯 核心功能

### 🔥 併發下載
同時下載 3 部影片，不用一個一個等

### 📱 隨處可用
搭配 Cloudflare Tunnel，手機、辦公室都能用

### 🖱️ 一鍵下載
安裝 Tampermonkey 腳本，在 YouTube 頁面直接點擊下載

### 🔄 自動更新
每 5 分鐘自動同步最新版本，更新時不中斷下載

### 📋 播放清單
一次下載整個播放清單，最多 50 部

### 🎵 多種格式
最佳畫質 / 1080p / 720p / 480p / 僅音訊 MP3

---

## 📥 兩種使用方式

### 方式一：網頁介面
開啟 `http://localhost:8765`，貼上網址即可下載

### 方式二：Tampermonkey 腳本 ⭐推薦
在 YouTube 影片頁面直接出現下載按鈕！

1. 安裝 [Tampermonkey](https://www.tampermonkey.net/) 瀏覽器擴充功能
2. 新增腳本，貼上 `scripts/ytify.user.js` 內容
3. 在 YouTube 看到下載按鈕，點擊選擇畫質

> 📖 [完整安裝教學](https://jeffrey0117.github.io/Ytify/#tampermonkey)

---

## 🖥️ 啟動模式

| 模式 | 資源需求 | 自動更新 | 適合 |
|:---:|:---:|:---:|:---:|
| 🐳 Docker | 4GB+ RAM | ✅ | 高規格電腦 |
| 🐍 Python | 低 | ❌ | 臨時使用 |
| 🚀 **Python + 自動更新** | 低 | ✅ | **推薦** |

> 💡 不知道選哪個？直接按 Enter，預設就是最推薦的選項

---

## 🌐 遠端存取

想從手機或外網使用？設定 Cloudflare Tunnel：

```bash
# 安裝 (一次)
winget install Cloudflare.cloudflared

# 設定 (一次)
cloudflared tunnel login
cloudflared tunnel create ytify
cloudflared tunnel route dns ytify ytify.你的網域.com

# 之後執行 start-all.bat 即可
```

---

## 🛠️ 網頁功能

| 頁面 | 說明 |
|------|------|
| `/download` | 下載介面 |
| `/playlist` | 播放清單下載 |
| `/history` | 下載歷史 |
| `/files` | 檔案管理 |
| `/dashboard` | 系統狀態 |

---

## ❓ 常見問題

<details>
<summary><b>下載的影片沒有聲音？</b></summary>

安裝 FFmpeg：
- Windows: `winget install FFmpeg`
- Linux: `sudo apt install ffmpeg`
</details>

<details>
<summary><b>Tampermonkey 腳本沒反應？</b></summary>

1. 確認 Ytify 服務已啟動
2. 點擊腳本的 Info 按鈕檢查連線狀態
3. 如果是遠端伺服器，修改腳本中的伺服器位址
</details>

<details>
<summary><b>自動更新會中斷下載嗎？</b></summary>

不會！Ytify 有「優雅重啟」機制，會等所有下載任務完成後才更新重啟。
</details>

<details>
<summary><b>支援哪些網站？</b></summary>

Ytify 使用 yt-dlp，支援 YouTube、Bilibili、Twitter 等 [1000+ 網站](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)。
</details>

---

## 📊 版本歷史

### v10.7 (2025-01) - 最新
- ✨ 失敗任務「重試」按鈕
- ✨ 任務「關閉」按鈕
- ✨ 面板「清除」按鈕
- 🐛 修復多任務下載阻塞問題
- 🐛 修復快速連續下載卡住問題

### v10.6 (2025-01)
- ✨ 併發下載（最多 3 個同時）
- ✨ 優雅重啟機制
- ✨ 離線時可修改伺服器位置

<details>
<summary>更早版本...</summary>

### v10.5 (2025-01)
- ✨ 連線狀態即時檢測
- ✨ 離線友善提示

### v10.0 (2024-12)
- ✨ WebSocket 即時進度
- ✨ 播放清單批次下載
- ✨ 代理池支援
</details>

---

## 🤝 貢獻

歡迎 Issue 和 PR！

---

## 📜 License

MIT - 自由使用、修改、分發

---

<p align="center">
  <b>⭐ 如果覺得好用，給個 Star 支持一下！</b>
</p>
