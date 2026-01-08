@echo off
chcp 65001 >nul
title ytify - YouTube 下載工具

echo ══════════════════════════════════════════════════
echo   ytify - YouTube 下載工具
echo ══════════════════════════════════════════════════
echo.

:: ========== 檢查 Python ==========
echo [1/3] 檢查 Python...
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
echo [2/3] 檢查 Python 依賴...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [*] 正在安裝依賴...
    pip install -r requirements.txt -q
    if errorlevel 1 (
        echo [錯誤] 安裝依賴失敗！
        pause
        exit /b 1
    )
)
echo [OK] Python 依賴已就緒

:: ========== 檢查 FFmpeg ==========
echo.
echo [3/3] 檢查 FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [警告] FFmpeg 未安裝，下載的影片可能沒有聲音
    echo        安裝方式: winget install FFmpeg
) else (
    echo [OK] FFmpeg 已安裝
)

:: ========== 建立必要目錄 ==========
if not exist "logs" mkdir logs
if not exist "downloads" mkdir downloads

echo.
echo ══════════════════════════════════════════════════
echo   啟動服務
echo ══════════════════════════════════════════════════
echo.

:: ========== 檢查/安裝 PM2 ==========
pm2 --version >nul 2>&1
if errorlevel 1 (
    echo [*] PM2 未安裝，檢查 Node.js...
    node --version >nul 2>&1
    if errorlevel 1 (
        echo [提示] Node.js 未安裝，使用直接啟動模式
        echo        關閉此視窗會停止服務
        echo.
        echo        如需背景執行，請先安裝 Node.js:
        echo        https://nodejs.org/
        echo.
        echo ──────────────────────────────────────────────────
        echo   服務網址: http://localhost:8765
        echo ──────────────────────────────────────────────────
        echo.
        python main.py
        pause
        exit /b
    )
    echo [*] 正在安裝 PM2...
    call npm install -g pm2 --silent
    if errorlevel 1 (
        echo [警告] PM2 安裝失敗，使用直接啟動模式
        echo.
        python main.py
        pause
        exit /b
    )
    echo [OK] PM2 安裝完成
)

:: ========== PM2 啟動 ==========
echo [*] 使用 PM2 守護進程啟動...
echo.

:: 檢查是否已在運行
pm2 describe ytify >nul 2>&1
if not errorlevel 1 (
    echo [!] ytify 已在運行，重啟中...
    pm2 restart ytify
) else (
    pm2 start ecosystem.config.js
)

echo.
echo ══════════════════════════════════════════════════
echo   服務已啟動！
echo ══════════════════════════════════════════════════
echo.
echo   網址: http://localhost:8765
echo.
echo   PM2 指令:
echo     pm2 status       - 查看狀態
echo     pm2 logs ytify   - 查看日誌
echo     pm2 stop ytify   - 停止服務
echo     pm2 restart ytify - 重啟服務
echo.
pm2 status
echo.
pause
