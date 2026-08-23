# -*- coding: utf-8 -*-
import http.server
import socketserver
import os
import re
import json
import subprocess

PORT = int(os.environ.get('PORT', 10000))

def parse_live_ports():
    login_port = 0
    game_port = 0
    
    bore_login = "/home/user/app/bore_login.log"
    bore_game = "/home/user/app/bore_game.log"
    
    if os.path.exists(bore_login):
        try:
            with open(bore_login, "r", encoding="utf-8", errors="ignore") as f:
                m = re.search(r'bore\.pub:(\d+)', f.read())
                if m: login_port = int(m.group(1))
        except: pass
        
    if os.path.exists(bore_game):
        try:
            with open(bore_game, "r", encoding="utf-8", errors="ignore") as f:
                m = re.search(r'bore\.pub:(\d+)', f.read())
                if m: game_port = int(m.group(1))
        except: pass
        
    return login_port, game_port

def read_log(path):
    if not os.path.exists(path): return "No log file found."
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()[-2000:]
    except Exception as e:
        return str(e)

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        login_port, game_port = parse_live_ports()
        
        # 1. API Diagnostics Endpoint
        if self.path.startswith("/api/ports") or self.path.startswith("/ports") or self.path.startswith("/api/debug"):
            data = {
                "status": "online" if (login_port and game_port) else "initializing",
                "host": "159.223.110.159",
                "domain": "bore.pub",
                "login_port": login_port,
                "game_port": game_port,
                "login_log": read_log("/home/user/app/login.log"),
                "game_log": read_log("/home/user/app/game.log")
            }
            body = json.dumps(data, indent=2).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # 2. Web UI Dashboard
        status_text = f"Login (3001): <strong>bore.pub:{login_port}</strong> | Game (7001): <strong>bore.pub:{game_port}</strong>"
        html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="5">
<title>NeoSteam Global Server</title>
<style>
body {{ background:#0d1117; color:#c9d1d9; font-family:system-ui, sans-serif; display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0; padding:20px; }}
.card {{ background:#161b22; border:1px solid #30363d; border-radius:12px; padding:32px; text-align:center; max-width:700px; width:100%; }}
h1 {{ color:#58a6ff; margin-bottom:8px; }}
.badge {{ background:rgba(46,160,67,0.2); color:#3fb950; border:1px solid #2ea043; padding:6px 14px; border-radius:20px; font-weight:bold; display:inline-block; margin-bottom:20px; }}
.box {{ background:#21262d; border:1px solid #30363d; border-radius:8px; padding:16px; margin:20px 0; font-size:16px; color:#f0f6fc; }}
pre {{ background:#090d13; padding:12px; border-radius:6px; text-align:left; font-size:11px; overflow-x:auto; max-height:200px; }}
</style>
</head>
<body>
<div class="card">
    <div class="badge">● SERVER ONLINE 24/7</div>
    <h1>NeoSteam Global Server</h1>
    <p>Render Cloud Engine Active ($0 / month)</p>
    <div class="box">{status_text}</div>
    <pre>Login Log:\n{read_log("/home/user/app/login.log")}\n\nGame Log:\n{read_log("/home/user/app/game.log")}</pre>
</div>
</body>
</html>'''
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args): pass

print(f'[HTTP] Dashboard listening on port {PORT}...')
with socketserver.TCPServer(('0.0.0.0', PORT), Handler) as httpd:
    httpd.serve_forever()
