@echo off
chcp 65001 >nul 2>&1
title ytify
cd /d "%~dp0"

echo.
echo   ytify - YouTube Downloader API
echo   http://localhost:8765
echo.

python main.py
pause
