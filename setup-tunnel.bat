@echo off
chcp 65001 >nul
title Ytify - Cloudflare Tunnel 設定精靈
cd /d "%~dp0"

echo.
echo ══════════════════════════════════════════════════
echo   Cloudflare Tunnel 設定精靈
echo ══════════════════════════════════════════════════
echo.
echo   想從手機或外網使用 Ytify？設定 Cloudflare Tunnel！
echo.
echo   [1] 快速隧道 - 無需網域，每次網址不同
echo   [2] 固定網址 - 需要網域，永久固定網址
echo.
echo   不確定選哪個？
echo   - 沒有網域 → 選 1
echo   - 有網域、想長期使用 → 選 2
echo.
set /p MODE="請選擇 (1/2): "

if "%MODE%"=="1" goto :QUICK_TUNNEL
if "%MODE%"=="2" goto :FIXED_TUNNEL
goto :QUICK_TUNNEL

:QUICK_TUNNEL
echo.
echo ══════════════════════════════════════════════════
echo   快速隧道模式
echo ══════════════════════════════════════════════════
echo.

:: 檢查 cloudflared
echo [1/2] 檢查 cloudflared...
cloudflared --version >nul 2>&1
if errorlevel 1 (
    echo [!] cloudflared 未安裝，正在安裝...
    winget install Cloudflare.cloudflared --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [錯誤] 安裝失敗！
        echo 請手動安裝: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
        pause
        exit /b 1
    )
    echo [OK] cloudflared 已安裝
    echo [!] 請重新執行此腳本
    pause
    exit /b 0
)
echo [OK] cloudflared 已安裝

:: 檢查 ytify 是否運行
echo.
echo [2/2] 檢查 Ytify 服務...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8765/health' -UseBasicParsing -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo [!] Ytify 服務未啟動
    echo.
    echo 請先執行 run.bat 啟動服務，然後再執行此腳本
    pause
    exit /b 1
)
echo [OK] Ytify 服務運行中

echo.
echo ══════════════════════════════════════════════════
echo   啟動快速隧道
echo ══════════════════════════════════════════════════
echo.
echo   即將啟動隧道，會自動產生一個臨時網址
echo   網址會顯示在下方，類似：
echo   https://xxx-yyy-zzz.trycloudflare.com
echo.
echo   注意：
echo   - 關閉此視窗會中斷隧道
echo   - 每次執行網址都會不同
echo   - 適合臨時分享使用
echo.
echo   按任意鍵開始...
pause >nul

echo.
echo [*] 啟動中...
echo.
cloudflared tunnel --url http://localhost:8765

pause
exit /b 0

:FIXED_TUNNEL
echo.
echo ══════════════════════════════════════════════════
echo   固定網址模式
echo ══════════════════════════════════════════════════
echo.

:: 檢查 cloudflared
echo [1/5] 檢查 cloudflared...
cloudflared --version >nul 2>&1
if errorlevel 1 (
    echo [!] cloudflared 未安裝，正在安裝...
    winget install Cloudflare.cloudflared --accept-package-agreements --accept-source-agreements
    if errorlevel 1 (
        echo [錯誤] 安裝失敗！
        pause
        exit /b 1
    )
    echo [OK] cloudflared 已安裝
    echo [!] 請重新執行此腳本
    pause
    exit /b 0
)
echo [OK] cloudflared 已安裝

:: 檢查是否已經登入/建立 tunnel
echo.
echo [2/5] 檢查 Tunnel 狀態...
cloudflared tunnel list 2>nul | findstr /C:"ytify" >nul
if not errorlevel 1 (
    echo [OK] Tunnel 'ytify' 已存在
    goto :SETUP_DNS
)

:: 登入 Cloudflare
echo.
echo [3/5] 登入 Cloudflare...
echo.
echo   即將開啟瀏覽器，請登入你的 Cloudflare 帳號
echo   登入後選擇要使用的網域
echo.
echo   按任意鍵開啟瀏覽器...
pause >nul

cloudflared tunnel login
if errorlevel 1 (
    echo [錯誤] 登入失敗！
    pause
    exit /b 1
)
echo [OK] 登入成功

:: 建立 Tunnel
echo.
echo [4/5] 建立 Tunnel...
cloudflared tunnel create ytify
if errorlevel 1 (
    echo [錯誤] 建立 Tunnel 失敗！
    echo 如果 tunnel 已存在，這是正常的
)
echo [OK] Tunnel 'ytify' 已建立

:SETUP_DNS
:: 設定 DNS
echo.
echo [5/5] 設定 DNS
echo.
echo   請輸入你要使用的網址
echo   例如：ytify.example.com
echo.
set /p DOMAIN="請輸入網址: "

if "%DOMAIN%"=="" (
    echo [錯誤] 網址不能為空！
    pause
    exit /b 1
)

echo.
echo [*] 設定 DNS: %DOMAIN%
cloudflared tunnel route dns ytify %DOMAIN%
if errorlevel 1 (
    echo [警告] DNS 設定可能失敗
    echo 如果網址已設定過，這是正常的
)

echo.
echo ══════════════════════════════════════════════════
echo   設定完成！
echo ══════════════════════════════════════════════════
echo.
echo   你的 Ytify 網址: https://%DOMAIN%
echo.
echo   使用方式：
echo   1. 執行 run.bat 啟動服務（會自動啟動 tunnel）
echo   2. 用手機或其他裝置開啟上面的網址
echo.
echo   如果 run.bat 沒有自動啟動 tunnel，手動執行：
echo   cloudflared tunnel run ytify
echo.
pause
exit /b 0
