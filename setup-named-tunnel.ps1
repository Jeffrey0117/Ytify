# ytify Named Tunnel Setup Script
# Use your own domain (e.g., ytify.example.com) instead of random URL

# Prevent window from closing on error
trap {
    Write-Host ""
    Write-Host "[ERROR] $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ytify Named Tunnel Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Interactive domain input
$Domain = Read-Host "Enter your subdomain (e.g., ytify.example.com)"

if ([string]::IsNullOrWhiteSpace($Domain)) {
    Write-Host "[ERROR] Domain cannot be empty!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Target domain: $Domain" -ForegroundColor Green
Write-Host ""

# Check cloudflared
Write-Host "[0/4] Checking cloudflared..." -ForegroundColor Yellow
$cloudflared = "cloudflared"
if (!(Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    if (Test-Path ".\cloudflared.exe") {
        $cloudflared = ".\cloudflared.exe"
        Write-Host "      Using local cloudflared.exe" -ForegroundColor Gray
    } else {
        Write-Host "[ERROR] cloudflared not found!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please download it first:" -ForegroundColor Yellow
        Write-Host "  Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'" -ForegroundColor White
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "      cloudflared installed" -ForegroundColor Green
}

# Step 1: Login
Write-Host ""
Write-Host "[1/4] Login to Cloudflare..." -ForegroundColor Yellow
Write-Host "      Browser will open, please select your domain and authorize" -ForegroundColor Gray
Write-Host ""

& $cloudflared login

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Login failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "      Login successful" -ForegroundColor Green

# Step 2: Create Tunnel
Write-Host ""
Write-Host "[2/4] Creating Tunnel..." -ForegroundColor Yellow
$tunnelName = "ytify"

# Check if exists
$existingTunnel = & $cloudflared tunnel list 2>&1 | Select-String $tunnelName
if ($existingTunnel) {
    Write-Host "      Tunnel '$tunnelName' already exists, skipping" -ForegroundColor Gray
} else {
    & $cloudflared tunnel create $tunnelName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create tunnel" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Host "      Tunnel ready" -ForegroundColor Green

# Step 3: Setup DNS
Write-Host ""
Write-Host "[3/4] Setting up DNS route..." -ForegroundColor Yellow
Write-Host "      Binding $Domain -> ytify tunnel" -ForegroundColor Gray

& $cloudflared tunnel route dns $tunnelName $Domain 2>&1 | Out-Null

Write-Host "      DNS route configured (or already exists)" -ForegroundColor Green

# Step 4: Generate config file
Write-Host ""
Write-Host "[4/4] Generating config file..." -ForegroundColor Yellow

# Get Tunnel ID
$tunnelListOutput = & $cloudflared tunnel list 2>&1
$tunnelLine = $tunnelListOutput | Select-String $tunnelName | Select-Object -First 1
if ($tunnelLine) {
    $tunnelId = ($tunnelLine.ToString().Trim() -split '\s+')[0]
} else {
    Write-Host "[ERROR] Cannot get Tunnel ID" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "      Tunnel ID: $tunnelId" -ForegroundColor Gray

# Ensure .cloudflared folder exists
$cloudflaredDir = "$env:USERPROFILE\.cloudflared"
if (!(Test-Path $cloudflaredDir)) {
    New-Item -ItemType Directory -Path $cloudflaredDir | Out-Null
}

$credPath = "$env:USERPROFILE\.cloudflared\$tunnelId.json"

# Build config using array to avoid here-string issues
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

Write-Host "      Config saved: $configPath" -ForegroundColor Green

# Done
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start:" -ForegroundColor Cyan
Write-Host "  .\start-named-tunnel.bat" -ForegroundColor White
Write-Host ""
Write-Host "Your fixed URL:" -ForegroundColor Cyan
Write-Host "  https://$Domain" -ForegroundColor Yellow
Write-Host ""
Write-Host "Tampermonkey script settings:" -ForegroundColor Cyan
Write-Host "  API_BASE: 'https://$Domain'" -ForegroundColor White
Write-Host "  @connect  $Domain" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
