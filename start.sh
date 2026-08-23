#!/bin/bash

echo "=========================================================="
echo "   NeoSteam 24/7 Global Server - Cloud Engine Active      "
echo "=========================================================="

mkdir -p /home/user/app/config
chmod -R 777 /home/user || true

# 1. Start Zero-SQL Cloud Engine on Ports 3001 & 7001
echo "[+] Starting Zero-SQL Cloud Game & Login Engine..."
python3 /home/user/app/cloud_engine.py &
sleep 1

# 2. Start Web Status Dashboard & Auto-Discovery API on Port $PORT
echo "[+] Starting Web Dashboard & Auto-Discovery API..."
python3 /home/user/app/server_web_dashboard.py &

# 3. Setup and start Bore TCP tunnels for Login (3001) & World (7001)
if [ ! -f "/home/user/app/bore" ]; then
    echo "[+] Fetching Bore binary..."
    curl -SsL "https://github.com/ekzhang/bore/releases/download/v0.5.2/bore-v0.5.2-x86_64-unknown-linux-musl.tar.gz" -o /home/user/app/bore.tar.gz || true
    tar -xzf /home/user/app/bore.tar.gz -C /home/user/app/ || true
    chmod +x /home/user/app/bore || true
fi

if [ -f "/home/user/app/bore" ]; then
    echo "[+] Starting Bore TCP Port Forwarding..."
    /home/user/app/bore local 3001 --to bore.pub > /home/user/app/bore_login.log 2>&1 &
    /home/user/app/bore local 7001 --to bore.pub > /home/user/app/bore_game.log 2>&1 &
fi

echo "[+] Cloud Server Engine Online 24/7!"

# Keep container running indefinitely
while true; do
    sleep 60
done
