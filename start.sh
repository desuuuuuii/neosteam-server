#!/bin/bash

echo "=========================================================="
echo "   NeoSteam 24/7 Global Server - Render Cloud Engine      "
echo "=========================================================="

# 1. Start Web Status Dashboard for Render Health Check
echo "[+] Starting Web Dashboard..."
python3 /home/user/app/server_web_dashboard.py &

# 2. Extract Server Engine if needed
if [ -f "/home/user/app/microserver.zip" ] && [ ! -d "/home/user/app/MicroServer" ]; then
    echo "[+] Extracting server engine..."
    unzip -q /home/user/app/microserver.zip -d /home/user/app/MicroServer || true
fi

# 3. Download official Playit Linux AMD64 Binary
if [ ! -f "/home/user/app/playit" ] || ! file /home/user/app/playit | grep -q "ELF"; then
    echo "[+] Fetching official Playit binary..."
    curl -SsL "https://github.com/playit-cloud/playit-agent/releases/download/v0.15.26/playit-linux-amd64" -o /home/user/app/playit || true
    chmod +x /home/user/app/playit || true
fi

if [ -f "/home/user/app/playit" ]; then
    echo "[+] Starting Playit Global Network Router..."
    /home/user/app/playit run &
fi

# 4. Start NeoSteam Server under Wine
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
