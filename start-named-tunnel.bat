@echo off
chcp 65001 >nul
title ytify Server + Named Tunnel

echo ========================================
echo   ytify - YouTube Downloader API
echo   with Named Tunnel (固定網址)
echo ========================================
echo.

:: 檢查 cloudflared
where cloudflared >nul 2>&1
if %errorlevel% neq 0 (
    if exist cloudflared.exe (
        set CLOUDFLARED=cloudflared.exe
    ) else (
        echo [錯誤] cloudflared 未找到！
        pause
        exit /b 1
    )
) else (
    set CLOUDFLARED=cloudflared
)

:: 檢查設定檔
if not exist "%USERPROFILE%\.cloudflared\config.yml" (
    echo [錯誤] 設定檔不存在！
    echo 請先執行: powershell -ExecutionPolicy Bypass -File setup-named-tunnel.ps1 -Domain 你的網域
    pause
    exit /b 1
)

echo [1/2] 啟動 ytify API Server...
start "ytify API" cmd /c "python main.py"

:: 等待 API 啟動
timeout /t 3 /nobreak >nul

echo [2/2] 啟動 Named Tunnel...
echo.

%CLOUDFLARED% tunnel run ytify

pause
