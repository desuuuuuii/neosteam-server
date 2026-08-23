#!/bin/bash

echo "=========================================================="
echo "   NeoSteam 24/7 Global Server - Cloud World Engine       "
echo "=========================================================="

mkdir -p /home/user/app/config

# Fix any double nesting if it exists
if [ -d "/home/user/app/MicroServer/MicroServer" ]; then
    cp -rn /home/user/app/MicroServer/MicroServer/* /home/user/app/MicroServer/ 2>/dev/null || true
fi

# Per-user runtime directory
UID_VAL=$(id -u)
export XDG_RUNTIME_DIR=/tmp/runtime-${UID_VAL}
mkdir -p ${XDG_RUNTIME_DIR}
chmod 700 ${XDG_RUNTIME_DIR}

export WINEPREFIX=/home/user/.wine
export WINEDEBUG=-all
export WINEDLLOVERRIDES="mscoree,mshtml="
export DISPLAY=:99

# 1. Start Multi-Threaded Web Dashboard on Port $PORT
echo "[1/5] Starting Web Dashboard on Port $PORT..."
python3 /home/user/app/server_web_dashboard.py &
sleep 1

# 2. Start Zero-SQL TDS Database Bridge on Port 1433
echo "[2/5] Starting Zero-SQL TDS Database Bridge on Port 1433..."
python3 /home/user/app/sql_bridge.py &
sleep 1

# 3. Clean and start Xvfb Display
echo "[3/5] Starting Xvfb Virtual Framebuffer..."
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99 /tmp/.X*-lock 2>/dev/null || true
pkill -9 -f Xvfb 2>/dev/null || true
Xvfb :99 -screen 0 1024x768x16 -ac -nolisten unix -nolisten tcp &
sleep 1

# 4. Prepare Wine prefix
echo "[4/5] Preparing Wine prefix..."
wineboot -u 2>/dev/null || true
sleep 3

# 5. Patch all INI files to link over 127.0.0.1
find /home/user/app/MicroServer -name "*.ini" -exec sed -i 's/113\.19\.181\.110/127.0.0.1/g' {} + 2>/dev/null || true
sed -i 's/GameServerIp1 = .*/GameServerIp1 = 127.0.0.1/g' /home/user/app/MicroServer/LoginServer/NSLoginServer.ini 2>/dev/null || true
sed -i 's/GameServerPort1 = .*/GameServerPort1 = 7001/g' /home/user/app/MicroServer/LoginServer/NSLoginServer.ini 2>/dev/null || true

# 6. Start Zone 8001 (Starter Hub) FIRST & Wait 6s for Map + NPC Loading
echo "[5/5] Starting Zone 8001 (Starter Hub)..."
cd /home/user/app/MicroServer/8001
if [ -f "NSGameServer_CN_r.exe" ]; then
    wine NSGameServer_CN_r.exe > /home/user/app/game.log 2>&1 &
elif [ -f "NSWorldService.exe" ]; then
    wine NSWorldService.exe > /home/user/app/game.log 2>&1 &
fi
echo "[+] Waiting 6 seconds for Map & NPC Loading to complete..."
sleep 6

# 7. Start Login Server under Wine (GameServer is already listening on 7001)
echo "[+] Starting Login Server..."
cd /home/user/app/MicroServer/LoginServer
if [ -f "NSLoginServer.exe" ]; then
    wine NSLoginServer.exe > /home/user/app/login.log 2>&1 &
elif [ -f "NSLoginService.exe" ]; then
    wine NSLoginService.exe > /home/user/app/login.log 2>&1 &
fi
sleep 3

# 8. Start Bore TCP tunnels for Login (3001) & World (7001)
echo "[+] Starting Bore TCP Port Forwarding..."
if [ ! -f "/home/user/app/bore" ]; then
    curl -SsL "https://github.com/ekzhang/bore/releases/download/v0.5.2/bore-v0.5.2-x86_64-unknown-linux-musl.tar.gz" -o /home/user/app/bore.tar.gz || true
    tar -xzf /home/user/app/bore.tar.gz -C /home/user/app/ || true
    chmod +x /home/user/app/bore || true
fi

if [ -f "/home/user/app/bore" ]; then
    /home/user/app/bore local 3001 --to bore.pub > /home/user/app/bore_login.log 2>&1 &
    /home/user/app/bore local 7001 --to bore.pub > /home/user/app/bore_game.log 2>&1 &
fi

cd /home/user/app
echo "[+] NeoSteam Cloud Server Engine Online 24/7!"

# Keep container running indefinitely
while true; do
    sleep 60
done
