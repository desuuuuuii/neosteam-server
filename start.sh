#!/bin/bash

echo "=========================================================="
echo "   NeoSteam 24/7 Global Server - Render Cloud Engine      "
echo "=========================================================="

mkdir -p /home/user/.config/playit
mkdir -p /home/user/app/config
chmod -R 777 /home/user || true

# 1. Start Web Status Dashboard for Render Health Check
echo "[+] Starting Web Dashboard..."
python3 /home/user/app/server_web_dashboard.py &

# 2. Extract Server Engine if needed
if [ -f "/home/user/app/microserver.zip" ] && [ ! -d "/home/user/app/MicroServer" ]; then
    echo "[+] Extracting server engine..."
    unzip -q /home/user/app/microserver.zip -d /home/user/app/MicroServer || true
fi

# 3. Setup and Run Playit with custom secret path
if [ ! -f "/home/user/app/playit" ]; then
    echo "[+] Fetching official Playit binary..."
    curl -SsL "https://github.com/playit-cloud/playit-agent/releases/download/v0.15.26/playit-linux-amd64" -o /home/user/app/playit || true
    chmod +x /home/user/app/playit || true
fi

if [ -f "/home/user/app/playit" ]; then
    echo "[+] Starting Playit Global Network Router..."
    /home/user/app/playit --secret_path /home/user/app/config/playit.toml run > /home/user/app/playit.log 2>&1 &
fi

# 4. Setup Bore TCP Tunnel (Instant 0-config fallback)
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

# 5. Start NeoSteam Server under Wine
echo "[+] Starting NeoSteam Server Under Wine..."
if [ -f "/home/user/app/MicroServer/LoginServer/NSLoginService.exe" ]; then
    wine /home/user/app/MicroServer/LoginServer/NSLoginService.exe &
fi

if [ -f "/home/user/app/MicroServer/8001/NSWorldService.exe" ]; then
    wine /home/user/app/MicroServer/8001/NSWorldService.exe &
fi

echo "[+] Cloud Server Engine Online 24/7!"

# Keep container running indefinitely
while true; do
    sleep 60
done
