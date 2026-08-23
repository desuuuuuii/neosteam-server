#!/bin/bash

echo "=========================================================="
echo "   NeoSteam 24/7 Global Server - Render Cloud Engine      "
echo "=========================================================="

# 1. Start Web Status Dashboard
echo "[+] Starting Web Dashboard..."
python3 /home/user/app/server_web_dashboard.py &

# 2. Extract Server Engine if needed
if [ -f "/home/user/app/microserver.zip" ] && [ ! -d "/home/user/app/MicroServer" ]; then
    echo "[+] Extracting server engine..."
    unzip -q /home/user/app/microserver.zip -d /home/user/app/MicroServer || true
fi

# 3. Start Playit Agent with persistent log
echo "[+] Starting Playit Global Network Router..."
playit run > /home/user/app/playit.log 2>&1 &

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
