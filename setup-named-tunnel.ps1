# ytify Named Tunnel 設定腳本
# 讓你用自己的網域（如 ytify.example.com）而不是隨機網址

param(
    [Parameter(Mandatory=$true)]
    [string]$Domain  # 你的子網域，例如 ytify.example.com
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ytify Named Tunnel 設定" -ForegroundColor Cyan
Write-Host "  目標網域: $Domain" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 cloudflared
$cloudflared = "cloudflared"
if (!(Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    if (Test-Path ".\cloudflared.exe") {
        $cloudflared = ".\cloudflared.exe"
    } else {
        Write-Host "[錯誤] cloudflared 未找到！請先執行 server-setup.ps1" -ForegroundColor Red
        exit 1
    }
}

# Step 1: 登入
Write-Host "[1/4] 登入 Cloudflare..." -ForegroundColor Yellow
Write-Host "      會開啟瀏覽器，請選擇你的網域並授權" -ForegroundColor Gray
& $cloudflared login

if ($LASTEXITCODE -ne 0) {
    Write-Host "[錯誤] 登入失敗" -ForegroundColor Red
    exit 1
}
Write-Host "      登入成功" -ForegroundColor Green

# Step 2: 建立 Tunnel
Write-Host ""
Write-Host "[2/4] 建立 Tunnel..." -ForegroundColor Yellow
$tunnelName = "ytify"

# 檢查是否已存在
$existingTunnel = & $cloudflared tunnel list 2>&1 | Select-String $tunnelName
if ($existingTunnel) {
    Write-Host "      Tunnel '$tunnelName' 已存在，跳過建立" -ForegroundColor Gray
} else {
    & $cloudflared tunnel create $tunnelName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[錯誤] 建立 Tunnel 失敗" -ForegroundColor Red
        exit 1
    }
}
Write-Host "      Tunnel 已就緒" -ForegroundColor Green

# Step 3: 設定 DNS
Write-Host ""
Write-Host "[3/4] 設定 DNS 路由..." -ForegroundColor Yellow
Write-Host "      綁定 $Domain -> ytify tunnel" -ForegroundColor Gray
& $cloudflared tunnel route dns $tunnelName $Domain

if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] DNS 設定可能已存在，繼續..." -ForegroundColor Yellow
} else {
    Write-Host "      DNS 已設定" -ForegroundColor Green
}

# Step 4: 產生設定檔
Write-Host ""
Write-Host "[4/4] 產生設定檔..." -ForegroundColor Yellow

# 取得 Tunnel ID
$tunnelInfo = & $cloudflared tunnel list 2>&1 | Select-String $tunnelName
$tunnelId = ($tunnelInfo -split '\s+')[0]

$configContent = @"
tunnel: $tunnelId
credentials-file: $env:USERPROFILE\.cloudflared\$tunnelId.json

ingress:
  - hostname: $Domain
    service: http://localhost:8765
  - service: http_status:404
"@

$configPath = "$env:USERPROFILE\.cloudflared\config.yml"
$configContent | Out-File -FilePath $configPath -Encoding UTF8

Write-Host "      設定檔已儲存: $configPath" -ForegroundColor Green

# 完成
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  設定完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "啟動方式:" -ForegroundColor Cyan
Write-Host "  .\start-named-tunnel.bat" -ForegroundColor White
Write-Host ""
Write-Host "你的固定網址:" -ForegroundColor Cyan
Write-Host "  https://$Domain" -ForegroundColor White
Write-Host ""
Write-Host "Tampermonkey 腳本設定:" -ForegroundColor Cyan
Write-Host "  API_BASE: 'https://$Domain'" -ForegroundColor White
Write-Host "  @connect: $Domain" -ForegroundColor White
Write-Host ""

Read-Host "按 Enter 結束"
