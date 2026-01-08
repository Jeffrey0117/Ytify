@echo off
chcp 65001 >nul
title ytify - YouTube 下載工具
cd /d "%~dp0"

echo ══════════════════════════════════════════════════
echo   ytify - YouTube 下載工具
echo ══════════════════════════════════════════════════
echo.

:: ========== 檢查 Python ==========
echo [1/4] 檢查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未找到 Python！
    echo.
    echo 請先安裝 Python 3.8+
    echo 下載: https://www.python.org/downloads/
    echo 安裝時記得勾選 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [OK] Python %%i

:: ========== 檢查/安裝 Python 依賴 ==========
echo.
echo [2/4] 檢查 Python 依賴...
set NEED_INSTALL=0

pip show fastapi >nul 2>&1
if errorlevel 1 set NEED_INSTALL=1

pip show uvicorn >nul 2>&1
if errorlevel 1 set NEED_INSTALL=1

pip show yt-dlp >nul 2>&1
if errorlevel 1 set NEED_INSTALL=1

pip show slowapi >nul 2>&1
if errorlevel 1 set NEED_INSTALL=1

if %NEED_INSTALL%==1 (
    echo [*] 正在安裝依賴...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [錯誤] 安裝依賴失敗！
        pause
        exit /b 1
    )
)
echo [OK] Python 依賴已就緒

:: ========== 檢查 FFmpeg ==========
echo.
echo [3/4] 檢查 FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [警告] FFmpeg 未安裝，下載的影片可能沒有聲音
    echo        安裝方式: winget install FFmpeg
) else (
    echo [OK] FFmpeg 已安裝
)

:: ========== 檢查 Cloudflared ==========
echo.
echo [4/4] 檢查 Cloudflared...
cloudflared --version >nul 2>&1
if errorlevel 1 (
    echo [警告] Cloudflared 未安裝，無法開啟外網
    echo        安裝方式: winget install Cloudflare.cloudflared
    set NO_TUNNEL=1
) else (
    echo [OK] Cloudflared 已安裝
)

:: ========== 建立必要目錄 ==========
if not exist "logs" mkdir logs
if not exist "downloads" mkdir downloads

echo.
echo ══════════════════════════════════════════════════
echo   啟動服務
echo ══════════════════════════════════════════════════
echo.

:: 啟動 ytify 服務
echo [*] 啟動 ytify 服務...
start "ytify-server" /min cmd /c "cd /d %~dp0 && python main.py"
timeout /t 3 /nobreak >nul

:: 啟動 Tunnel（如果有安裝）
if not defined NO_TUNNEL (
    echo [*] 啟動 Cloudflare Tunnel...
    start "ytify-tunnel" /min cmd /c "cloudflared tunnel run ytify"
    timeout /t 2 /nobreak >nul
    echo.
    echo   Local:  http://localhost:8765
    echo   Public: https://ytify.isnowfriend.com
) else (
    echo.
    echo   Local:  http://localhost:8765
)

echo.
echo ══════════════════════════════════════════════════
echo   服務已啟動！
echo ══════════════════════════════════════════════════
echo.
echo   ytify 服務運行於最小化視窗
echo   關閉此視窗不會停止服務
echo.
echo   停止服務請執行: stop.bat
echo.
pause
