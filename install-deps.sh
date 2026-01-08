#!/bin/bash
# ytify - Ubuntu/Debian 全自動安裝腳本
# 用法: curl -fsSL https://raw.githubusercontent.com/Jeffrey0117/Ytify/main/install-deps.sh | bash

set -e

echo "══════════════════════════════════════════════════"
echo "  ytify - 自動安裝依賴 (Ubuntu/Debian)"
echo "══════════════════════════════════════════════════"
echo

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 檢查是否為 root
if [ "$EUID" -eq 0 ]; then
    SUDO=""
else
    SUDO="sudo"
fi

echo "[1/5] 更新套件列表..."
$SUDO apt update -qq

echo
echo "[2/5] 安裝 Python3..."
if ! command -v python3 &> /dev/null; then
    $SUDO apt install -y python3 python3-pip python3-venv
fi
echo -e "${GREEN}[OK] Python3 $(python3 --version | cut -d' ' -f2)${NC}"

echo
echo "[3/5] 安裝 FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    $SUDO apt install -y ffmpeg
fi
echo -e "${GREEN}[OK] FFmpeg 已安裝${NC}"

echo
echo "[4/5] 安裝 Node.js..."
if ! command -v node &> /dev/null; then
    # 使用 NodeSource 安裝 LTS 版本
    curl -fsSL https://deb.nodesource.com/setup_lts.x | $SUDO -E bash -
    $SUDO apt install -y nodejs
fi
echo -e "${GREEN}[OK] Node.js $(node --version)${NC}"

echo
echo "[5/5] 安裝 PM2..."
if ! command -v pm2 &> /dev/null; then
    $SUDO npm install -g pm2
fi
echo -e "${GREEN}[OK] PM2 $(pm2 --version)${NC}"

echo
echo "══════════════════════════════════════════════════"
echo -e "  ${GREEN}系統依賴安裝完成！${NC}"
echo "══════════════════════════════════════════════════"
echo
echo "  下一步："
echo "    cd ytify"
echo "    ./run.sh"
echo
