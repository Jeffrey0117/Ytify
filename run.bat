@echo off
chcp 65001 >nul
title Ytify - YouTube 下載工具
cd /d "%~dp0"

:: ========== 檢查 winget ==========
winget --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 需要 winget 來自動安裝依賴
    echo.
    echo 請先更新 Windows 或手動安裝 App Installer:
    echo https://aka.ms/getwinget
    echo.
    pause
    exit /b 1
)

echo ══════════════════════════════════════════════════
echo   Ytify - YouTube 下載工具
echo ══════════════════════════════════════════════════
echo.
echo   [1] Docker - 需 4GB+ RAM, 自動更新
echo   [2] Python - 最輕量, 手動更新
echo   [3] Python + 自動更新 (推薦)
echo.
echo   * 自動偵測並安裝 Python、FFmpeg、Git
echo   * 已安裝但沒加 PATH? 沒關係，會自動找到
echo.
echo   不確定選哪個? 直接按 Enter 選 3
echo.
set /p MODE="請選擇 (1/2/3) [預設 3]: "

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
    :: 嘗試多個可能的路徑
    if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    ) else if exist "%LOCALAPPDATA%\Docker\Docker Desktop.exe" (
        start "" "%LOCALAPPDATA%\Docker\Docker Desktop.exe"
    ) else (
        start "" "Docker Desktop"
    )
    echo [*] 等待 Docker 啟動 (約 60 秒)...
    set DOCKER_WAIT=0
    :WAIT_DOCKER
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if not errorlevel 1 goto :DOCKER_READY
    set /a DOCKER_WAIT+=1
    if %DOCKER_WAIT% lss 12 (
        echo     等待中... %DOCKER_WAIT%/12
        goto :WAIT_DOCKER
    )
    echo [錯誤] Docker 啟動失敗！請手動啟動 Docker Desktop
    pause
    exit /b 1
)
:DOCKER_READY
echo [OK] Docker 運行中

:: 建立必要目錄
if not exist "downloads" mkdir downloads
if not exist "data" mkdir data

:: 判斷使用 docker-compose 還是 docker compose
set DOCKER_COMPOSE=docker compose
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo [錯誤] 找不到 docker compose 指令！
        pause
        exit /b 1
    )
    set DOCKER_COMPOSE=docker-compose
)

:: 啟動服務
echo.
echo [2/3] 拉取最新 image...
%DOCKER_COMPOSE% pull >nul 2>&1
if errorlevel 1 (
    echo [警告] 無法拉取最新 image，使用本地版本
) else (
    echo [OK] 已拉取最新版本
)

echo.
echo [3/3] 啟動 Docker 容器...
%DOCKER_COMPOSE% up -d >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 啟動失敗！
    echo.
    echo 嘗試查看錯誤:
    %DOCKER_COMPOSE% up -d
    pause
    exit /b 1
)

:: 等待服務啟動
echo [*] 等待服務啟動...
timeout /t 5 /nobreak >nul

:: 檢查服務狀態
%DOCKER_COMPOSE% ps 2>nul
echo.

:: 測試連線 (用 PowerShell 避免 curl 未安裝問題)
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8765/health' -UseBasicParsing -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
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
echo   Ytify:      http://localhost:8765
echo   Watchtower: 每 5 分鐘自動檢查更新
echo.
echo   查看日誌: %DOCKER_COMPOSE% logs -f ytify
echo   停止服務: %DOCKER_COMPOSE% down
echo.
pause
exit /b 0

:PYTHON_MODE
echo.
echo ══════════════════════════════════════════════════
echo   Python 模式
echo ══════════════════════════════════════════════════
echo.

:: ========== 尋找 Python ==========
call :FIND_PYTHON
if errorlevel 1 (
    pause
    exit /b 1
)

:: ========== 停止現有服務 ==========
echo [0/4] 停止現有服務...
taskkill /f /fi "WINDOWTITLE eq ytify-server*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq ytify-tunnel*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [OK] 已清理

:: ========== 檢查/安裝 Python 依賴 ==========
echo.
echo [1/4] Checking Python dependencies...
call :CHECK_DEPS
echo [OK] Python dependencies ready

:: ========== 檢查 FFmpeg ==========
call :FIND_FFMPEG

:: ========== 檢查 Cloudflared ==========
echo.
echo [3/4] 檢查 Cloudflared...
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

:: ========== 尋找 Python ==========
call :FIND_PYTHON
if errorlevel 1 (
    pause
    exit /b 1
)

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

:: ========== 檢查/安裝 Python 依賴 ==========
echo.
echo [2/5] Checking Python dependencies...
call :CHECK_DEPS
echo [OK] Python dependencies ready

