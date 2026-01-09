@echo off
chcp 65001 >nul
title ytify - 停止服務

echo ══════════════════════════════════════════════════
echo   ytify - 停止服務
echo ══════════════════════════════════════════════════
echo.

echo [*] 停止 ytify 服務...
taskkill /f /fi "WINDOWTITLE eq ytify-server*" >nul 2>&1
taskkill /f /im python.exe /fi "WINDOWTITLE eq ytify*" >nul 2>&1

echo [*] 停止自動更新...
taskkill /f /fi "WINDOWTITLE eq ytify-updater*" >nul 2>&1

echo [*] 停止 Cloudflare Tunnel...
taskkill /f /fi "WINDOWTITLE eq ytify-tunnel*" >nul 2>&1
taskkill /f /im cloudflared.exe >nul 2>&1

echo.
echo [OK] 服務已停止
echo.
pause
