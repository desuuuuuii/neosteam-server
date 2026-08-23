# -*- coding: utf-8 -*-
"""
Full TDS SQL Bridge for NeoSteam Server
Parses actual T-SQL queries and returns proper resultsets from SQLite
"""

import socket
import struct
import threading
import sqlite3
import os
import re
import time

DB_PATH = "/home/user/app/neosteam.sqlite" if os.name != 'nt' else r"D:\NeoSteam\neosteam.sqlite"

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
    print("[SQL Bridge] SQLite Database Initialized!")

def execute_sql(query_text):
    """Execute SQL against SQLite and return (columns, rows) or (None, None) for no-result queries."""
    try:
        # Normalize the query
        q = query_text.strip()
        if not q:
            return None, None

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Map common MS SQL patterns to SQLite
        q = re.sub(r'WITH\s*\(NOLOCK\)', '', q, flags=re.IGNORECASE)
        q = re.sub(r'TOP\s+\d+', '', q, flags=re.IGNORECASE)
        q = re.sub(r'NOCOUNT\s+ON', '', q, flags=re.IGNORECASE)
        q = re.sub(r'SET\s+\w+\s+\w+', '', q, flags=re.IGNORECASE)
        q = re.sub(r'\bGO\b', '', q, flags=re.IGNORECASE)
        q = re.sub(r'\bdbo\.', '', q, flags=re.IGNORECASE)
        q = re.sub(r'\bMain_DB_1\.', '', q, flags=re.IGNORECASE)
        q = re.sub(r'\bGame_DB_1_1\.', '', q, flags=re.IGNORECASE)
        q = re.sub(r'GETDATE\(\)', "datetime('now')", q, flags=re.IGNORECASE)
        q = re.sub(r'@@IDENTITY', 'last_insert_rowid()', q, flags=re.IGNORECASE)
        q = q.strip()

        if not q or q.startswith('--'):
            conn.close()
            return None, None

        is_select = q.upper().lstrip().startswith('SELECT')

        cur.execute(q)

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
        return cols, rows

    except Exception as e:
        return None, None


# ---------- TDS ENCODING HELPERS ----------

def tds_varchar(s):
    """Encode a string as TDS NVARCHAR token value (utf-16le with 2-byte length prefix)."""
    if s is None:
        return b'\xff\xff'  # NULL
    encoded = str(s).encode('utf-16le')
    return struct.pack('<H', len(encoded)) + encoded

def tds_int(v):
    """Encode a 4-byte integer value."""
    return struct.pack('<i', int(v) if v is not None else 0)

def tds_col_meta(cols):
    """Build a COLMETADATA token (0x81) for the given column names."""
    # 0x81 = COLMETADATA
    col_count = len(cols)
    data = struct.pack('<BH', 0x81, col_count)
    for col in cols:
        # UserType=0, Flags=0x0009 (nullable), TypeInfo=NVARCHARMAX, ColName
        col_name = col.encode('utf-16le')
        data += struct.pack('<HHB', 0, 0x0009, 0xe7)  # NVARCHAR type
        data += struct.pack('<H', 8000)  # max length
        data += b'\x09\x04\xd0\x00\x34'  # LCID/collation
        data += struct.pack('<B', len(col)) + col_name
    return data

def tds_row(row_values):
    """Build a ROW token (0xD1) for one result row."""
    data = b'\xd1'
    for v in row_values:
        if v is None:
            data += b'\xff\xff'
        else:
            encoded = str(v).encode('utf-16le')
            data += struct.pack('<H', len(encoded)) + encoded
    return data

def tds_done(rows_affected=0):
    """Build a DONE token (0xFD)."""
    return struct.pack('<BHHQ', 0xfd, 0x00, 0x00, rows_affected)

def tds_packet(payload, pkt_type=0x04):
    """Wrap payload in TDS packet header."""
    hdr = struct.pack('>BBHHBB', pkt_type, 0x01, len(payload) + 8, 0, 1, 0)
    return hdr + payload


def build_resultset(cols, rows):
    """Build a full TDS resultset: COLMETADATA + ROWs + DONE."""
    payload = tds_col_meta(cols)
    for row in rows:
        payload += tds_row(list(row))
    payload += tds_done(len(rows))
    return tds_packet(payload)


def build_empty_done():
    return tds_packet(tds_done(0))


def extract_queries(raw_bytes):
    """Extract SQL text from a TDS batch packet (type 0x01)."""
    if len(raw_bytes) < 8:
        return []
    pkt_type = raw_bytes[0]
    if pkt_type == 0x01:  # SQL Batch
        sql_bytes = raw_bytes[8:]
        try:
            text = sql_bytes.decode('utf-16le', errors='ignore')
        except:
            try:
                text = sql_bytes.decode('utf-8', errors='ignore')
            except:
                return []
        return [text.strip()]
    return []


def handle_tds_client(client_sock, addr):
    try:
        client_sock.settimeout(60)

        # 1. Pre-Login handshake
        data = client_sock.recv(4096)
        if not data or len(data) < 8:
            return

        if data[0] == 0x12:  # Pre-Login
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

            # 2. Login7
            login_data = client_sock.recv(4096)
            if not login_data:
                return

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

        # 3. Query loop
        while True:
            pkt = client_sock.recv(8192)
            if not pkt or len(pkt) < 8:
                break

            queries = extract_queries(pkt)
            response = None

            for q in queries:
                if not q:
                    continue
                cols, rows = execute_sql(q)
                if cols is not None:
                    response = build_resultset(cols, rows)
                    break

            if response is None:
                response = build_empty_done()

            client_sock.sendall(response)

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
        print(f"[SQL Bridge] Full TDS server on port {port}...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_tds_client, args=(conn, addr), daemon=True).start()
    except Exception as e:
        print(f"[SQL Bridge] Error: {e}")

if __name__ == '__main__':
    start_sql_bridge()
