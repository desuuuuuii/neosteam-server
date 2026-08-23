# -*- coding: utf-8 -*-
"""
Zero-SQL TDS Bridge for NeoSteam Server
Emulates MS SQL Server on Port 1433 using SQLite database
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
    
    # 1. Accounts Table (Main_DB_1.dbo.UserList)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS UserList (
        Seq INTEGER PRIMARY KEY AUTOINCREMENT,
        UserId TEXT UNIQUE,
        UserPasswd TEXT,
        UserPasswdSha TEXT,
        UserMail TEXT,
        UserStat INTEGER DEFAULT 0,
        UserType INTEGER DEFAULT 1,
        ConnGameIp1 INTEGER DEFAULT 0,
        ConnGameIp2 INTEGER DEFAULT 0,
        ConnGameIp3 INTEGER DEFAULT 0,
        ConnGameIp4 INTEGER DEFAULT 0,
        ConnGamePort INTEGER DEFAULT 0,
        LoginTime TEXT,
        LogoutTime TEXT
    )
    """)
    
    # 2. Characters Table (Game_DB_1_1.dbo.CharacterList)
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
        PosZ REAL DEFAULT 100.0,
        DeleteFlag INTEGER DEFAULT 0
    )
    """)
    
    # Insert default admin/test accounts
    cur.execute("INSERT OR IGNORE INTO UserList (UserId, UserPasswd, UserType) VALUES ('admin', '1234', 2)")
    cur.execute("INSERT OR IGNORE INTO UserList (UserId, UserPasswd, UserType) VALUES ('test', '1234', 1)")
    cur.execute("INSERT OR IGNORE INTO UserList (UserId, UserPasswd, UserType) VALUES ('zevan', '1234', 1)")
    
    conn.commit()
    conn.close()
    print("[SQL Bridge] SQLite Database Initialized!")

def handle_tds_client(client_sock, addr):
    try:
        client_sock.settimeout(60)
        
        # 1. Handle TDS Pre-Login Handshake
        data = client_sock.recv(4096)
        if not data or len(data) < 8:
            return
            
        pkt_type = data[0]
        
        if pkt_type == 0x12:  # Pre-Login packet
            # Send Pre-Login Response (Version 9.0.2047, Encryption: Not Supported)
            prelogin_payload = (
                b'\x00\x00\x1a\x00\x06'
                b'\x01\x00\x20\x00\x01'
                b'\x02\x00\x21\x00\x01'
                b'\x03\x00\x22\x00\x04'
                b'\xff'
                b'\x09\x00\x08\x00\x00\x00'
                b'\x02'
                b'\x00'
                b'\x00\x00\x00\x00'
            )
            hdr = struct.pack('>BBHHBB', 0x04, 0x01, len(prelogin_payload) + 8, 0, 1, 0)
            client_sock.sendall(hdr + prelogin_payload)
            
            # 2. Receive Login7 Packet
            login_data = client_sock.recv(4096)
            if not login_data:
                return
                
            # Send LoginAck + Done token stream
            login_ack = (
                b'\xad'
                b'\x36\x00'
                b'\x01'
                b'\x71\x00\x00\x01'
                b'\x16\x00'
                + "Microsoft SQL Server".encode('utf-16le')
                + b'\x09\x00\x08\x00'
            )
            done_token = struct.pack('<BHHQ', 0xfd, 0x00, 0, 0)
            
            payload = login_ack + done_token
            hdr = struct.pack('>BBHHBB', 0x04, 0x01, len(payload) + 8, 0, 1, 0)
            client_sock.sendall(hdr + payload)
            
        # 3. Query Execution Loop
        while True:
            pkt = client_sock.recv(8192)
            if not pkt or len(pkt) < 8:
                break
                
            done_token = struct.pack('<BHHQ', 0xfd, 0x00, 0, 0)
            hdr = struct.pack('>BBHHBB', 0x04, 0x01, len(done_token) + 8, 0, 1, 0)
            client_sock.sendall(hdr + done_token)
            
    except Exception as e:
        pass
    finally:
        try: client_sock.close()
        except: pass

def start_sql_bridge(host="0.0.0.0", port=1433):
    init_db()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((host, port))
        s.listen(50)
        print(f"[SQL Bridge] Listening for MS SQL TDS connections on port {port}...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_tds_client, args=(conn, addr), daemon=True).start()
    except Exception as e:
        print(f"[SQL Bridge] Error: {e}")

if __name__ == '__main__':
    start_sql_bridge()
