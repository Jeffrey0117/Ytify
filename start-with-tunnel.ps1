# ytify Server + Cloudflare Tunnel 啟動腳本 (PowerShell)
# 使用方式: 右鍵 -> 使用 PowerShell 執行

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ytify - YouTube Downloader API" -ForegroundColor Cyan
Write-Host "  with Cloudflare Tunnel" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 cloudflared
$cloudflared = "cloudflared"
if (!(Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    if (Test-Path ".\cloudflared.exe") {
        $cloudflared = ".\cloudflared.exe"
    } else {
        Write-Host "[錯誤] cloudflared 未找到！" -ForegroundColor Red
        Write-Host "請先執行 server-setup.ps1" -ForegroundColor Yellow
        Read-Host "按 Enter 結束"
        exit 1
    }
}

# 啟動 API Server (背景)
Write-Host "[1/2] 啟動 ytify API Server..." -ForegroundColor Yellow
$apiJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    python main.py
}
Write-Host "      API Server PID: $($apiJob.Id)" -ForegroundColor Green

# 等待 API 啟動
Start-Sleep -Seconds 3

# 測試 API 是否啟動
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8765/health" -Method Get
    Write-Host "      API Server 已啟動" -ForegroundColor Green
} catch {
    Write-Host "      [警告] API Server 可能尚未完全啟動" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2/2] 啟動 Cloudflare Tunnel..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  複製下方的 Tunnel 網址" -ForegroundColor Green
Write-Host "  貼到 Tampermonkey 腳本的 API_BASE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 啟動 Tunnel (前景，會顯示網址)
& $cloudflared tunnel --url http://localhost:8765

# 清理
Write-Host ""
Write-Host "正在關閉 API Server..." -ForegroundColor Yellow
Stop-Job -Job $apiJob
Remove-Job -Job $apiJob

Write-Host "已關閉" -ForegroundColor Green
Read-Host "按 Enter 結束"
