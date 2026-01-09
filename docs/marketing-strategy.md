# ytify 宣傳策略

> 自架式 YouTube 下載伺服器的完整行銷規劃

---

## 目錄

1. [目標受眾分析](#1-目標受眾分析)
2. [宣傳渠道建議](#2-宣傳渠道建議)
3. [宣傳文案範例](#3-宣傳文案範例)
4. [SEO 關鍵字建議](#4-seo-關鍵字建議)
5. [社群經營策略](#5-社群經營策略)
6. [競品差異化定位](#6-競品差異化定位)

---

## 1. 目標受眾分析

### 1.1 主要受眾群體

#### A. 隱私意識型使用者

| 特徵 | 描述 |
|------|------|
| **人口統計** | 25-45 歲，技術背景，關注數位隱私 |
| **痛點** | 不信任第三方下載服務、擔心資料外洩 |
| **行為模式** | 使用 VPN、偏好開源軟體、自架服務 |
| **平台偏好** | Reddit (r/privacy, r/selfhosted)、Hacker News |

#### B. 自架服務愛好者 (Self-Hosters)

| 特徵 | 描述 |
|------|------|
| **人口統計** | 20-40 歲，IT 從業者、開發者、系統管理員 |
| **痛點** | 希望完全控制自己的服務與資料 |
| **行為模式** | 經營 Homelab、使用 Docker、熟悉 Linux |
| **平台偏好** | Reddit (r/selfhosted, r/homelab)、GitHub |

#### C. 進階 YouTube 使用者

| 特徵 | 描述 |
|------|------|
| **人口統計** | 18-35 歲，重度 YouTube 使用者 |
| **痛點** | 公共下載服務不穩定、常被封鎖、廣告太多 |
| **行為模式** | 批量下載、收藏教學影片、離線觀看需求 |
| **平台偏好** | 論壇、Telegram 群組、PTT |

#### D. 開發者社群

| 特徵 | 描述 |
|------|------|
| **人口統計** | 全年齡層開發者 |
| **痛點** | 需要整合下載功能到自己的工具或工作流程 |
| **行為模式** | 閱讀技術文件、參與開源專案 |
| **平台偏好** | GitHub、Stack Overflow、Dev.to |

### 1.2 使用者旅程地圖

```
認知 → 興趣 → 評估 → 試用 → 採用 → 推薦
  │       │       │       │       │       │
  │       │       │       │       │       └── 社群分享、Star 專案
  │       │       │       │       └── 長期使用、貢獻回饋
  │       │       │       └── git clone、執行 run.bat
  │       │       └── 閱讀 README、比較競品
  │       └── 發現「自架」「隱私」關鍵字
  └── 在 Reddit/論壇 看到推薦
```

### 1.3 受眾規模估計

| 群體 | 全球估計 | 潛在轉換率 |
|------|----------|------------|
| Self-Hosters | 500 萬+ | 5-10% |
| 隱私意識使用者 | 2000 萬+ | 1-3% |
| 進階 YouTube 使用者 | 5000 萬+ | 0.5-1% |
| 開發者 | 3000 萬+ | 2-5% |

---

## 2. 宣傳渠道建議

### 2.1 Reddit（高優先級）

#### 目標 Subreddit

| Subreddit | 成員數 | 適合內容 | 發文策略 |
|-----------|--------|----------|----------|
| r/selfhosted | 300K+ | 專案介紹 | Show & Tell 文 |
| r/homelab | 1.5M+ | 架設教學 | 教學圖文 |
| r/privacy | 1.5M+ | 隱私優勢 | 討論串回覆 |
| r/DataHoarder | 500K+ | 批量下載 | 使用案例 |
| r/opensource | 200K+ | 開源精神 | 專案發布 |
| r/commandline | 300K+ | CLI 工具 | 技術分享 |

#### Reddit 發文最佳實踐

1. **先參與社群**：發專案前先在該社群活躍 2-4 週
2. **遵守規則**：每個 subreddit 都有自我宣傳限制
3. **提供價值**：不只是宣傳，要解決問題
4. **適當時機**：美國時間週二至週四上午發文

### 2.2 GitHub（核心陣地）

#### 優化策略

- **完善 README**：清晰的功能說明、安裝步驟、截圖展示
- **Topics 標籤**：`youtube-downloader`, `self-hosted`, `privacy`, `yt-dlp`, `python`, `docker`
- **Release 發布**：定期發布版本，撰寫詳細 changelog
- **Issue 模板**：提供 bug report 和 feature request 模板
- **Contributing Guide**：鼓勵社群貢獻

#### GitHub 曝光管道

- GitHub Trending（目標：進入 Python/Daily）
- Awesome Lists 收錄申請
  - [awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted)
  - [awesome-privacy](https://github.com/pluja/awesome-privacy)

### 2.3 Hacker News

#### 發文策略

- **標題格式**：`Show HN: ytify – Self-hosted YouTube downloader with Tampermonkey integration`
- **發文時機**：美國東岸時間週二至週四 9-11 AM
- **準備回應**：發文後 2 小時內積極回覆留言

### 2.4 中文社群

| 平台 | 適合內容 | 優先級 |
|------|----------|--------|
| PTT (Linux, Soft_Job) | 技術分享 | 高 |
| 巴哈姆特 (電腦應用版) | 使用教學 | 中 |
| Mobile01 | 圖文教學 | 中 |
| V2EX | 專案發布 | 高 |
| 少數派 | 深度評測 | 中 |
| Telegram 群組 | 即時推廣 | 高 |

### 2.5 技術部落格平台

| 平台 | 策略 |
|------|------|
| Dev.to | 英文技術文章 |
| Medium | 深度教學 |
| Hashnode | SEO 優化文章 |
| iT 邦幫忙 | 中文技術文 |

### 2.6 影片平台

- **YouTube**：製作 3-5 分鐘架設教學
- **Bilibili**：中文圈影響力大

---

## 3. 宣傳文案範例

### 3.1 Reddit 發文（英文）

#### r/selfhosted 版本

```markdown
# Show & Tell: ytify - Self-hosted YouTube downloader with browser integration

Hey r/selfhosted!

I built **ytify**, a self-hosted YouTube download server that I wanted to share.

## Why I built this

I was tired of:
- Sketchy third-party download sites
- Services going down randomly
- Worrying about my data being collected

So I made ytify - run it on your own hardware, keep your data private.

## Features

- **Self-hosted**: Your server, your data, your rules
- **Multiple formats**: Best quality, 1080p, 720p, 480p, or audio-only
- **Browser integration**: Tampermonkey script adds download button directly on YouTube
- **Web UI**: Clean interface at `localhost:8765/download`
- **Remote access**: Works great with Cloudflare Tunnel
- **Easy setup**: One command on Windows/Linux/Mac, Docker supported

## Quick Start

```bash
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
./run.sh  # or run.bat on Windows
```

## Screenshots

[Web UI Screenshot]
[Tampermonkey Button Screenshot]

## Tech Stack

- Python + FastAPI
- yt-dlp under the hood
- Vanilla JS frontend

GitHub: https://github.com/Jeffrey0117/Ytify

Happy to answer any questions! Feedback welcome.
```

#### r/privacy 版本

```markdown
# Self-host your own YouTube downloader - no third parties needed

Sharing a project for those who value privacy when downloading YouTube videos.

**The problem**: Most YouTube download services are third-party websites that:
- Track your downloads
- Inject ads
- Could be collecting your viewing habits
- Often get shut down

**The solution**: ytify lets you run your own download server.

Key privacy benefits:
- Downloads go directly from YouTube → Your server → Your device
- No middleman services
- No accounts needed
- Works behind your firewall
- Pair with Cloudflare Tunnel for secure remote access

It's open source (MIT license) and uses yt-dlp.

GitHub: https://github.com/Jeffrey0117/Ytify
```

### 3.2 Reddit 發文（中文 - PTT 適用）

#### Soft_Job 版

```
[分享] ytify - 自架 YouTube 下載伺服器

各位好，分享一個自己做的小專案。

## 動機

之前用那些線上 YouTube 下載服務，不是廣告一堆就是常常掛掉，
而且每次下載都要經過別人的伺服器，隱私方面總覺得怪怪的。

所以就自己寫了 ytify，在自己電腦上跑，下載過程不經過任何第三方。

## 功能

- 支援多種畫質（最佳/1080p/720p/480p/純音訊）
- 網頁介面 + Tampermonkey 腳本（在 YouTube 頁面直接按下載）
- 支援 Docker 部署
- 可搭配 Cloudflare Tunnel 從外網存取

## 安裝

Windows:
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify && run.bat

Linux/Mac:
./run.sh

Docker:
docker-compose up -d

## 使用

1. 開 http://localhost:8765/download 貼網址
2. 或裝 Tampermonkey 腳本，YouTube 影片頁會多一個下載按鈕

GitHub: https://github.com/Jeffrey0117/Ytify

歡迎試用，有問題可以開 issue 或在這邊討論～
```

### 3.3 Hacker News

```
Show HN: ytify – Self-hosted YouTube downloader with browser integration

I built ytify because I wanted a YouTube downloader that:
1. Doesn't require trusting third-party services
2. Integrates seamlessly with my browser
3. Can be accessed remotely from my phone

It's a Python/FastAPI server that uses yt-dlp. The Tampermonkey script adds
a download button directly on YouTube pages. Works great with Cloudflare
Tunnel for remote access.

Features:
- Multiple quality options (best/1080p/720p/480p/audio-only)
- Real-time progress tracking
- Queue system for multiple downloads
- Docker support

Tech: Python, FastAPI, yt-dlp, vanilla JS

https://github.com/Jeffrey0117/Ytify
```

### 3.4 Twitter/X 推文

#### 發布推文

```
🚀 Just released ytify - a self-hosted YouTube downloader

✅ Your server, your data
✅ Browser integration (Tampermonkey)
✅ Web UI + API
✅ Docker ready
✅ Cloudflare Tunnel support

No more sketchy download sites.

GitHub: github.com/Jeffrey0117/Ytify

#selfhosted #privacy #opensource #youtube
```

#### 功能介紹推文串

```
Thread: Why I built ytify 🧵

1/ I download YouTube videos regularly for offline viewing. But every
download service I used had problems...

2/ Third-party sites:
- Covered in ads
- Randomly go offline
- Who knows what they're tracking?

3/ So I built ytify - run it yourself, on your own hardware.

4/ The cool part: Install the Tampermonkey script and get a download
button directly on YouTube. Pick quality, click, done.

5/ Works great with Cloudflare Tunnel - I can download from my phone
while away from home.

6/ It's open source and free. Check it out:
github.com/Jeffrey0117/Ytify
```

### 3.5 中文社群短文

#### V2EX / Telegram

```
分享一個自架的 YouTube 下載工具 - ytify

厭倦了那些廣告滿天飛、隨時可能掛掉的線上下載網站嗎？

ytify 讓你在自己的電腦/伺服器上跑下載服務：
• 隱私安全，資料不經過第三方
• Tampermonkey 腳本，YouTube 頁面一鍵下載
• 支援 Docker，部署超簡單
• 搭配 Cloudflare Tunnel 可遠端使用

Windows: run.bat
Linux/Mac: ./run.sh
Docker: docker-compose up -d

GitHub: https://github.com/Jeffrey0117/Ytify

MIT 開源，歡迎 Star ⭐
```

---

## 4. SEO 關鍵字建議

### 4.1 核心關鍵字

#### 英文關鍵字

| 關鍵字 | 搜尋量 | 競爭度 | 優先級 |
|--------|--------|--------|--------|
| self-hosted youtube downloader | 中 | 低 | ⭐⭐⭐ |
| youtube downloader self host | 中 | 低 | ⭐⭐⭐ |
| private youtube downloader | 中 | 中 | ⭐⭐⭐ |
| youtube download server | 低 | 低 | ⭐⭐ |
| yt-dlp web interface | 中 | 低 | ⭐⭐⭐ |
| yt-dlp gui self hosted | 低 | 低 | ⭐⭐ |
| youtube downloader docker | 高 | 中 | ⭐⭐⭐ |
| youtube downloader tampermonkey | 低 | 低 | ⭐⭐ |
| homelab youtube downloader | 低 | 低 | ⭐⭐ |
| youtube downloader no ads | 高 | 高 | ⭐ |

#### 中文關鍵字

| 關鍵字 | 搜尋量 | 競爭度 | 優先級 |
|--------|--------|--------|--------|
| 自架 YouTube 下載 | 低 | 低 | ⭐⭐⭐ |
| YouTube 下載器 自架 | 低 | 低 | ⭐⭐⭐ |
| yt-dlp 網頁介面 | 低 | 低 | ⭐⭐ |
| YouTube 下載 隱私 | 低 | 低 | ⭐⭐ |
| YouTube 下載伺服器 | 低 | 低 | ⭐⭐⭐ |
| YouTube 影片下載 Docker | 中 | 低 | ⭐⭐ |

### 4.2 長尾關鍵字

#### 英文長尾

- how to self host youtube downloader
- best self hosted youtube downloader 2025
- youtube downloader without third party
- yt-dlp web ui docker
- private youtube download solution
- youtube downloader for homelab
- cloudflare tunnel youtube downloader

#### 中文長尾

- 如何自架 YouTube 下載服務
- 不用第三方的 YouTube 下載方法
- 自己架設 YouTube 下載伺服器教學
- yt-dlp Docker 部署教學
- 在家架設影片下載服務

### 4.3 GitHub README SEO 優化

```markdown
# ytify - Self-Hosted YouTube Downloader

> A privacy-focused, self-hosted YouTube download server with browser integration

<!-- 關鍵字密度優化 -->
ytify is a **self-hosted YouTube downloader** that runs on your own server.
Download YouTube videos privately without relying on third-party services.

## Features

- **Self-hosted** - Your server, your data, complete privacy
- **Browser Integration** - Tampermonkey script adds download button to YouTube
- **Web Interface** - Clean UI for easy downloading
- **Docker Support** - Deploy with a single command
- **Cloudflare Tunnel** - Secure remote access from anywhere
- **Multiple Formats** - Best quality, 1080p, 720p, 480p, audio-only

## Keywords

youtube downloader, self-hosted, yt-dlp, docker, privacy, tampermonkey,
homelab, open source, web interface, download server
```

### 4.4 部落格文章標題建議

#### 英文

1. "How to Self-Host Your Own YouTube Downloader in 5 Minutes"
2. "Stop Using Sketchy YouTube Download Sites - Self-Host Instead"
3. "The Ultimate Privacy-Focused YouTube Downloader Setup Guide"
4. "ytify: A Self-Hosted Alternative to Online YouTube Downloaders"
5. "Building a Personal YouTube Download Server with Docker"

#### 中文

1. 「5 分鐘自架 YouTube 下載伺服器 - ytify 完整教學」
2. 「不再依賴第三方！自己架設 YouTube 下載服務」
3. 「注重隱私的 YouTube 下載方案 - ytify 使用指南」
4. 「用 Docker 部署私人 YouTube 下載伺服器」
5. 「Homelab 必備：自架 ytify 下載 YouTube 影片」

---

## 5. 社群經營策略

### 5.1 社群建設階段

#### 第一階段：建立基礎（1-3 個月）

| 目標 | 行動 | KPI |
|------|------|-----|
| GitHub 曝光 | 優化 README、參與 Awesome Lists | 100 Stars |
| Reddit 存在感 | 發布介紹文、回覆相關討論 | 3 篇熱門文 |
| 建立信任 | 快速回應 Issues、定期更新 | Issue 回應 < 24h |

#### 第二階段：成長擴張（3-6 個月）

| 目標 | 行動 | KPI |
|------|------|-----|
| 社群互動 | 建立 Discord/Telegram | 100 活躍成員 |
| 內容產出 | 技術部落格文章 | 5 篇以上 |
| 口碑傳播 | 鼓勵使用者分享 | 外部引用連結 |

#### 第三階段：生態建設（6-12 個月）

| 目標 | 行動 | KPI |
|------|------|-----|
| 貢獻者成長 | 建立貢獻指南、標記 good-first-issue | 10+ 貢獻者 |
| 功能擴展 | 社群驅動的功能開發 | 5+ 社群 PR |
| 跨專案合作 | 與相關專案整合 | 2+ 整合專案 |

### 5.2 Discord/Telegram 社群規劃

#### 頻道結構

```
# ytify Community
├── 📢 announcements     - 版本發布、重要公告
├── 💬 general           - 一般討論
├── ❓ support           - 使用問題求助
├── 💡 feature-requests  - 功能建議
├── 🐛 bug-reports       - 問題回報
├── 🛠️ development       - 開發討論
├── 📸 showcase          - 使用案例分享
└── 🌐 languages
    ├── chinese          - 中文討論
    └── other            - 其他語言
```

#### 社群規則

1. 尊重所有成員
2. 保持討論與 ytify 相關
3. 不分享非法內容
4. 提問前先搜尋
5. 幫助他人

### 5.3 內容行事曆

#### 每週內容

| 日期 | 內容類型 | 平台 |
|------|----------|------|
| 週一 | 技術分享 / Tips | Twitter |
| 週三 | 使用案例 / 教學 | Blog |
| 週五 | 社群互動 / Q&A | Discord |

#### 每月內容

| 週次 | 內容 |
|------|------|
| 第一週 | 版本更新公告 |
| 第二週 | 深度技術文章 |
| 第三週 | 使用者案例分享 |
| 第四週 | 社群回顧 & 預告 |

### 5.4 互動策略

#### GitHub 互動

- **Issue 回應**：24 小時內首次回應
- **PR 審核**：48 小時內審核
- **感謝貢獻者**：在 README 列出貢獻者
- **標籤系統**：good-first-issue、help-wanted、enhancement

#### 社群互動

- **歡迎新成員**：自動歡迎訊息
- **問題追蹤**：確保問題得到解決
- **鼓勵分享**：使用者分享使用心得
- **徵求反饋**：定期詢問改進建議

### 5.5 品牌形象

#### 核心價值

- **隱私優先**：不追蹤、不收集、不外洩
- **使用者掌控**：自己的服務、自己的資料
- **開放透明**：開源、可審計
- **簡單易用**：一鍵安裝、直覺操作

#### 語調風格

- 技術專業但不艱澀
- 友善親切不傲慢
- 直接了當不囉嗦

---

## 6. 競品差異化定位

### 6.1 競品分析

#### 線上下載服務（如 y2mate、savefrom）

| 面向 | 競品 | ytify |
|------|------|-------|
| 隱私 | ❌ 經過第三方 | ✅ 完全自架 |
| 穩定性 | ❌ 常被封鎖 | ✅ 自己控制 |
| 廣告 | ❌ 廣告很多 | ✅ 無廣告 |
| 速度 | ⚠️ 看伺服器 | ✅ 取決於你的網路 |
| 使用門檻 | ✅ 零門檻 | ⚠️ 需要架設 |

#### 桌面軟體（如 4K Video Downloader）

| 面向 | 競品 | ytify |
|------|------|-------|
| 安裝 | ❌ 需安裝軟體 | ✅ 網頁/瀏覽器腳本 |
| 跨裝置 | ❌ 僅限單機 | ✅ 任何裝置存取 |
| 遠端使用 | ❌ 不支援 | ✅ Cloudflare Tunnel |
| 價格 | ❌ 付費版才完整 | ✅ 完全免費 |
| 更新 | ⚠️ 需手動更新 | ✅ git pull 即可 |

#### 其他自架方案（如 MeTube、TubeArchivist）

| 面向 | MeTube | TubeArchivist | ytify |
|------|--------|---------------|-------|
| 定位 | 下載器 | 完整歸檔 | 輕量下載 |
| 功能複雜度 | 中 | 高 | 低 |
| 資源需求 | 中 | 高 | 低 |
| 瀏覽器整合 | ❌ 無 | ❌ 無 | ✅ Tampermonkey |
| 學習曲線 | 低 | 高 | 極低 |

### 6.2 差異化定位

#### ytify 的獨特價值主張 (UVP)

> **「最簡單的自架 YouTube 下載方案，瀏覽器一鍵下載」**

#### 三大差異化優勢

##### 1. 瀏覽器原生整合

```
其他方案：複製網址 → 開新分頁 → 貼上 → 下載
ytify：在 YouTube 頁面點擊「下載」→ 完成
```

Tampermonkey 腳本直接在 YouTube 頁面新增下載按鈕，無需切換頁面。

##### 2. 極低部署門檻

```bash
# 一行指令啟動
git clone https://github.com/Jeffrey0117/Ytify.git && cd Ytify && ./run.sh
```

- 不需要複雜設定
- 不需要資料庫
- 不需要額外服務

##### 3. 遠端存取設計

原生支援 Cloudflare Tunnel 整合：
- 從手機下載影片到家裡的伺服器
- 無需 Port Forwarding
- 免費、安全、簡單

### 6.3 目標市場定位圖

```
                    功能完整
                        │
                        │
        TubeArchivist   │
              ●         │
                        │
                        │         ● MeTube
     ─────────────────────────────────────────
     複雜設定           │              簡單設定
                        │
                        │    ● ytify
                        │
                        │
        yt-dlp (CLI)    │
              ●         │
                        │
                    功能精簡
```

### 6.4 競爭策略

#### 短期策略（0-6 個月）

1. **強化差異點**：持續優化 Tampermonkey 腳本體驗
2. **降低門檻**：一鍵安裝腳本、Windows Installer
3. **建立社群**：在 Self-Hosted 社群建立存在感

#### 中期策略（6-12 個月）

1. **功能擴展**：Playlist 支援、字幕下載
2. **整合生態**：Docker Hub 官方映像、Unraid 模板
3. **多語言**：界面多語言支援

#### 長期策略（12+ 個月）

1. **平台擴展**：支援更多影片平台（yt-dlp 支援的）
2. **API 生態**：讓其他工具可以整合
3. **社群驅動**：由社群主導功能開發

### 6.5 行銷訊息矩陣

| 受眾 | 痛點 | ytify 解決方案 | 關鍵訊息 |
|------|------|----------------|----------|
| 隱私重視者 | 不信任第三方 | 完全自架 | 「你的資料，你做主」 |
| Self-Hosters | 想要簡單方案 | 一鍵部署 | 「最輕量的 YouTube 下載服務」 |
| 一般使用者 | 公共服務不穩 | 自己控制 | 「永不關站的下載服務」 |
| 開發者 | 需要 API | RESTful API | 「整合友善的下載 API」 |

---

## 附錄：行動清單

### 立即可做（本週）

- [ ] 優化 GitHub README
- [ ] 設定正確的 Topics 標籤
- [ ] 準備 Reddit 發文
- [ ] 建立 Twitter 帳號

### 短期（本月）

- [ ] 在 r/selfhosted 發布介紹文
- [ ] 申請加入 awesome-selfhosted
- [ ] 撰寫第一篇技術部落格
- [ ] 建立 Discord/Telegram 群組

### 中期（3 個月內）

- [ ] 發布 Hacker News Show HN
- [ ] 製作 YouTube 教學影片
- [ ] 在 V2EX、PTT 發布中文介紹
- [ ] 撰寫 3 篇以上 SEO 文章

---

*文件版本：1.0*
*最後更新：2025 年 1 月*
