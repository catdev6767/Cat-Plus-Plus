#!/bin/bash
# Cat++ — Share toàn cầu
cd "$(dirname "$0")"

G='\033[92m'; R='\033[91m'; Y='\033[93m'; C='\033[96m'; B='\033[1m'; X='\033[0m'

echo ""
echo -e "${B}${C}🐱 Cat++ — Mở cho cả thế giới${X}"
echo ""

# 1. Kill
pkill -9 -f "python3 catpp.py" 2>/dev/null
pkill -9 -f "cloudflared tunnel" 2>/dev/null
sleep 2

# 2. Server
echo "[1/3] Khởi động server..."
nohup python3 catpp.py > /tmp/catpp.log 2>&1 &
sleep 3

if ! pgrep -f "python3 catpp.py" > /dev/null; then
    echo -e "${R}✗ Server không chạy${X}"
    tail -10 /tmp/catpp.log
    exit 1
fi
echo -e "${G}✓ Server OK${X}"

# 3. Cloudflared
CF=""
if command -v cloudflared >/dev/null 2>&1; then
    CF=$(command -v cloudflared)
elif [ -f "$HOME/.local/bin/cloudflared" ]; then
    CF="$HOME/.local/bin/cloudflared"
else
    echo "[2/3] Cài cloudflared..."
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64)  U="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64" ;;
        aarch64) U="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64" ;;
    esac
    mkdir -p ~/.local/bin
    curl -L "$U" -o ~/.local/bin/cloudflared
    chmod +x ~/.local/bin/cloudflared
    CF="$HOME/.local/bin/cloudflared"
fi

# 4. Tunnel
echo "[3/3] Mở tunnel..."
rm -f /tmp/tunnel.log /tmp/catpp-url.txt
nohup $CF tunnel --url http://localhost:5000 > /tmp/tunnel.log 2>&1 &
sleep 15

URL=""
for i in $(seq 1 20); do
    URL=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/tunnel.log 2>/dev/null | head -1)
    [ -n "$URL" ] && break
    sleep 1
done

if [ -n "$URL" ]; then
    echo "$URL" > /tmp/catpp-url.txt
    echo ""
    echo -e "${G}${B}═══════════════════════════════════════════════${X}"
    echo -e "${G}${B}  🌐 LINK CÔNG KHAI${X}"
    echo -e "${G}${B}═══════════════════════════════════════════════${X}"
    echo ""
    echo -e "  ${C}Landing:${X}  $URL"
    echo -e "  ${C}IDE:${X}      $URL/ide/"
    echo -e "  ${C}Docs:${X}     $URL/docs/"
    echo ""
    echo -e "  ${Y}→ IDE share link sẽ dùng URL này.${X}"
    echo -e "  ${Y}→ Gửi link cho bạn bè.${X}"
    echo ""
    echo -e "  Tắt: pkill -9 cloudflared; pkill -9 -f catpp.py"
    echo ""
    echo -e "${G}${B}═══════════════════════════════════════════════${X}"
else
    echo -e "${R}✗ Không lấy được URL${X}"
    tail -20 /tmp/tunnel.log
fi
