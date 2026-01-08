@echo off
chcp 65001 >nul 2>&1
title ytify
cd /d "%~dp0"

echo.
echo   ╔═══════════════════════════════════════════╗
echo   ║     ytify - YouTube Downloader API        ║
echo   ╚═══════════════════════════════════════════╝
echo.

:: Check if cloudflared exists and tunnel is configured
set HAS_TUNNEL=0
where cloudflared >nul 2>&1
if %errorlevel% equ 0 (
    cloudflared tunnel list 2>nul | findstr /i "ytify" >nul 2>&1
    if %errorlevel% equ 0 (
        set HAS_TUNNEL=1
    )
)

:: Menu
echo   [1] Start ytify only (localhost:8765)
if %HAS_TUNNEL% equ 1 (
    echo   [2] Start ytify + Cloudflare Tunnel
)
echo   [Q] Quit
echo.
set /p choice="  Select: "

if /i "%choice%"=="q" exit /b 0
if /i "%choice%"=="1" goto :start_local
if /i "%choice%"=="2" if %HAS_TUNNEL% equ 1 goto :start_tunnel

:: Default to local
:start_local
echo.
echo   Starting ytify API...
echo   URL: http://localhost:8765
echo.
python main.py
goto :end

:start_tunnel
echo.
echo   Starting ytify API + Cloudflare Tunnel...
echo.

:: Start ytify in background
start /min "ytify" cmd /c "cd /d %~dp0 && python main.py"
timeout /t 2 /nobreak >nul

:: Start tunnel
echo   Local:  http://localhost:8765
echo   Public: https://ytify.isnowfriend.com
echo.
echo   (Press Ctrl+C to stop)
echo.
cloudflared tunnel run ytify

:end
pause