:: ========== 檢查 FFmpeg ==========
call :FIND_FFMPEG

:: ========== 設定自動更新 ==========
echo.
echo [4/5] 設定自動更新排程...
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

:: Start ytify server
echo [*] Starting ytify server...
start "ytify-server" /min cmd /c "cd /d %~dp0 && python main.py"

:: Start auto-update loop (background)
echo [*] Starting auto-update loop...
start "ytify-updater" /min cmd /c "cd /d %~dp0 && call auto-update-loop.bat"

:: Wait and check server (用 PowerShell 避免 curl 未安裝問題)
echo [*] Waiting for server...
set RETRY=0
:CHECK_SERVER
timeout /t 2 /nobreak >nul
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8765/health' -UseBasicParsing -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    set /a RETRY+=1
    if %RETRY% lss 5 (
        echo     Retry %RETRY%/5...
        goto :CHECK_SERVER
    )
    echo [ERROR] ytify server failed to start!
    echo.
    echo Please check:
    echo   1. Install deps: pip install -r requirements.txt
    echo   2. Run manually: python main.py
    echo.
    pause
    exit /b 1
)
echo [OK] ytify server ready

:: 檢查 Cloudflared
cloudflared --version >nul 2>&1
if not errorlevel 1 (
    echo [*] 啟動 Cloudflare Tunnel...
    start "ytify-tunnel" /min cmd /c "cloudflared tunnel run ytify"
    timeout /t 2 /nobreak >nul
    echo.
    echo   Local:  http://localhost:8765
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
exit /b 0

:: ══════════════════════════════════════════════════
:: 函數: 尋找並設定 Python
:: ══════════════════════════════════════════════════
:FIND_PYTHON
echo [*] 檢查 Python...

:: 先檢查 PATH 裡有沒有
python --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [OK] Python %%i
    exit /b 0
)

:: PATH 沒有，嘗試尋找常見安裝位置
echo [!] Python 不在 PATH 中，正在尋找...
set PYTHON_FOUND=

:: 檢查 %LOCALAPPDATA%\Programs\Python (Windows Store / 標準安裝)
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%d\python.exe" (
        set "PYTHON_FOUND=%%d"
    )
)

:: 檢查 %APPDATA%\Python
if not defined PYTHON_FOUND (
    for /d %%d in ("%APPDATA%\Python\Python*") do (
        if exist "%%d\python.exe" (
            set "PYTHON_FOUND=%%d"
        )
    )
)

:: 檢查 C:\Python*
if not defined PYTHON_FOUND (
    for /d %%d in ("C:\Python*") do (
        if exist "%%d\python.exe" (
            set "PYTHON_FOUND=%%d"
        )
    )
)

:: 檢查 C:\Program Files\Python*
if not defined PYTHON_FOUND (
    for /d %%d in ("C:\Program Files\Python*") do (
        if exist "%%d\python.exe" (
            set "PYTHON_FOUND=%%d"
        )
    )
)

:: 檢查 %USERPROFILE%\AppData\Local\Microsoft\WindowsApps
if not defined PYTHON_FOUND (
    if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
        set "PYTHON_FOUND=%LOCALAPPDATA%\Microsoft\WindowsApps"
    )
)

:: 找到了！
if defined PYTHON_FOUND (
    echo [OK] 找到 Python: %PYTHON_FOUND%
    echo [*] 加入 PATH...
    set "PATH=%PYTHON_FOUND%;%PYTHON_FOUND%\Scripts;%PATH%"

    :: 驗證
    python --version >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [OK] Python %%i 已就緒
        exit /b 0
    )
)

:: 都找不到，安裝新的
echo [!] 找不到 Python，正在安裝...
winget install Python.Python.3.11 --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo [錯誤] Python 安裝失敗！
    exit /b 1
)

:: 安裝後再找一次
for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%d\python.exe" (
        set "PYTHON_FOUND=%%d"
    )
)

if defined PYTHON_FOUND (
    echo [OK] Python 已安裝: %PYTHON_FOUND%
    set "PATH=%PYTHON_FOUND%;%PYTHON_FOUND%\Scripts;%PATH%"
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [OK] Python %%i 已就緒
    exit /b 0
)

echo [!] 請重新開啟命令提示字元後再執行
exit /b 1

:: ══════════════════════════════════════════════════
:: 函數: 尋找並設定 FFmpeg
:: ══════════════════════════════════════════════════
:FIND_FFMPEG
echo.
echo [*] 檢查 FFmpeg...

:: 先檢查 PATH 裡有沒有
ffmpeg -version >nul 2>&1
if not errorlevel 1 (
    echo [OK] FFmpeg 已安裝
    exit /b 0
)

