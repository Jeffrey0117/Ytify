@echo off
chcp 65001 >nul
title ytify - 設定自動更新

echo ══════════════════════════════════════════════════
echo   ytify - 設定自動更新排程
echo ══════════════════════════════════════════════════
echo.

:: 取得當前目錄
set YTIFY_PATH=%~dp0
set YTIFY_PATH=%YTIFY_PATH:~0,-1%

echo [1/2] 建立 Windows 工作排程...
echo.

:: 刪除舊的排程（如果存在）
schtasks /delete /tn "ytify-auto-update" /f >nul 2>&1

:: 建立新排程：每 5 分鐘執行一次
schtasks /create /tn "ytify-auto-update" /tr "\"%YTIFY_PATH%\auto-update.bat\"" /sc minute /mo 5 /f

if errorlevel 1 (
    echo [錯誤] 建立排程失敗！
    echo        請以系統管理員身份執行此腳本
    pause
    exit /b 1
)

echo [OK] 排程已建立
echo.

echo [2/2] 排程資訊:
echo.
schtasks /query /tn "ytify-auto-update" /fo list | findstr /i "TaskName Status"
echo.

echo ══════════════════════════════════════════════════
echo   設定完成！
echo ══════════════════════════════════════════════════
echo.
echo   ytify 將每 5 分鐘自動檢查更新
echo   更新日誌: logs\auto-update.log
echo.
echo   停用自動更新: schtasks /delete /tn "ytify-auto-update" /f
echo.
pause
