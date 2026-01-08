@echo off
chcp 65001 >nul 2>&1
title ytify + Tunnel
cd /d "%~dp0"

echo.
echo   ytify + Cloudflare Tunnel
echo.

start /min "ytify" cmd /c "cd /d %~dp0 && python main.py"
timeout /t 2 /nobreak >nul

echo   Local:  http://localhost:8765
echo   Public: https://ytify.isnowfriend.com
echo.

cloudflared tunnel run ytify
pause
