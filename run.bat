@echo off
chcp 65001 >nul
title ytify - YouTube 下載工具
cd /d "%~dp0"

echo ══════════════════════════════════════════════════
echo   ytify - YouTube 下載工具
echo ══════════════════════════════════════════════════
echo.
echo   [1] Docker 模式（推薦，含自動更新）
echo   [2] Python 模式（傳統）
echo.
set /p MODE="請選擇啟動模式 (1/2): "

if "%MODE%"=="1" goto :DOCKER_MODE
if "%MODE%"=="2" goto :PYTHON_MODE
goto :DOCKER_MODE

:DOCKER_MODE
echo.
echo ══════════════════════════════════════════════════
echo   Docker 模式
echo ══════════════════════════════════════════════════
echo.

:: 檢查 Docker
echo [1/3] 檢查 Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [!] Docker 未安裝，正在安裝...
    echo.
    winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [錯誤] 安裝失敗！請手動安裝 Docker Desktop
        echo 下載: https://www.docker.com/products/docker-desktop
        pause
        exit /b 1
    )
    echo.
    echo [OK] Docker 已安裝
    echo [!] 請啟動 Docker Desktop 後重新執行此腳本
    pause
    exit /b 0
)
echo [OK] Docker 已安裝

:: 檢查 Docker 是否運行
docker info >nul 2>&1
if errorlevel 1 (
    echo [!] Docker 未運行，嘗試啟動...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo [*] 等待 Docker 啟動（約 30 秒）...
    timeout /t 30 /nobreak >nul
    docker info >nul 2>&1
    if errorlevel 1 (
        echo [錯誤] Docker 啟動失敗！請手動啟動 Docker Desktop
        pause
        exit /b 1
    )
)
echo [OK] Docker 運行中

:: 建立必要目錄
if not exist "downloads" mkdir downloads
if not exist "data" mkdir data

:: 啟動服務
echo.
echo [2/3] 拉取最新 image...
docker-compose pull >nul 2>&1
if errorlevel 1 (
    echo [警告] 無法拉取最新 image，使用本地版本
) else (
    echo [OK] 已拉取最新版本
)

echo.
echo [3/3] 啟動 Docker 容器...
docker-compose up -d >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 啟動失敗！
    echo.
    echo 嘗試查看錯誤:
    docker-compose up -d
    pause
    exit /b 1
)

:: 等待服務啟動
echo [*] 等待服務啟動...
timeout /t 5 /nobreak >nul

:: 檢查服務狀態
docker-compose ps --format "table {{.Name}}\t{{.Status}}" 2>nul
echo.

:: 測試連線
curl -s http://localhost:8765/health >nul 2>&1
if errorlevel 1 (
    echo [警告] 服務可能還在啟動中，請稍後再試
) else (
    echo [OK] 服務已就緒
)

echo.
echo ══════════════════════════════════════════════════
echo   Docker 服務已啟動！
echo ══════════════════════════════════════════════════
echo.
echo   ytify:      http://localhost:8765
echo   Watchtower: 每 5 分鐘自動檢查更新
echo.
echo   查看日誌: docker-compose logs -f ytify
echo   停止服務: docker-compose down
echo.
pause
exit /b 0

:PYTHON_MODE
echo.
echo ══════════════════════════════════════════════════
echo   Python 模式
echo ══════════════════════════════════════════════════
echo.

:: ========== 停止現有服務 ==========
echo [0/4] 停止現有服務...
taskkill /f /fi "WINDOWTITLE eq ytify-server*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq ytify-tunnel*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [OK] 已清理

:: ========== 檢查 Python ==========
echo.
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
