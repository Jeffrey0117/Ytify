@echo off
:: ytify 自動更新循環
:: 每 5 分鐘檢查一次 GitHub 更新

cd /d "%~dp0"

:: 建立 logs 資料夾
if not exist logs mkdir logs

echo [%date% %time%] 自動更新服務啟動 >> logs\auto-update.log

:LOOP
:: 等待 5 分鐘 (300 秒)
timeout /t 300 /nobreak >nul

:: 執行更新檢查
call auto-update.bat

:: 繼續循環
goto :LOOP
