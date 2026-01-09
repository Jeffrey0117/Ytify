@echo off
chcp 65001 >nul
:: ytify auto-update script (with graceful restart)

cd /d "%~dp0"

:: Create logs folder if not exists
if not exist logs mkdir logs

:: Save current commit hash before pull
for /f "tokens=*" %%i in ('git rev-parse HEAD 2^>nul') do set OLD_HASH=%%i

:: Pull latest changes
git pull origin main >nul 2>&1

:: Get new commit hash after pull
for /f "tokens=*" %%i in ('git rev-parse HEAD 2^>nul') do set NEW_HASH=%%i

:: Compare hashes - only restart if changed
if not "%OLD_HASH%"=="%NEW_HASH%" (
    echo [%date% %time%] Update found: %OLD_HASH:~0,7% to %NEW_HASH:~0,7% >> logs\auto-update.log

    :: Graceful restart: wait for tasks to complete
    call :graceful_restart
)

goto :eof

:graceful_restart
:: 最多等待 10 分鐘（60 次，每次 10 秒）
set max_wait=60
set wait_count=0

:check_loop
:: 呼叫 API 檢查是否可以重啟
curl -s -o "%TEMP%\ytify_restart.json" -w "%%{http_code}" http://localhost:8765/api/can-restart 2>nul > "%TEMP%\ytify_http_code.txt"
set /p HTTP_CODE=<"%TEMP%\ytify_http_code.txt"

:: If HTTP request failed or non-200, restart directly
if not "%HTTP_CODE%"=="200" (
    echo [%date% %time%] API unavailable (HTTP %HTTP_CODE%), restarting >> logs\auto-update.log
    goto :do_restart
)

:: Check if can_restart is true
findstr /c:"\"can_restart\": true" "%TEMP%\ytify_restart.json" >nul 2>&1
if %errorlevel%==0 (
    echo [%date% %time%] No running tasks, restarting >> logs\auto-update.log
    goto :do_restart
)

:: Tasks still running, wait
set /a wait_count+=1
if %wait_count% geq %max_wait% (
    echo [%date% %time%] Timeout (10min), force restarting >> logs\auto-update.log
    goto :do_restart
)

:: Wait 10 seconds and check again
echo [%date% %time%] Tasks running, waiting... (%wait_count%/%max_wait%) >> logs\auto-update.log
timeout /t 10 /nobreak >nul
goto :check_loop

:do_restart
:: Stop old server
taskkill /f /fi "WINDOWTITLE eq ytify-server*" >nul 2>&1
timeout /t 2 /nobreak >nul

:: Start new server (with UTF-8 and ANSI support)
start "ytify-server" /min cmd /c "chcp 65001 >nul && cd /d %~dp0 && python main.py"
echo [%date% %time%] Server restarted >> logs\auto-update.log

:: Cleanup temp files
del "%TEMP%\ytify_restart.json" >nul 2>&1
del "%TEMP%\ytify_http_code.txt" >nul 2>&1
goto :eof
