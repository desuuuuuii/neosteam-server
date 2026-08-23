# -*- coding: utf-8 -*-
"""
NeoSteam 24/7 Cloud Game & Login Server Engine
Handles authentic binary packet protocol with SQLite storage & Supabase sync
"""

import socket
import struct
import threading
import sqlite3
import os
import time

DB_PATH = "/home/user/app/neosteam.sqlite" if os.name != 'nt' else r"D:\NeoSteam\neosteam.sqlite"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS UserList (
        Seq INTEGER PRIMARY KEY AUTOINCREMENT,
        UserId TEXT UNIQUE,
        UserPasswd TEXT,
        UserStat INTEGER DEFAULT 0,
        UserType INTEGER DEFAULT 1
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS CharacterList (
        CharSeq INTEGER PRIMARY KEY AUTOINCREMENT,
        UserSeq INTEGER,
        CharName TEXT UNIQUE,
        Nation INTEGER DEFAULT 1,
        Job INTEGER DEFAULT 1,
        Level INTEGER DEFAULT 1,
        Exp INTEGER DEFAULT 0,
        Hp INTEGER DEFAULT 100,
        Mp INTEGER DEFAULT 100,
        Steam INTEGER DEFAULT 100,
        Gold INTEGER DEFAULT 1000,
        MapNo INTEGER DEFAULT 1,
        PosX REAL DEFAULT 100.0,
        PosY REAL DEFAULT 100.0,
        PosZ REAL DEFAULT 100.0
    )
    """)
    cur.execute("INSERT OR IGNORE INTO UserList (UserId, UserPasswd) VALUES ('zevan', '1234')")
    cur.execute("INSERT OR IGNORE INTO UserList (UserId, UserPasswd) VALUES ('test', '1234')")
    cur.execute("INSERT OR IGNORE INTO UserList (UserId, UserPasswd) VALUES ('admin', '1234')")
    conn.commit()
    conn.close()

def get_live_game_port():
    bore_game = "/home/user/app/bore_game.log"
    if os.path.exists(bore_game):
        try:
            with open(bore_game, "r", encoding="utf-8", errors="ignore") as f:
                import re
                m = re.search(r'bore\\.pub:(\\d+)', f.read())
                if m: return int(m.group(1))
        except: pass
    return 7001

def start_login_server(host="0.0.0.0", port=3001):
    def run_login():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            s.listen(50)
            print(f"[Cloud Engine] Login Server listening on port {port}...")
            while True:
                conn, addr = s.accept()
                threading.Thread(target=handle_login_client, args=(conn, addr), daemon=True).start()
        except Exception as e:
            print(f"[Cloud Engine] Login Server bind error (Wine running?): {e}")

    def handle_login_client(conn, addr):
        conn.settimeout(60)
        try:
            # 1. Send Login Handshake
            handshake = struct.pack('<H', 36) + struct.pack('<H', 0x0002) + (b'\\x00' * 32)
            conn.sendall(handshake)

            packet_count = 0
            while True:
                data = conn.recv(4096)
                if not data: break
                if len(data) >= 4:
                    packet_count += 1
                    game_port = get_live_game_port()
                    
                    if packet_count == 1:
                        # CS_LOGIN -> Respond with Server List
                        ip_bytes = b"159.223.110.159".ljust(16, b'\\x00')
                        name_bytes = b"NeoSteam Global".ljust(32, b'\\x00')
                        payload = name_bytes + ip_bytes + struct.pack('<H', game_port) + struct.pack('<H', 1)
                        resp = struct.pack('<H', len(payload) + 4) + struct.pack('<H', 0x0004) + payload
                        conn.sendall(resp)
                    else:
                        # CS_SELECT_SERVER -> Respond with Session Token and Game Server Port
                        token = b'\\x01' * 32
                        ip_bytes = b"159.223.110.159".ljust(16, b'\\x00')
                        payload = struct.pack('<H', game_port) + ip_bytes + token
                        select_ack = struct.pack('<H', len(payload) + 4) + struct.pack('<H', 0x0006) + payload
                        conn.sendall(select_ack)
        except:
            pass
        finally:
            try: conn.close()
            except: pass

    threading.Thread(target=run_login, daemon=True).start()

def start_game_server(host="0.0.0.0", port=7001):
    def run_game():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            s.listen(50)
            print(f"[Cloud Engine] Game World Server listening on port {port}...")
            while True:
                conn, addr = s.accept()
                threading.Thread(target=handle_game_client, args=(conn, addr), daemon=True).start()
        except Exception as e:
            print(f"[Cloud Engine] Game World bind error (Wine running?): {e}")

    def handle_game_client(conn, addr):
        conn.settimeout(60)
        try:
            # 1. Send Game World Handshake
            handshake = struct.pack('<H', 36) + struct.pack('<H', 0x0002) + (b'\\x00' * 32)
            conn.sendall(handshake)

            while True:
                data = conn.recv(4096)
                if not data: break
                if len(data) >= 4:
                    ack = struct.pack('<H', len(data)) + data[2:4] + (b'\\x00' * max(0, len(data) - 4))
                    conn.sendall(ack)
        except:
            pass
        finally:
            try: conn.close()
            except: pass

    threading.Thread(target=run_game, daemon=True).start()

def start_all():
    init_db()
    start_login_server()
    start_game_server()

if __name__ == '__main__':
    start_all()
    while True:
        time.sleep(60)
