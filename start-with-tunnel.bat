@echo off
chcp 65001 >nul
title ytify Server + Cloudflare Tunnel

echo ========================================
echo   ytify - YouTube Downloader API
echo   with Cloudflare Tunnel
echo ========================================
echo.

:: 檢查 cloudflared
where cloudflared >nul 2>&1
if %errorlevel% neq 0 (
    if exist cloudflared.exe (
        set CLOUDFLARED=cloudflared.exe
    ) else (
        echo [錯誤] cloudflared 未找到！
        echo 請先執行 server-setup.ps1 或手動下載 cloudflared
        pause
        exit /b 1
    )
) else (
    set CLOUDFLARED=cloudflared
)

echo [1/2] 啟動 ytify API Server...
start "ytify API" cmd /c "python main.py"

:: 等待 API 啟動
timeout /t 3 /nobreak >nul

echo [2/2] 啟動 Cloudflare Tunnel...
echo.
echo ========================================
echo   複製下方的 Tunnel 網址
echo   貼到 Tampermonkey 腳本的 API_BASE
echo ========================================
echo.

%CLOUDFLARED% tunnel --url http://localhost:8765

pause
