#!/bin/bash
# ytify - 一鍵啟動腳本 (Linux/Mac)

cd "$(dirname "$0")"

echo "══════════════════════════════════════════════════"
echo "  ytify - YouTube 下載工具"
echo "══════════════════════════════════════════════════"
echo
echo "  [1] Docker 模式（推薦，含自動更新）"
echo "  [2] Python 模式（傳統）"
echo
read -p "請選擇啟動模式 (1/2): " MODE

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ "$MODE" = "2" ]; then
    # ========== Python 模式 ==========
    echo
    echo "══════════════════════════════════════════════════"
    echo "  Python 模式"
    echo "══════════════════════════════════════════════════"
    echo

    echo "[1/3] 檢查 Python..."
    if ! command -v python3 &> /dev/null; then
        echo -e "${YELLOW}[!] Python3 未安裝，正在安裝...${NC}"
        if [ -f /etc/debian_version ]; then
            sudo apt update && sudo apt install -y python3 python3-pip
        elif [ -f /etc/redhat-release ]; then
            sudo yum install -y python3 python3-pip
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install python3
        fi
    fi
    echo -e "${GREEN}[OK] Python $(python3 --version | cut -d' ' -f2)${NC}"

    echo
    echo "[2/3] 檢查 Python 依賴..."
    if ! python3 -c "import fastapi" &> /dev/null; then
        echo "[*] 正在安裝依賴..."
        pip3 install -r requirements.txt -q
    fi
    echo -e "${GREEN}[OK] Python 依賴已就緒${NC}"

    echo
    echo "[3/3] 檢查 FFmpeg..."
    if ! command -v ffmpeg &> /dev/null; then
        echo -e "${YELLOW}[!] FFmpeg 未安裝，正在安裝...${NC}"
        if [ -f /etc/debian_version ]; then
            sudo apt install -y ffmpeg
        elif [ -f /etc/redhat-release ]; then
            sudo yum install -y ffmpeg
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install ffmpeg
        fi
    fi
    echo -e "${GREEN}[OK] FFmpeg 已安裝${NC}"

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
else
    # ========== Docker 模式 ==========
    echo
    echo "══════════════════════════════════════════════════"
    echo "  Docker 模式"
    echo "══════════════════════════════════════════════════"
    echo

    echo "[1/3] 檢查 Docker..."
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}[!] Docker 未安裝，正在安裝...${NC}"
        if [ -f /etc/debian_version ]; then
            # Ubuntu/Debian
            curl -fsSL https://get.docker.com | sudo sh
            sudo usermod -aG docker $USER
        elif [ -f /etc/redhat-release ]; then
            # CentOS/RHEL
            sudo yum install -y docker docker-compose
            sudo systemctl start docker
            sudo systemctl enable docker
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew install --cask docker
            echo -e "${YELLOW}[!] 請手動啟動 Docker Desktop 後重新執行${NC}"
            exit 0
        fi
    fi
    echo -e "${GREEN}[OK] Docker 已安裝${NC}"

    # 檢查 docker-compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}[!] docker-compose 未安裝，正在安裝...${NC}"
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi

    # 確保 Docker daemon 運行
    if ! docker info &> /dev/null; then
        echo "[*] 啟動 Docker daemon..."
        sudo systemctl start docker 2>/dev/null || sudo service docker start 2>/dev/null
        sleep 3
    fi
    echo -e "${GREEN}[OK] Docker 運行中${NC}"

    mkdir -p downloads data

    echo
    echo "[2/3] 拉取最新 image..."
    docker-compose pull
    echo -e "${GREEN}[OK] 已拉取最新版本${NC}"

    echo
    echo "[3/3] 啟動 Docker 容器..."
    docker-compose up -d

    echo
    docker-compose ps

    echo
    echo "══════════════════════════════════════════════════"
    echo "  Docker 服務已啟動！"
    echo "══════════════════════════════════════════════════"
    echo
    echo "  ytify:      http://localhost:8765"
    echo "  Watchtower: 每 5 分鐘自動檢查更新"
    echo
    echo "  查看日誌: docker-compose logs -f ytify"
    echo "  停止服務: docker-compose down"
    echo
fi
