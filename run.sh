#!/bin/bash
# ytify - 一鍵啟動腳本 (Linux/Mac)

set -e

echo "══════════════════════════════════════════════════"
echo "  ytify - YouTube 下載工具"
echo "══════════════════════════════════════════════════"
echo

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ========== 檢查 Python ==========
echo "[1/4] 檢查 Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[錯誤] 未找到 Python3！${NC}"
    echo
    echo "請先安裝 Python 3.8+"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  Mac: brew install python3"
    echo
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}[OK] Python $PYTHON_VERSION${NC}"

# ========== 檢查/安裝 Python 依賴 ==========
echo
echo "[2/4] 檢查 Python 依賴..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "[*] 正在安裝依賴..."
    pip3 install -r requirements.txt -q
fi
echo -e "${GREEN}[OK] Python 依賴已就緒${NC}"

# ========== 檢查 FFmpeg ==========
echo
echo "[3/4] 檢查 FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}[警告] FFmpeg 未安裝，下載的影片可能沒有聲音${NC}"
    echo "       Ubuntu/Debian: sudo apt install ffmpeg"
    echo "       Mac: brew install ffmpeg"
else
    echo -e "${GREEN}[OK] FFmpeg 已安裝${NC}"
fi

# ========== 檢查/安裝 PM2 ==========
echo
echo "[4/4] 檢查 PM2..."
if ! command -v pm2 &> /dev/null; then
    echo "[*] PM2 未安裝，檢查 Node.js..."
    if ! command -v node &> /dev/null; then
        echo -e "${YELLOW}[提示] Node.js 未安裝，使用直接啟動模式${NC}"
        echo "       關閉此終端會停止服務"
        echo
        echo "       如需背景執行，請先安裝 Node.js:"
        echo "       Ubuntu/Debian: sudo apt install nodejs npm"
        echo "       Mac: brew install node"
        echo
        echo "──────────────────────────────────────────────────"
        echo "  服務網址: http://localhost:8765"
        echo "──────────────────────────────────────────────────"
        echo
        python3 main.py
        exit 0
    fi
    echo "[*] 正在安裝 PM2..."
    npm install -g pm2 --silent
    echo -e "${GREEN}[OK] PM2 安裝完成${NC}"
fi

# ========== 建立必要目錄 ==========
mkdir -p logs downloads

# ========== PM2 啟動 ==========
echo
echo "══════════════════════════════════════════════════"
echo "  啟動服務"
echo "══════════════════════════════════════════════════"
echo

echo "[*] 使用 PM2 守護進程啟動..."

# 檢查是否已在運行
if pm2 describe ytify &> /dev/null; then
    echo "[!] ytify 已在運行，重啟中..."
    pm2 restart ytify
else
    pm2 start ecosystem.config.js
fi

echo
echo "══════════════════════════════════════════════════"
echo -e "  ${GREEN}服務已啟動！${NC}"
echo "══════════════════════════════════════════════════"
echo
echo "  網址: http://localhost:8765"
echo
echo "  PM2 指令:"
echo "    pm2 status       - 查看狀態"
echo "    pm2 logs ytify   - 查看日誌"
echo "    pm2 stop ytify   - 停止服務"
echo "    pm2 restart ytify - 重啟服務"
echo
pm2 status
