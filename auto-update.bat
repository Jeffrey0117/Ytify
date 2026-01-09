@echo off
:: ytify 自動更新腳本
:: 由 Windows 工作排程器每 5 分鐘執行

cd /d "%~dp0"

:: 靜默執行 git pull
git pull origin main >nul 2>&1

:: 如果有更新，重啟服務
if %errorlevel%==0 (
    git diff --quiet HEAD@{1} HEAD 2>nul
    if errorlevel 1 (
        :: 有更新，重啟 ytify
        echo [%date% %time%] 發現更新，重啟服務... >> logs\auto-update.log
        taskkill /f /fi "WINDOWTITLE eq ytify-server*" >nul 2>&1
        timeout /t 2 /nobreak >nul
        start "ytify-server" /min cmd /c "cd /d %~dp0 && python main.py"
    )
)
