@echo off
chcp 65001 >nul
title ytify - One-Click Installer
cd /d "%~dp0"

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     ytify - YouTube Downloader Setup      ║
echo  ║                                           ║
echo  ║  One-click install for Windows            ║
echo  ╚═══════════════════════════════════════════╝
echo.

:: Check Python
echo [1/4] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo       [ERROR] Python not found!
    echo.
    echo       Please install Python first:
    echo       https://www.python.org/downloads/
    echo.
    echo       Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)
echo       [OK] Python found
echo.

:: Check FFmpeg
echo [2/4] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo       [WARNING] FFmpeg not found
    echo       Video/audio merging may not work properly
    echo.
    echo       Install with: winget install FFmpeg
    echo       Or download from: https://ffmpeg.org/download.html
    echo.
    set FFMPEG_MISSING=1
) else (
    echo       [OK] FFmpeg found
)
echo.

:: Install Python dependencies
echo [3/4] Installing Python dependencies...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo       [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo       [OK] Dependencies installed
echo.

:: Create downloads folder
echo [4/4] Setting up...
if not exist downloads mkdir downloads
echo       [OK] Ready
echo.

echo  ╔═══════════════════════════════════════════╗
echo  ║           Installation Complete!          ║
echo  ╚═══════════════════════════════════════════╝
echo.
echo  Next steps:
echo.
echo  1. Start the server:
echo     Double-click "start.bat"
echo.
echo  2. Install Tampermonkey extension:
echo     https://www.tampermonkey.net/
echo.
echo  3. Install ytify script:
echo     Open scripts/ytify.user.js in browser
echo     -or-
echo     Copy content to Tampermonkey
echo.
echo  4. Open any YouTube video and click the red
echo     "Download" button at bottom right
echo.

if defined FFMPEG_MISSING (
    echo  [!] Remember to install FFmpeg for best results
    echo.
)

pause
