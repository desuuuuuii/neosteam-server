#!/bin/bash

echo "=========================================================="
echo "   NeoSteam 24/7 Global Server - Authentic Cloud Engine   "
echo "=========================================================="

mkdir -p /home/user/app/config

# Fix: create per-user runtime dir for wineserver socket
UID_VAL=$(id -u)
export XDG_RUNTIME_DIR=/tmp/runtime-${UID_VAL}
mkdir -p ${XDG_RUNTIME_DIR}
chmod 700 ${XDG_RUNTIME_DIR}

export WINEPREFIX=/home/user/.wine
export WINEDEBUG=-all
export WINEDLLOVERRIDES="mscoree,mshtml="
export DISPLAY=:99

# 1. Start Xvfb (as user, without X11 socket, just framebuffer)
echo "[+] Starting Xvfb Virtual Framebuffer..."
Xvfb :99 -screen 0 1024x768x16 -nolisten unix -nolisten tcp &
sleep 1

# 2. Initialize Wine prefix once (sequential, not parallel)
echo "[+] Initializing Wine prefix..."
wineboot --init 2>/dev/null || true
sleep 3

# 3. Start Zero-SQL TDS Database Bridge on Port 1433
echo "[+] Starting Zero-SQL TDS Database Bridge on Port 1433..."
python3 /home/user/app/sql_bridge.py &
sleep 1

# 4. Start Web Status Dashboard & Auto-Discovery API on Port $PORT
echo "[+] Starting Web Dashboard & Auto-Discovery API..."
python3 /home/user/app/server_web_dashboard.py &

# 5. Setup and start Bore TCP tunnels for Login (3001) & World (7001)
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

# 6. Dynamically configure NSLoginServer.ini with assigned bore game port
GAME_PORT=$(grep -oE 'bore\.pub:[0-9]+' /home/user/app/bore_game.log | awk -F: '{print $2}' | head -n 1)
if [ -z "$GAME_PORT" ]; then
    GAME_PORT=7001
fi
echo "[+] Configuring Game Port: $GAME_PORT"

LOGIN_INI="/home/user/app/MicroServer/LoginServer/NSLoginServer.ini"
if [ -f "$LOGIN_INI" ]; then
    sed -i "s/GameServerIp1 = .*/GameServerIp1 = 159.223.110.159/g" "$LOGIN_INI" || true
    sed -i "s/GameServerPort1 = .*/GameServerPort1 = $GAME_PORT/g" "$LOGIN_INI" || true
fi

# 7. Start Login Server under Wine (sequential)
echo "[+] Starting Login Server Under Wine..."
cd /home/user/app/MicroServer/LoginServer
if [ -f "NSLoginService.exe" ]; then
    wine NSLoginService.exe > /home/user/app/login.log 2>&1 &
elif [ -f "NSLoginServer.exe" ]; then
    wine NSLoginServer.exe > /home/user/app/login.log 2>&1 &
fi
sleep 3

# 8. Start World/Game Server under Wine
echo "[+] Starting World Server Under Wine..."
cd /home/user/app/MicroServer/8001
if [ -f "NSWorldService.exe" ]; then
    wine NSWorldService.exe > /home/user/app/game.log 2>&1 &
elif [ -f "NSGameServer_CN_r.exe" ]; then
    wine NSGameServer_CN_r.exe > /home/user/app/game.log 2>&1 &
fi

cd /home/user/app
echo "[+] Authentic Cloud Server Systems Online 24/7!"

# Keep container running indefinitely
while true; do
    sleep 60
done