:: PATH 沒有，嘗試尋找常見安裝位置
echo [!] FFmpeg 不在 PATH 中，正在尋找...
set FFMPEG_FOUND=

:: winget 安裝的 FFmpeg 通常在這
if exist "C:\ffmpeg\bin\ffmpeg.exe" (
    set "FFMPEG_FOUND=C:\ffmpeg\bin"
)

:: 檢查 C:\Program Files\ffmpeg
if not defined FFMPEG_FOUND (
    if exist "C:\Program Files\ffmpeg\bin\ffmpeg.exe" (
        set "FFMPEG_FOUND=C:\Program Files\ffmpeg\bin"
    )
)

:: 檢查 C:\Program Files (x86)\ffmpeg
if not defined FFMPEG_FOUND (
    if exist "C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe" (
        set "FFMPEG_FOUND=C:\Program Files (x86)\ffmpeg\bin"
    )
)

:: 檢查 %LOCALAPPDATA%\Microsoft\WinGet\Packages 下的 ffmpeg
if not defined FFMPEG_FOUND (
    for /d %%d in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*") do (
        if exist "%%d\ffmpeg-*\bin\ffmpeg.exe" (
            for /d %%e in ("%%d\ffmpeg-*") do (
                if exist "%%e\bin\ffmpeg.exe" (
                    set "FFMPEG_FOUND=%%e\bin"
                )
            )
        )
    )
)

:: 檢查 scoop 安裝位置
if not defined FFMPEG_FOUND (
    if exist "%USERPROFILE%\scoop\apps\ffmpeg\current\bin\ffmpeg.exe" (
        set "FFMPEG_FOUND=%USERPROFILE%\scoop\apps\ffmpeg\current\bin"
    )
)

:: 檢查 chocolatey 安裝位置
if not defined FFMPEG_FOUND (
    if exist "C:\ProgramData\chocolatey\bin\ffmpeg.exe" (
        set "FFMPEG_FOUND=C:\ProgramData\chocolatey\bin"
    )
)

:: 找到了！
if defined FFMPEG_FOUND (
    echo [OK] 找到 FFmpeg: %FFMPEG_FOUND%
    echo [*] 加入 PATH...
    set "PATH=%FFMPEG_FOUND%;%PATH%"

    :: 驗證
    ffmpeg -version >nul 2>&1
    if not errorlevel 1 (
        echo [OK] FFmpeg 已就緒
        exit /b 0
    )
)

:: 都找不到，安裝新的
echo [!] 找不到 FFmpeg，正在安裝...
winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo [警告] FFmpeg 安裝失敗，部分功能可能無法使用
    exit /b 0
)

:: 安裝後再找一次
for /d %%d in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*") do (
    for /d %%e in ("%%d\ffmpeg-*") do (
        if exist "%%e\bin\ffmpeg.exe" (
            set "FFMPEG_FOUND=%%e\bin"
        )
    )
)

if defined FFMPEG_FOUND (
    echo [OK] FFmpeg 已安裝: %FFMPEG_FOUND%
    set "PATH=%FFMPEG_FOUND%;%PATH%"
    echo [OK] FFmpeg 已就緒
    exit /b 0
)

echo [警告] FFmpeg 已安裝但需重啟終端生效
exit /b 0

:: ══════════════════════════════════════════════════
:: 函數: 檢查並安裝 Python 依賴
:: 用 requirements.txt 的 hash 來判斷是否需要重新安裝
:: ══════════════════════════════════════════════════
:CHECK_DEPS
set "DEPS_MARKER=%~dp0.deps-installed"
set "REQ_FILE=%~dp0requirements.txt"

:: 計算 requirements.txt 的 hash
for /f "skip=1 delims=" %%h in ('certutil -hashfile "%REQ_FILE%" MD5 2^>nul') do (
    if not defined CURRENT_HASH set "CURRENT_HASH=%%h"
)

:: 讀取已存的 hash
set "SAVED_HASH="
if exist "%DEPS_MARKER%" (
    set /p SAVED_HASH=<"%DEPS_MARKER%"
)

:: 比對 hash
if "%CURRENT_HASH%"=="%SAVED_HASH%" (
    echo [*] Dependencies unchanged, skipping install
    set "CURRENT_HASH="
    exit /b 0
)

:: Hash 不同或標記檔不存在，執行安裝
echo [*] Installing dependencies...
pip install -r "%REQ_FILE%" -q --disable-pip-version-check
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    set "CURRENT_HASH="
    exit /b 1
)

:: 安裝成功，儲存 hash
echo %CURRENT_HASH%>"%DEPS_MARKER%"
set "CURRENT_HASH="
exit /b 0
