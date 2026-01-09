@echo off
chcp 65001 >nul
title ytify - YouTube 下載工具
cd /d "%~dp0"

echo ══════════════════════════════════════════════════
echo   ytify - YouTube 下載工具
echo ══════════════════════════════════════════════════
echo.
echo   [1] Docker 模式 (含自動更新, 需較多資源)
echo   [2] Python 模式 (傳統, 手動更新)
echo   [3] Python 模式 + 自動更新 (輕量推薦)
echo.
set /p MODE="請選擇啟動模式 (1/2/3): "

if "%MODE%"=="1" goto :DOCKER_MODE
if "%MODE%"=="2" goto :PYTHON_MODE
if "%MODE%"=="3" goto :PYTHON_AUTO_MODE
goto :PYTHON_AUTO_MODE

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
    echo [*] 等待 Docker 啟動 (約 30 秒)...
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

:: 啟動 Tunnel (如果有安裝)
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
exit /b 0

:PYTHON_AUTO_MODE
echo.
echo ══════════════════════════════════════════════════
echo   Python 模式 + 自動更新
echo ══════════════════════════════════════════════════
echo.

:: ========== 停止現有服務 ==========
echo [0/5] 停止現有服務...
taskkill /f /fi "WINDOWTITLE eq ytify-server*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq ytify-tunnel*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [OK] 已清理

:: ========== 檢查 Git ==========
echo.
echo [1/5] 檢查 Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo [!] Git 未安裝，正在安裝...
    winget install Git.Git --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [錯誤] Git 安裝失敗！
        pause
        exit /b 1
    )
    echo [!] 請重新開啟命令提示字元後再執行
    pause
    exit /b 0
)
echo [OK] Git 已安裝

:: ========== 檢查 Python ==========
echo.
echo [2/5] 檢查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python 未安裝，正在安裝...
    winget install Python.Python.3.11 --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [錯誤] Python 安裝失敗！
        pause
        exit /b 1
    )
    echo [!] 請重新開啟命令提示字元後再執行
    pause
    exit /b 0
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [OK] Python %%i

:: ========== 檢查/安裝 Python 依賴 ==========
echo.
echo [3/5] 檢查 Python 依賴...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [*] 正在安裝依賴...
    pip install -r requirements.txt -q
)
echo [OK] Python 依賴已就緒

:: ========== 檢查 FFmpeg ==========
echo.
echo [4/5] 檢查 FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [!] FFmpeg 未安裝，正在安裝...
    winget install FFmpeg --accept-package-agreements --accept-source-agreements >nul 2>&1
    echo [OK] FFmpeg 已安裝 (需重啟終端生效)
) else (
    echo [OK] FFmpeg 已安裝
)

:: ========== 設定自動更新 ==========
echo.
echo [5/5] 設定自動更新排程...
if not exist "logs" mkdir logs

:: 檢查排程是否已存在
schtasks /query /tn "ytify-auto-update" >nul 2>&1
if errorlevel 1 (
    :: 建立排程
    set YTIFY_PATH=%~dp0
    schtasks /create /tn "ytify-auto-update" /tr "\"%~dp0auto-update.bat\"" /sc minute /mo 5 /f >nul 2>&1
    if errorlevel 1 (
        echo [警告] 無法建立排程 (需系統管理員權限)
        echo        手動設定: 執行 setup-auto-update.bat
    ) else (
        echo [OK] 自動更新排程已建立 (每 5 分鐘)
    )
) else (
    echo [OK] 自動更新排程已存在
)

:: ========== 拉取最新版本 ==========
echo.
echo [*] 檢查更新...
git pull origin main 2>nul
echo [OK] 已同步最新版本

:: ========== 建立必要目錄 ==========
if not exist "downloads" mkdir downloads

echo.
echo ══════════════════════════════════════════════════
echo   啟動服務
echo ══════════════════════════════════════════════════
echo.

:: 啟動 ytify 服務
echo [*] 啟動 ytify 服務...
start "ytify-server" /min cmd /c "cd /d %~dp0 && python main.py"

:: 等待服務啟動並檢查
echo [*] 等待服務啟動...
set RETRY=0
:CHECK_SERVER
timeout /t 2 /nobreak >nul
curl -s http://localhost:8765/health >nul 2>&1
if errorlevel 1 (
    set /a RETRY+=1
    if %RETRY% lss 5 (
        echo     嘗試 %RETRY%/5...
        goto :CHECK_SERVER
    )
    echo [錯誤] ytify 服務啟動失敗!
    echo.
    echo 請檢查:
    echo   1. Python 依賴是否安裝: pip install -r requirements.txt
    echo   2. 查看錯誤訊息: python main.py
    echo.
    pause
    exit /b 1
)
echo [OK] ytify 服務已就緒

:: 檢查 Cloudflared
cloudflared --version >nul 2>&1
if not errorlevel 1 (
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
echo   服務已啟動! (含自動更新)
echo ══════════════════════════════════════════════════
echo.
echo   ytify 服務運行於最小化視窗
echo   每 5 分鐘自動檢查 GitHub 更新
echo.
echo   更新日誌: logs\auto-update.log
echo   停止服務: stop.bat
echo   停用自動更新: schtasks /delete /tn "ytify-auto-update" /f
echo.
pause
