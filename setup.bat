@echo off
chcp 65001 >nul
title ytify 一鍵配置

echo ══════════════════════════════════════════════════
echo   ytify - 一鍵配置腳本
echo ══════════════════════════════════════════════════
echo.

:: 檢查 Python
echo [1/4] 檢查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未找到 Python，請先安裝 Python 3.8+
    echo 下載: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python 已安裝

:: 檢查 Node.js (PM2 需要)
echo [2/4] 檢查 Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未找到 Node.js，PM2 守護進程將無法使用
    echo 下載: https://nodejs.org/
    set NO_PM2=1
) else (
    echo [OK] Node.js 已安裝
)

:: 安裝 Python 依賴
echo [3/4] 安裝 Python 依賴...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [錯誤] 安裝依賴失敗
    pause
    exit /b 1
)
echo [OK] Python 依賴已安裝

:: 安裝 PM2
if not defined NO_PM2 (
    echo [4/4] 安裝 PM2...
    call npm list -g pm2 >nul 2>&1
    if errorlevel 1 (
        call npm install -g pm2 --silent
    )
    echo [OK] PM2 已安裝
) else (
    echo [4/4] 跳過 PM2 安裝
)

:: 建立 logs 目錄
if not exist logs mkdir logs

echo.
echo ══════════════════════════════════════════════════
echo   配置完成！
echo ══════════════════════════════════════════════════
echo.
echo   啟動方式:
echo     方式1: run.bat          (PM2 守護進程)
echo     方式2: start.bat        (直接啟動)
echo.
echo   服務網址: http://localhost:8765
echo.
pause
