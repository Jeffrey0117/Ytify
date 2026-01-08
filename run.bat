@echo off
chcp 65001 >nul
title ytify

:: 檢查是否已安裝
if not exist "logs" (
    echo 首次執行，正在配置...
    call setup.bat
)

:: 檢查 PM2
pm2 --version >nul 2>&1
if errorlevel 1 (
    echo [提示] PM2 未安裝，使用直接啟動模式
    echo.
    python main.py
    exit /b
)

:: 使用 PM2 啟動
echo ══════════════════════════════════════════════════
echo   ytify - 啟動服務
echo ══════════════════════════════════════════════════
echo.

:: 檢查是否已在運行
pm2 describe ytify >nul 2>&1
if not errorlevel 1 (
    echo [!] ytify 已在運行，重啟中...
    pm2 restart ytify
) else (
    echo [*] 啟動 ytify...
    pm2 start ecosystem.config.js
)

echo.
echo [OK] 服務已啟動！
echo.
echo   網址: http://localhost:8765
echo.
echo   常用指令:
echo     pm2 status       - 查看狀態
echo     pm2 logs ytify   - 查看日誌
echo     pm2 stop ytify   - 停止服務
echo     pm2 restart ytify - 重啟服務
echo.
pm2 status
