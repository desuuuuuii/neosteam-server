#!/bin/bash

echo "=========================================================="
echo "   NeoSteam 24/7 Global Server - Full 4-Zone Cloud Engine "
echo "=========================================================="

mkdir -p /home/user/app/config

# Per-user runtime directory
UID_VAL=$(id -u)
export XDG_RUNTIME_DIR=/tmp/runtime-${UID_VAL}
mkdir -p ${XDG_RUNTIME_DIR}
chmod 700 ${XDG_RUNTIME_DIR}

export WINEPREFIX=/home/user/.wine
export WINEDEBUG=-all
export WINEDLLOVERRIDES="mscoree,mshtml="
export DISPLAY=:99

# 1. Start Web Status Dashboard & Auto-Discovery API FIRST (Instant Health Check)
echo "[+] Starting Web Dashboard & Auto-Discovery API on Port $PORT..."
python3 /home/user/app/server_web_dashboard.py &
sleep 1

# 2. Clean any stale display locks and start Xvfb
echo "[+] Starting Xvfb Virtual Framebuffer..."
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99 /tmp/.X*-lock 2>/dev/null || true
pkill -9 -f Xvfb 2>/dev/null || true
Xvfb :99 -screen 0 1024x768x16 -ac -nolisten unix -nolisten tcp &
sleep 1

# 3. Initialize Wine prefix and configure Wine ODBC registry cleanly
echo "[+] Initializing Wine prefix..."
wineboot --init 2>/dev/null || true
sleep 2

# Register SQL Server driver in Wine ODBC registry using wine reg
wine reg add "HKLM\Software\ODBC\ODBCINST.INI\ODBC Drivers" /v "SQL Server" /d "Installed" /f 2>/dev/null || true
wine reg add "HKLM\Software\ODBC\ODBCINST.INI\SQL Server" /v "Driver" /d "C:\windows\system32\odbc32.dll" /f 2>/dev/null || true
wine reg add "HKLM\Software\ODBC\ODBCINST.INI\SQL Server" /v "Setup" /d "C:\windows\system32\odbc32.dll" /f 2>/dev/null || true
wine reg add "HKLM\Software\ODBC\ODBCINST.INI\SQL Server" /v "CPTimeout" /d "60" /f 2>/dev/null || true

# System DSNs for Main_DB_1 and Game_DB_1_1
wine reg add "HKLM\Software\ODBC\ODBC.INI\ODBC Data Sources" /v "Main_DB_1" /d "SQL Server" /f 2>/dev/null || true
wine reg add "HKLM\Software\ODBC\ODBC.INI\Main_DB_1" /v "Driver" /d "C:\windows\system32\odbc32.dll" /f 2>/dev/null || true
wine reg add "HKLM\Software\ODBC\ODBC.INI\Main_DB_1" /v "Server" /d "127.0.0.1" /f 2>/dev/null || true
wine reg add "HKLM\Software\ODBC\ODBC.INI\Main_DB_1" /v "Database" /d "Main_DB_1" /f 2>/dev/null || true

wine reg add "HKLM\Software\ODBC\ODBC.INI\ODBC Data Sources" /v "Game_DB_1_1" /d "SQL Server" /f 2>/dev/null || true
wine reg add "HKLM\Software\ODBC\ODBC.INI\Game_DB_1_1" /v "Driver" /d "C:\windows\system32\odbc32.dll" /f 2>/dev/null || true
wine reg add "HKLM\Software\ODBC\ODBC.INI\Game_DB_1_1" /v "Server" /d "127.0.0.1" /f 2>/dev/null || true
wine reg add "HKLM\Software\ODBC\ODBC.INI\Game_DB_1_1" /v "Database" /d "Game_DB_1_1" /f 2>/dev/null || true

# 4. Start Zero-SQL TDS Database Bridge on Port 1433
echo "[+] Starting Zero-SQL TDS Database Bridge on Port 1433..."
python3 /home/user/app/sql_bridge.py &
sleep 1

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

# 6. Ensure NSLoginServer.ini points to local WorldServer (127.0.0.1:7001)
LOGIN_INI="/home/user/app/MicroServer/LoginServer/NSLoginServer.ini"
if [ -f "$LOGIN_INI" ]; then
    sed -i "s/GameServerIp1 = .*/GameServerIp1 = 127.0.0.1/g" "$LOGIN_INI" || true
    sed -i "s/GameServerPort1 = .*/GameServerPort1 = 7001/g" "$LOGIN_INI" || true
fi

# 7. Start Login Server
echo "[+] Starting Login Server..."
cd /home/user/app/MicroServer/LoginServer
if [ -f "NSLoginService.exe" ]; then
    wine NSLoginService.exe > /home/user/app/login.log 2>&1 &
elif [ -f "NSLoginServer.exe" ]; then
    wine NSLoginServer.exe > /home/user/app/login.log 2>&1 &
fi
sleep 2

# 8. Start All 4 Zone Servers
echo "[+] Starting Zone 8001 (Starter Hub)..."
cd /home/user/app/MicroServer/8001
if [ -f "NSWorldService.exe" ]; then
    wine NSWorldService.exe > /home/user/app/game.log 2>&1 &
elif [ -f "NSGameServer_CN_r.exe" ]; then
    wine NSGameServer_CN_r.exe > /home/user/app/game.log 2>&1 &
fi
sleep 1

if [ -d "/home/user/app/MicroServer/8002" ]; then
    echo "[+] Starting Zone 8002 (Rogwell Republic)..."
    cd /home/user/app/MicroServer/8002
    wine NSGameServer_CN_r.exe > /dev/null 2>&1 &
fi

if [ -d "/home/user/app/MicroServer/8003" ]; then
    echo "[+] Starting Zone 8003 (Taxon Continent)..."
    cd /home/user/app/MicroServer/8003
    wine NSGameServer_CN_r.exe > /dev/null 2>&1 &
fi

if [ -d "/home/user/app/MicroServer/8004" ]; then
    echo "[+] Starting Zone 8004 (Elerd Kingdom)..."
    cd /home/user/app/MicroServer/8004
    wine NSGameServer_CN_r.exe > /dev/null 2>&1 &
fi

cd /home/user/app
echo "[+] Full 4-Zone Cloud Server Engine Online 24/7!"

# Keep container running indefinitely
while true; do
    sleep 60
done
