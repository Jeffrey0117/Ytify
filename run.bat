@echo off
chcp 65001 >nul
title ytify - YouTube 下載工具
cd /d "%~dp0"

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
echo   網址: http://localhost:8765
echo.
echo   按 Ctrl+C 停止服務
echo ══════════════════════════════════════════════════
echo.

python main.py
pause
