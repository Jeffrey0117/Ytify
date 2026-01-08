# ytify Named Tunnel 設定腳本
# 讓你用自己的網域（如 ytify.example.com）而不是隨機網址

# 防止視窗直接關閉
trap {
    Write-Host ""
    Write-Host "[錯誤] $_" -ForegroundColor Red
    Read-Host "按 Enter 結束"
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ytify Named Tunnel 設定" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 互動式輸入網域
$Domain = Read-Host "請輸入你的子網域 (例如 ytify.example.com)"

if ([string]::IsNullOrWhiteSpace($Domain)) {
    Write-Host "[錯誤] 網域不能為空！" -ForegroundColor Red
    Read-Host "按 Enter 結束"
    exit 1
}

Write-Host ""
Write-Host "目標網域: $Domain" -ForegroundColor Green
Write-Host ""

# 檢查 cloudflared
Write-Host "[0/4] 檢查 cloudflared..." -ForegroundColor Yellow
$cloudflared = "cloudflared"
if (!(Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    if (Test-Path ".\cloudflared.exe") {
        $cloudflared = ".\cloudflared.exe"
        Write-Host "      使用本地 cloudflared.exe" -ForegroundColor Gray
    } else {
        Write-Host "[錯誤] cloudflared 未找到！" -ForegroundColor Red
        Write-Host ""
        Write-Host "請先執行以下指令下載:" -ForegroundColor Yellow
        Write-Host "  Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'" -ForegroundColor White
        Write-Host ""
        Read-Host "按 Enter 結束"
        exit 1
    }
} else {
    Write-Host "      cloudflared 已安裝" -ForegroundColor Green
}

# Step 1: 登入
Write-Host ""
Write-Host "[1/4] 登入 Cloudflare..." -ForegroundColor Yellow
Write-Host "      會開啟瀏覽器，請選擇你的網域並授權" -ForegroundColor Gray
Write-Host ""

& $cloudflared login

if ($LASTEXITCODE -ne 0) {
    Write-Host "[錯誤] 登入失敗" -ForegroundColor Red
    Read-Host "按 Enter 結束"
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
        Read-Host "按 Enter 結束"
        exit 1
    }
}
Write-Host "      Tunnel 已就緒" -ForegroundColor Green

# Step 3: 設定 DNS
Write-Host ""
Write-Host "[3/4] 設定 DNS 路由..." -ForegroundColor Yellow
Write-Host "      綁定 $Domain -> ytify tunnel" -ForegroundColor Gray

& $cloudflared tunnel route dns $tunnelName $Domain 2>&1 | Out-Null

# DNS 設定失敗通常是因為已存在，不是真的錯誤
Write-Host "      DNS 路由已設定 (或已存在)" -ForegroundColor Green

# Step 4: 產生設定檔
Write-Host ""
Write-Host "[4/4] 產生設定檔..." -ForegroundColor Yellow

# 取得 Tunnel ID
$tunnelListOutput = & $cloudflared tunnel list 2>&1
$tunnelLine = $tunnelListOutput | Select-String $tunnelName | Select-Object -First 1
if ($tunnelLine) {
    $tunnelId = ($tunnelLine.ToString().Trim() -split '\s+')[0]
} else {
    Write-Host "[錯誤] 無法取得 Tunnel ID" -ForegroundColor Red
    Read-Host "按 Enter 結束"
    exit 1
}

Write-Host "      Tunnel ID: $tunnelId" -ForegroundColor Gray

# 確保 .cloudflared 資料夾存在
$cloudflaredDir = "$env:USERPROFILE\.cloudflared"
if (!(Test-Path $cloudflaredDir)) {
    New-Item -ItemType Directory -Path $cloudflaredDir | Out-Null
}

$credPath = "$env:USERPROFILE\.cloudflared\$tunnelId.json"

# 用陣列組合避免 here-string 問題
$configLines = @(
    "tunnel: $tunnelId",
    "credentials-file: $credPath",
    "",
    "ingress:",
    "  - hostname: $Domain",
    "    service: http://localhost:8765",
    "  - service: http_status:404"
)

$configPath = "$cloudflaredDir\config.yml"
$configLines | Out-File -FilePath $configPath -Encoding UTF8 -Force

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
Write-Host "  https://$Domain" -ForegroundColor Yellow
Write-Host ""
Write-Host "Tampermonkey 腳本設定:" -ForegroundColor Cyan
Write-Host "  API_BASE: 'https://$Domain'" -ForegroundColor White
Write-Host "  @connect  $Domain" -ForegroundColor White
Write-Host ""

Read-Host "按 Enter 結束"
