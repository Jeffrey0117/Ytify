@echo off
chcp 65001 >nul
title ytify + Cloudflare Tunnel
cd /d "%~dp0"

echo ══════════════════════════════════════════════════
echo   ytify + Cloudflare Tunnel
echo ══════════════════════════════════════════════════
echo.

:: ========== 檢查 Python ==========
echo [1/2] 檢查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未找到 Python！
    pause
    exit /b 1
)
echo [OK] Python 已安裝

:: ========== 檢查 cloudflared ==========
echo.
echo [2/2] 檢查 Cloudflared...
cloudflared --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未找到 cloudflared！
    echo.
    echo 請先安裝: winget install Cloudflare.cloudflared
    pause
    exit /b 1
)
echo [OK] Cloudflared 已安裝

:: ========== 檢查/安裝 Python 依賴 ==========
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo.
    echo [*] 正在安裝 Python 依賴...
    pip install -r requirements.txt -q
)

:: ========== 建立必要目錄 ==========
if not exist "logs" mkdir logs
if not exist "downloads" mkdir downloads

echo.
echo ══════════════════════════════════════════════════
echo   啟動服務
echo ══════════════════════════════════════════════════
echo.

:: 在新視窗啟動 ytify
echo [*] 啟動 ytify 服務...
start "ytify-server" /min cmd /c "cd /d %~dp0 && python main.py"

:: 等待服務啟動
echo [*] 等待服務啟動...
timeout /t 3 /nobreak >nul

echo [OK] ytify 服務已啟動
echo.
echo [*] 啟動 Cloudflare Tunnel...
echo.
echo   Local:  http://localhost:8765
echo.
echo   按 Ctrl+C 停止 Tunnel
echo ══════════════════════════════════════════════════
echo.

cloudflared tunnel run ytify
pause
