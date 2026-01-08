@echo off
chcp 65001 >nul
title ytify - 守護進程模式
cd /d "%~dp0"

echo ══════════════════════════════════════════════════
echo   ytify - 守護進程模式 (Supervisor)
echo ══════════════════════════════════════════════════
echo.

:: ========== 檢查 Python ==========
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未找到 Python！
    pause
    exit /b 1
)

:: ========== 檢查/安裝依賴 ==========
pip show supervisor >nul 2>&1
if errorlevel 1 (
    echo [*] 正在安裝依賴...
    pip install -r requirements.txt -q
)

:: ========== 建立必要目錄 ==========
if not exist "logs" mkdir logs
if not exist "downloads" mkdir downloads

echo.
echo   選擇操作:
echo.
echo   1. 啟動服務 (背景執行)
echo   2. 停止服務
echo   3. 重啟服務
echo   4. 查看狀態
echo   5. 查看日誌
echo   0. 退出
echo.

:menu
set /p choice="請輸入選項 (0-5): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto status
if "%choice%"=="5" goto logs
if "%choice%"=="0" goto exit
goto menu

:start
echo.
echo [*] 啟動 Supervisor...
start /b supervisord -c supervisord.conf
timeout /t 2 /nobreak >nul
echo [OK] 服務已在背景啟動
echo.
echo   網址: http://localhost:8765
echo   管理: http://localhost:9001
echo.
goto menu

:stop
echo.
echo [*] 停止服務...
supervisorctl -c supervisord.conf stop all >nul 2>&1
supervisorctl -c supervisord.conf shutdown >nul 2>&1
echo [OK] 服務已停止
echo.
goto menu

:restart
echo.
echo [*] 重啟服務...
supervisorctl -c supervisord.conf restart ytify
echo [OK] 服務已重啟
echo.
goto menu

:status
echo.
supervisorctl -c supervisord.conf status
echo.
goto menu

:logs
echo.
echo [*] 最近日誌 (按 Ctrl+C 退出):
echo.
type logs\ytify.log | more
echo.
goto menu

:exit
exit /b
