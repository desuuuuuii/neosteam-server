# -*- coding: utf-8 -*-
import http.server
import socketserver
import os
import re
import json

PORT = int(os.environ.get('PORT', 10000))

def parse_bore_ports():
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

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        login_port, game_port = parse_bore_ports()
        
        # 1. API Endpoint for nsstarter.exe Auto-Discovery
        if self.path == "/api/ports" or self.path == "/api/ports/":
            data = json.dumps({
                "status": "online" if (login_port and game_port) else "starting",
                "host": "159.223.110.159",
                "login_port": login_port,
                "game_port": game_port
            }).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        # 2. Web UI Dashboard
        status_color = "#3fb950" if (login_port and game_port) else "#f0883e"
        status_text = "● SERVER ONLINE 24/7" if (login_port and game_port) else "● INITIALIZING..."
        
        ports_html = f'''
        <div style="font-size:18px; margin-bottom:10px;">
            <strong style="color:#58a6ff;">Login Server:</strong> bore.pub:{login_port or '...'}
        </div>
        <div style="font-size:18px;">
            <strong style="color:#3fb950;">3D Game World:</strong> bore.pub:{game_port or '...'}
        </div>
        '''
        
        html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="5">
<title>NeoSteam Global MMO Server</title>
<style>
body {{ background:#0d1117; color:#c9d1d9; font-family:system-ui, sans-serif; display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0; padding:20px; }}
.card {{ background:#161b22; border:1px solid #30363d; border-radius:12px; padding:32px; text-align:center; max-width:600px; width:100%; box-shadow:0 8px 24px rgba(0,0,0,0.5); }}
h1 {{ color:#58a6ff; margin-bottom:8px; }}
.badge {{ background:rgba(46,160,67,0.2); color:{status_color}; border:1px solid {status_color}; padding:6px 14px; border-radius:20px; font-weight:bold; display:inline-block; margin-bottom:20px; }}
.info-box {{ background:#21262d; border:1px solid #30363d; border-radius:8px; padding:20px; margin:20px 0; word-break:break-all; line-height:1.6; }}
</style>
</head>
<body>
<div class="card">
    <div class="badge">{status_text}</div>
    <h1>NeoSteam Global Server</h1>
    <p>Cloud Engine Active on Render ($0 / month)</p>
    
    <div class="info-box">
        {ports_html}
    </div>
    
    <p style="font-size:13px; color:#8b949e;">Auto-Discovery API Active. Launch <strong>nsstarter.exe</strong> to play.</p>
</div>
</body>
</html>'''
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args): pass

print(f'[HTTP] Dashboard & API listening on port {PORT}...')
with socketserver.TCPServer(('0.0.0.0', PORT), Handler) as httpd:
    httpd.serve_forever()
