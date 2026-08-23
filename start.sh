#!/bin/bash
set -e

echo "=========================================================="
echo "   NeoSteam 24/7 Global Server - Hugging Face Cloud Engine "
echo "=========================================================="

# 1. Start Web Status Dashboard on Port 7860 (Required by Hugging Face)
echo "[+] Starting Web Dashboard on Port 7860..."
python3 /home/user/app/server_web_dashboard.py &

# 2. Download and run Playit tunnel agent for public game routing
echo "[+] Starting Global Game Network Connection..."
if [ ! -f "/home/user/app/playit" ]; then
    curl -SsL https://playit-cloud.github.io/ppa/playit-linux-amd64 -o /home/user/app/playit || true
    chmod +x /home/user/app/playit || true
fi

if [ -f "/home/user/app/playit" ]; then
    /home/user/app/playit run &
fi

# 3. Start NeoSteam Server under Wine
echo "[+] Starting NeoSteam Game Server Engine..."
if [ -f "/home/user/app/MicroServer/LoginServer/NSLoginService.exe" ]; then
    wine /home/user/app/MicroServer/LoginServer/NSLoginService.exe &
fi

if [ -f "/home/user/app/MicroServer/8001/NSWorldService.exe" ]; then
    wine /home/user/app/MicroServer/8001/NSWorldService.exe &
fi

echo "[+] All Cloud Server Systems Online 24/7!"
wait -n
