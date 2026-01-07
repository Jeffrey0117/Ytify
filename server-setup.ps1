# ytify Server 部署腳本 (Windows PowerShell)
# 使用方式: 右鍵 -> 使用 PowerShell 執行

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ytify Server 部署腳本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 檢查 Python
Write-Host "[1/5] 檢查 Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "      $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "      Python 未安裝！請先安裝 Python 3.10+" -ForegroundColor Red
    exit 1
}

# 2. 檢查 FFmpeg
Write-Host "[2/5] 檢查 FFmpeg..." -ForegroundColor Yellow
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "      FFmpeg 已安裝" -ForegroundColor Green
} catch {
    Write-Host "      FFmpeg 未安裝！" -ForegroundColor Red
    Write-Host "      請從 https://ffmpeg.org/download.html 下載並加入 PATH" -ForegroundColor Yellow
    Write-Host "      或使用: winget install FFmpeg" -ForegroundColor Yellow
}

# 3. 安裝 Python 依賴
Write-Host "[3/5] 安裝 Python 依賴..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
Write-Host "      依賴安裝完成" -ForegroundColor Green

# 4. 檢查 Cloudflared
Write-Host "[4/5] 檢查 Cloudflared..." -ForegroundColor Yellow
try {
    $cfVersion = cloudflared --version 2>&1
    Write-Host "      $cfVersion" -ForegroundColor Green
} catch {
    Write-Host "      Cloudflared 未安裝，正在下載..." -ForegroundColor Yellow

    # 下載 cloudflared
    $cloudflaredUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    $cloudflaredPath = "$PWD\cloudflared.exe"

    Invoke-WebRequest -Uri $cloudflaredUrl -OutFile $cloudflaredPath
    Write-Host "      Cloudflared 下載完成: $cloudflaredPath" -ForegroundColor Green
}

# 5. 建立啟動腳本
Write-Host "[5/5] 建立啟動腳本..." -ForegroundColor Yellow

# 建立 downloads 資料夾
if (!(Test-Path "downloads")) {
    New-Item -ItemType Directory -Path "downloads" | Out-Null
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "啟動方式:" -ForegroundColor Cyan
Write-Host "  1. 僅本地:    .\start.bat" -ForegroundColor White
Write-Host "  2. 含 Tunnel: .\start-with-tunnel.bat" -ForegroundColor White
Write-Host ""
Write-Host "Tunnel 網址會顯示在終端機中，複製到 Tampermonkey 腳本的 API_BASE" -ForegroundColor Yellow
Write-Host ""

Read-Host "按 Enter 結束"
