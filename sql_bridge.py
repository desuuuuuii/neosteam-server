# -*- coding: utf-8 -*-
"""
Universal Zero-SQL TDS Bridge for NeoSteam Server
Supports TDS 4.2, 7.0, 7.1, 7.2 (Wine ODBC, FreeTDS, unixODBC, native Winsock)
"""

import socket
import struct
import threading
import sqlite3
import os
import re
import time

DB_PATH = "/home/user/app/neosteam.sqlite" if os.name != 'nt' else r"D:\NeoSteam\neosteam.sqlite"
LOG_PATH = "/home/user/app/sql_bridge.log" if os.name != 'nt' else r"D:\NeoSteam\sql_bridge.log"

def log_msg(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except: pass

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS UserList (
        Seq INTEGER PRIMARY KEY AUTOINCREMENT,
        UserId TEXT UNIQUE COLLATE NOCASE,
        UserPasswd TEXT,
        UserPasswdSha TEXT DEFAULT '',
        UserMail TEXT DEFAULT '',
        UserStat INTEGER DEFAULT 0,
        UserType INTEGER DEFAULT 1,
        ConnGameIp1 INTEGER DEFAULT 0,
        ConnGameIp2 INTEGER DEFAULT 0,
        ConnGameIp3 INTEGER DEFAULT 0,
        ConnGameIp4 INTEGER DEFAULT 0,
        ConnGamePort INTEGER DEFAULT 0,
        LoginTime TEXT DEFAULT '',
        LogoutTime TEXT DEFAULT '',
        CharCount INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS CharacterList (
        CharSeq INTEGER PRIMARY KEY AUTOINCREMENT,
        UserSeq INTEGER,
        CharName TEXT UNIQUE,
        Nation INTEGER DEFAULT 1,
        Job INTEGER DEFAULT 1,
        Level INTEGER DEFAULT 1,
        Exp INTEGER DEFAULT 0,
        Hp INTEGER DEFAULT 100,
        MaxHp INTEGER DEFAULT 100,
        Mp INTEGER DEFAULT 100,
        MaxMp INTEGER DEFAULT 100,
        Steam INTEGER DEFAULT 100,
        MaxSteam INTEGER DEFAULT 100,
        Str INTEGER DEFAULT 10,
        Dex INTEGER DEFAULT 10,
        Int INTEGER DEFAULT 10,
        Gold INTEGER DEFAULT 1000,
        MapNo INTEGER DEFAULT 1,
        PosX REAL DEFAULT 100.0,
        PosY REAL DEFAULT 100.0,
        PosZ REAL DEFAULT 100.0,
        DeleteFlag INTEGER DEFAULT 0,
        CreateTime TEXT DEFAULT ''
    );
    INSERT OR IGNORE INTO UserList (UserId, UserPasswd, UserType) VALUES ('admin', '1234', 2);
    INSERT OR IGNORE INTO UserList (UserId, UserPasswd, UserType) VALUES ('test', '1234', 1);
    INSERT OR IGNORE INTO UserList (UserId, UserPasswd, UserType) VALUES ('zevan', '1234', 1);
    """)
    conn.commit()
    conn.close()
    log_msg("SQLite Database Initialized!")

def execute_sql(query_text):
    try:
        q = query_text.strip()
        if not q:
            return None, None

        log_msg(f"SQL QUERY: {q}")

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Map common MS SQL patterns to SQLite
        q_clean = re.sub(r'WITH\s*\(NOLOCK\)', '', q, flags=re.IGNORECASE)
        q_clean = re.sub(r'TOP\s+\d+', '', q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r'NOCOUNT\s+ON', '', q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r'SET\s+\w+\s+\w+', '', q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r'\bGO\b', '', q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r'\bdbo\.', '', q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r'\bMain_DB_1\.', '', q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r'\bGame_DB_1_1\.', '', q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r'GETDATE\(\)', "datetime('now')", q_clean, flags=re.IGNORECASE)
        q_clean = re.sub(r'@@IDENTITY', 'last_insert_rowid()', q_clean, flags=re.IGNORECASE)
        q_clean = q_clean.strip()

        if not q_clean or q_clean.startswith('--'):
            conn.close()
            return None, None

        # Check if user query
        m_user = re.search(r"UserId\s*=\s*'([^']+)'", q_clean, re.IGNORECASE)
        if m_user:
            # Ensure user exists in table
            uid = m_user.group(1)
            cur.execute("INSERT OR IGNORE INTO UserList (UserId, UserPasswd, UserType) VALUES (?, '1234', 1)", (uid,))
            conn.commit()

        is_select = q_clean.upper().lstrip().startswith('SELECT')

        cur.execute(q_clean)

        if is_select:
            rows = cur.fetchall()
            if rows:
                cols = [desc[0] for desc in cur.description]
            elif cur.description:
                cols = [desc[0] for desc in cur.description]
                rows = []
            else:
                cols, rows = None, None
        else:
            conn.commit()
            cols, rows = None, None

        conn.close()
        log_msg(f"SQL SUCCESS: is_select={is_select}, rows={len(rows) if rows is not None else 0}")
        return cols, rows

    except Exception as e:
        log_msg(f"SQL ERROR: {e} on query: {query_text}")
        return None, None

def tds_col_meta(cols):
    col_count = len(cols)
    data = struct.pack('<BH', 0x81, col_count)
    for col in cols:
        col_name = col.encode('utf-16le')
        data += struct.pack('<HHB', 0, 0x0009, 0xe7)
        data += struct.pack('<H', 8000)
        data += b'\x09\x04\xd0\x00\x34'
        data += struct.pack('<B', len(col)) + col_name
    return data

def tds_row(row_values):
    data = b'\xd1'
    for v in row_values:
        if v is None:
            data += b'\xff\xff'
        else:
            encoded = str(v).encode('utf-16le')
            data += struct.pack('<H', len(encoded)) + encoded
    return data

def tds_done(rows_affected=0):
    return struct.pack('<BHHQ', 0xfd, 0x00, 0x00, rows_affected)

def tds_packet(payload, pkt_type=0x04):
    hdr = struct.pack('>BBHHBB', pkt_type, 0x01, len(payload) + 8, 0, 1, 0)
    return hdr + payload

def build_resultset(cols, rows):
    payload = tds_col_meta(cols)
    for row in rows:
        payload += tds_row(list(row))
    payload += tds_done(len(rows))
    return tds_packet(payload)

def build_empty_done():
    return tds_packet(tds_done(0))

def extract_queries(raw_bytes):
    if len(raw_bytes) < 8:
        return []
    pkt_type = raw_bytes[0]
    # Packet types: 0x01 (SQL Batch), 0x03 (RPC), 0x0E (Transaction Manager)
    sql_bytes = raw_bytes[8:]
    queries = []
    
    # Try utf-16le
    try:
        t = sql_bytes.decode('utf-16le', errors='ignore')
        for part in re.split(r'[\x00\r\n]+', t):
            part = part.strip()
            if len(part) >= 4 and any(k in part.upper() for k in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'EXEC']):
                queries.append(part)
    except: pass
    
    # Try utf-8/ascii
    try:
        t2 = sql_bytes.decode('utf-8', errors='ignore')
        for part in re.split(r'[\x00\r\n]+', t2):
            part = part.strip()
            if len(part) >= 4 and any(k in part.upper() for k in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'EXEC']):
                if part not in queries:
                    queries.append(part)
    except: pass

    if not queries:
        try:
            raw_str = sql_bytes.decode('utf-16le', errors='ignore').strip()
            if raw_str: queries.append(raw_str)
        except: pass
        
    return queries

def handle_tds_client(client_sock, addr):
    try:
        client_sock.settimeout(60)
        log_msg(f"New Database Connection from {addr}")

        while True:
            pkt = client_sock.recv(8192)
            if not pkt or len(pkt) < 8:
                break

            pkt_type = pkt[0]
            log_msg(f"TDS Packet Received: Type=0x{pkt_type:02x}, Length={len(pkt)}")

            if pkt_type == 0x12:  # Pre-Login Handshake
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
                client_sock.sendall(tds_packet(prelogin_payload))

            elif pkt_type in [0x01, 0x02, 0x10]:  # Login / Login7 / Pre-TDS Login
                # Send LoginACK + DONE
                login_ack = (
                    b'\xad'
                    b'\x36\x00'
                    b'\x01'
                    b'\x71\x00\x00\x01'
                    b'\x16\x00'
                    + "Microsoft SQL Server".encode('utf-16le')
                    + b'\x09\x00\x08\x00'
                )
                client_sock.sendall(tds_packet(login_ack + tds_done()))
                log_msg("Sent LOGINACK Success to client!")

            else:
                # Query / Command packet
                queries = extract_queries(pkt)
                log_msg(f"Extracted queries ({len(queries)}): {queries}")
                response = None

                for q in queries:
                    if not q: continue
                    cols, rows = execute_sql(q)
                    if cols is not None:
                        response = build_resultset(cols, rows)
                        break

                if response is None:
                    response = build_empty_done()

                client_sock.sendall(response)

    except Exception as e:
        log_msg(f"TDS Client Exception: {e}")
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
        log_msg(f"Universal TDS server listening on port {port}...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_tds_client, args=(conn, addr), daemon=True).start()
    except Exception as e:
        log_msg(f"SQL Bridge Bind Error: {e}")

if __name__ == '__main__':
    start_sql_bridge()
