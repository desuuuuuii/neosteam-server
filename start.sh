#!/bin/bash

echo "=========================================================="
echo "   NeoSteam 24/7 Global Server - Dynamic Cloud Engine     "
echo "=========================================================="

mkdir -p /home/user/app/config
chmod -R 777 /home/user || true

# 1. Start Zero-SQL Database Bridge on Port 1433 (Required for Login & World Services)
echo "[+] Starting Zero-SQL Database Bridge on Port 1433..."
python3 /home/user/app/sql_bridge.py &
sleep 1

# 2. Start Web Status Dashboard & Auto-Discovery API on Port $PORT
echo "[+] Starting Web Dashboard & Auto-Discovery API..."
python3 /home/user/app/server_web_dashboard.py &

# 3. Extract Server Engine if needed
if [ -f "/home/user/app/microserver.zip" ] && [ ! -d "/home/user/app/MicroServer" ]; then
    echo "[+] Extracting server engine..."
    unzip -q /home/user/app/microserver.zip -d /home/user/app/MicroServer || true
fi

# 4. Setup and start Bore TCP tunnels for Login (3001) & World (7001)
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

# Wait 2 seconds for Bore ports to allocate
sleep 2

# 5. Dynamically configure NSLoginServer.ini with assigned game port
GAME_PORT=$(grep -oE 'bore\.pub:[0-9]+' /home/user/app/bore_game.log | awk -F: '{print $2}' | head -n 1)
if [ -z "$GAME_PORT" ]; then
    GAME_PORT=7001
fi
echo "[+] Dynamically configuring cloud LoginServer redirect to Game Port: $GAME_PORT"

LOGIN_INI="/home/user/app/MicroServer/LoginServer/NSLoginServer.ini"
if [ -f "$LOGIN_INI" ]; then
    sed -i "s/GameServerIp1 = .*/GameServerIp1 = 159.223.110.159/g" "$LOGIN_INI" || true
    sed -i "s/GameServerPort1 = .*/GameServerPort1 = $GAME_PORT/g" "$LOGIN_INI" || true
fi

# 6. Start NeoSteam Server under Wine
echo "[+] Starting NeoSteam Server Under Wine..."
if [ -f "/home/user/app/MicroServer/LoginServer/NSLoginService.exe" ]; then
    wine /home/user/app/MicroServer/LoginServer/NSLoginService.exe &
fi

if [ -f "/home/user/app/MicroServer/8001/NSWorldService.exe" ]; then
    wine /home/user/app/MicroServer/8001/NSWorldService.exe &
fi

echo "[+] All Cloud Server Systems Online 24/7!"

# Keep container running indefinitely
while true; do
    sleep 60
done
