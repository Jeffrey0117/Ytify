@echo off
chcp 65001 >nul 2>&1
title ytify Launcher

echo ==================================================
echo   ytify - All Services Launcher
echo ==================================================
echo.

cd /d "%~dp0"

REM Start ytify
echo [1/2] Starting ytify API...
start /min "ytify_api" cmd /c "cd /d %~dp0 && python main.py"
timeout /t 3 /nobreak >nul

REM Start Cloudflare Tunnel
echo [2/2] Starting Cloudflare Tunnel...
start /min "cloudflare_tunnel" cmd /c "cloudflared tunnel run ytify"

echo.
echo ==================================================
echo   All services started!
echo.
echo   ytify API:    http://localhost:8765
echo   Public URL:   https://ytify.isnowfriend.com
echo ==================================================
echo.
echo Press any key to close this window...
pause >nul
