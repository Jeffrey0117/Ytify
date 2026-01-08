#!/bin/bash
# ytify - 守護進程模式 (Supervisor)

cd "$(dirname "$0")"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 檢查依賴
if ! python3 -c "import supervisor" &> /dev/null; then
    echo "[*] 安裝 Supervisor..."
    pip3 install -r requirements.txt -q
fi

mkdir -p logs downloads

case "$1" in
    start)
        echo "[*] 啟動服務..."
        supervisord -c supervisord.conf
        echo -e "${GREEN}[OK] 服務已在背景啟動${NC}"
        echo
        echo "  網址: http://localhost:8765"
        echo "  管理: http://localhost:9001"
        ;;
    stop)
        echo "[*] 停止服務..."
        supervisorctl -c supervisord.conf stop all 2>/dev/null
        supervisorctl -c supervisord.conf shutdown 2>/dev/null
        echo -e "${GREEN}[OK] 服務已停止${NC}"
        ;;
    restart)
        echo "[*] 重啟服務..."
        supervisorctl -c supervisord.conf restart ytify
        echo -e "${GREEN}[OK] 服務已重啟${NC}"
        ;;
    status)
        supervisorctl -c supervisord.conf status
        ;;
    logs)
        tail -f logs/ytify.log
        ;;
    *)
        echo "══════════════════════════════════════════════════"
        echo "  ytify - 守護進程模式 (Supervisor)"
        echo "══════════════════════════════════════════════════"
        echo
        echo "  用法: $0 {start|stop|restart|status|logs}"
        echo
        echo "  start   - 啟動服務 (背景執行)"
        echo "  stop    - 停止服務"
        echo "  restart - 重啟服務"
        echo "  status  - 查看狀態"
        echo "  logs    - 查看日誌 (即時)"
        echo
        ;;
esac
