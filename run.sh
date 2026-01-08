#!/bin/bash
# ytify - 一鍵啟動腳本 (Linux/Mac)

cd "$(dirname "$0")"

echo "══════════════════════════════════════════════════"
echo "  ytify - YouTube 下載工具"
echo "══════════════════════════════════════════════════"
echo

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ========== 檢查 Python ==========
echo "[1/3] 檢查 Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[錯誤] 未找到 Python3！${NC}"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  Mac: brew install python3"
    exit 1
fi
echo -e "${GREEN}[OK] Python $(python3 --version | cut -d' ' -f2)${NC}"

# ========== 檢查/安裝 Python 依賴 ==========
echo
echo "[2/3] 檢查 Python 依賴..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "[*] 正在安裝依賴..."
    pip3 install -r requirements.txt -q
fi
echo -e "${GREEN}[OK] Python 依賴已就緒${NC}"

# ========== 檢查 FFmpeg ==========
echo
echo "[3/3] 檢查 FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}[警告] FFmpeg 未安裝，下載的影片可能沒有聲音${NC}"
    echo "       sudo apt install ffmpeg"
else
    echo -e "${GREEN}[OK] FFmpeg 已安裝${NC}"
fi

# ========== 建立必要目錄 ==========
mkdir -p logs downloads

echo
echo "══════════════════════════════════════════════════"
echo "  啟動服務"
echo "══════════════════════════════════════════════════"
echo
echo "  網址: http://localhost:8765"
echo
echo "  按 Ctrl+C 停止服務"
echo "══════════════════════════════════════════════════"
echo

python3 main.py
