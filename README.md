# ytify

YouTube 影片下載 API 服務 + Tampermonkey 腳本

在 YouTube 網頁上一鍵下載影片，透過本地 API 服務完成下載。

## 功能

- 支援多種畫質 (最佳/1080p/720p/480p)
- 支援僅下載音訊 (MP3)
- 即時下載進度顯示
- Tampermonkey 腳本一鍵操作

## 快速開始

### 1. 安裝依賴

```bash
cd ytify
pip install -r requirements.txt
```

### 2. 啟動服務

```bash
python main.py
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
4. 檔案會儲存在 `downloads/` 資料夾

## API 文件

### 健康檢查
```
GET /health
```

### 取得影片資訊
```
POST /api/info
Content-Type: application/json

{"url": "https://www.youtube.com/watch?v=xxxxx"}
```

### 開始下載
```
POST /api/download
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=xxxxx",
  "format": "best",
  "audio_only": false
}
```

### 查詢下載狀態
```
GET /api/status/{task_id}
```

### 列出已下載檔案
```
GET /api/files
```

### 刪除檔案
```
DELETE /api/files/{filename}
```

## 專案結構

```
ytify/
├── main.py              # FastAPI 入口
├── requirements.txt     # Python 依賴
├── README.md
├── api/
│   ├── __init__.py
│   └── routes.py        # API 路由
├── services/
│   ├── __init__.py
│   └── downloader.py    # yt-dlp 下載邏輯
├── scripts/
│   └── ytify.user.js    # Tampermonkey 腳本
└── downloads/           # 下載檔案存放
```

## 注意事項

- 需要安裝 [FFmpeg](https://ffmpeg.org/) 才能合併影片和音訊
- 服務預設監聽 `0.0.0.0:8765`
- 下載的檔案會存放在 `downloads/` 資料夾

## License

MIT
