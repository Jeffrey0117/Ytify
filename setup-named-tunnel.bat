@echo off
chcp 65001 >nul
title ytify Named Tunnel 設定
powershell -ExecutionPolicy Bypass -File "%~dp0setup-named-tunnel.ps1"
pause
