# Ytify Userscript UI 設計文檔

## 目標

在 YouTube 頁面的下載按鈕 UI 中加入引導元素，讓用戶可以：
1. 快速存取官網/說明文件
2. 了解如何設定自己的伺服器
3. 發現連線失敗時能獲得幫助

---

## 設計方案

### 方案 A：下拉選單底部加入幫助連結

在現有的畫質選單底部加入分隔線 + 幫助連結：

```
┌─────────────────────┐
│ 最佳畫質            │
│ 1080p               │
│ 720p                │
│ 480p                │
│ 僅音訊              │
├─────────────────────┤
│ ⚙️ 設定伺服器        │ → 開啟官網 quickstart
│ ❓ 使用說明          │ → 開啟官網
└─────────────────────┘
```

**優點：** 不打擾正常使用，需要時才會看到
**缺點：** 較隱蔽，新用戶可能不會注意

---

### 方案 B：連線失敗時顯示引導卡片

當偵測到伺服器未啟動時，顯示友善的錯誤提示：

```
┌─────────────────────────────────────────┐
│  ⚠️ 無法連線到 Ytify 伺服器              │
│                                         │
│  目前設定: http://localhost:8765        │
│                                         │
│  ┌─────────────┐  ┌─────────────┐      │
│  │ 📖 查看教學  │  │ ⚙️ 修改設定  │      │
│  └─────────────┘  └─────────────┘      │
│                                         │
│  還沒架設伺服器？                        │
│  → 點此查看 5 分鐘快速架設指南           │
└─────────────────────────────────────────┘
```

**優點：** 精準在需要幫助時出現
**缺點：** 需要額外 UI 空間

---

### 方案 C：下載按鈕旁的 Info 圖示（推薦）

在下載按鈕旁加一個小 icon，hover 顯示 tooltip：

```
[ ⬇️ 下載 ] [ℹ️]
              │
              ▼
     ┌──────────────────┐
     │ Ytify v10.2      │
     │ ────────────────  │
     │ 🌐 官方網站       │
     │ 📖 使用說明       │
     │ ⚙️ 伺服器設定     │
     │ 🐛 回報問題       │
     └──────────────────┘
```

**優點：** 始終可見但不打擾、資訊完整
**缺點：** 需要額外按鈕空間

---

## 推薦實作：方案 B + C 組合

### 1. 正常狀態：Info 圖示

```javascript
// 在下載按鈕旁加入 info icon
<button class="ytdl-info-btn" title="關於 Ytify">ℹ️</button>

// 點擊顯示 popup
┌──────────────────────────┐
│       Ytify v10.2        │
│  ────────────────────    │
│  🌐 官方網站              │ → https://jeffrey0117.github.io/Ytify/
│  📖 快速開始              │ → 官網 #quickstart
│  💻 GitHub               │ → https://github.com/Jeffrey0117/Ytify
│  🐛 回報問題              │ → GitHub Issues
│  ────────────────────    │
│  目前伺服器:              │
│  http://localhost:8765   │
│  ────────────────────    │
│  修改伺服器位置？          │
│  → 編輯腳本第 38 行       │
└──────────────────────────┘
```

### 2. 連線失敗狀態：錯誤提示

```javascript
// 當 health check 失敗時，下載按鈕變成警告狀態
[ ⚠️ 伺服器離線 ]

// 點擊顯示詳細幫助
┌─────────────────────────────────────────┐
│  ⚠️ 無法連線到 Ytify 伺服器              │
│                                         │
│  嘗試連線: http://localhost:8765        │
│                                         │
│  可能原因：                              │
│  1. 伺服器未啟動 → 執行 run.bat         │
│  2. 網址設定錯誤 → 編輯腳本第 38 行      │
│  3. 防火牆阻擋   → 檢查網路設定          │
│                                         │
│  ┌─────────────┐  ┌─────────────┐      │
│  │ 📖 查看教學  │  │ 🔄 重新連線  │      │
│  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────┘
```

---

## UI 風格

保持與 YouTube 一致的暗色風格：

```css
/* 主題色 */
--ytify-bg: #212121;
--ytify-text: #ffffff;
--ytify-muted: #aaaaaa;
--ytify-primary: #3ea6ff;  /* YouTube 藍 */
--ytify-error: #ff4444;
--ytify-border: #383838;

/* Info 按鈕 */
.ytdl-info-btn {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: transparent;
    border: 1px solid var(--ytify-border);
    color: var(--ytify-muted);
    cursor: pointer;
}

.ytdl-info-btn:hover {
    background: var(--ytify-border);
    color: var(--ytify-text);
}

/* Popup */
.ytdl-info-popup {
    position: absolute;
    background: var(--ytify-bg);
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 4px 32px rgba(0,0,0,0.5);
    min-width: 280px;
}

/* 連結項目 */
.ytdl-info-link {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border-radius: 8px;
    color: var(--ytify-text);
    text-decoration: none;
}

.ytdl-info-link:hover {
    background: var(--ytify-border);
}
```

---

## 實作優先順序

### Phase 1（簡單）
- [x] 腳本頂部加入設定區塊（已完成）
- [ ] 選單底部加入官網連結

### Phase 2（中等）
- [ ] Info 按鈕 + Popup
- [ ] 版本號顯示

### Phase 3（進階）
- [ ] 連線狀態檢測
- [ ] 離線時的友善錯誤提示
- [ ] 重新連線按鈕

---

## 文案

### Info Popup 標題
```
Ytify - 自架 YouTube 下載器
```

### 連結文字
```
🌐 官方網站
📖 快速開始（5 分鐘架設）
💻 GitHub 原始碼
🐛 回報問題 / 功能建議
⚙️ 修改伺服器位置
```

### 連線失敗提示
```
⚠️ 無法連線到伺服器

目前設定: {YTIFY_API_URL}

請確認：
• 伺服器是否已啟動（執行 run.bat）
• 網址設定是否正確
• 網路連線是否正常

[📖 查看教學] [🔄 重試]
```

### Footer 小字
```
v10.2 | MIT License
```
