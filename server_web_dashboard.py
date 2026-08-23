# -*- coding: utf-8 -*-
import http.server
import socketserver
import os
import re
import json

PORT = int(os.environ.get('PORT', 10000))

def parse_bore_ports():
    bore_login = "/home/user/app/bore_login.log"
    bore_game = "/home/user/app/bore_game.log"
    login_p = 32881
    game_p = 39597
    
    if os.path.exists(bore_login):
        try:
            with open(bore_login, "r", encoding="utf-8", errors="ignore") as f:
                m = re.search(r'bore\.pub:(\d+)', f.read())
                if m: login_p = int(m.group(1))
        except: pass

    if os.path.exists(bore_game):
        try:
            with open(bore_game, "r", encoding="utf-8", errors="ignore") as f:
                m = re.search(r'bore\.pub:(\d+)', f.read())
                if m: game_p = int(m.group(1))
        except: pass

    return {"host": "159.223.110.159", "domain": "bore.pub", "login_port": login_p, "game_port": game_p}

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        ports_data = parse_bore_ports()
        
        # 1. API Route for nsstarter.exe Auto-Discovery
        if self.path in ['/api/ports', '/ports.json']:
            resp = json.dumps(ports_data).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
            return

        # 2. Web UI Dashboard
        conn_html = f'<div style="font-size:18px; color:#3fb950; font-weight:bold;">Login (3001): bore.pub:{ports_data["login_port"]} | Game (7001): bore.pub:{ports_data["game_port"]}</div>'
        html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="6">
<title>NeoSteam Global MMO Server</title>
<style>
body {{ background:#0d1117; color:#c9d1d9; font-family:system-ui, sans-serif; display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0; padding:20px; }}
.card {{ background:#161b22; border:1px solid #30363d; border-radius:12px; padding:32px; text-align:center; max-width:650px; width:100%; box-shadow:0 8px 24px rgba(0,0,0,0.5); }}
h1 {{ color:#58a6ff; margin-bottom:8px; }}
.badge {{ background:rgba(46,160,67,0.2); color:#3fb950; border:1px solid #2ea043; padding:6px 14px; border-radius:20px; font-weight:bold; display:inline-block; margin-bottom:20px; }}
.info-box {{ background:#21262d; border:1px solid #30363d; border-radius:8px; padding:20px; margin:20px 0; word-break:break-all; line-height:1.6; }}
</style>
</head>
<body>
<div class="card">
    <div class="badge">● SERVER ONLINE 24/7</div>
    <h1>NeoSteam Global Server</h1>
    <p>Cloud Engine Active on Render ($0 / month)</p>
    
    <div class="info-box">
        {conn_html}
    </div>
    
    <p style="font-size:13px; color:#8b949e;">Auto-Discovery Endpoint Active: <code>/api/ports</code></p>
</div>
</body>
</html>'''
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args): pass

print(f'[HTTP] Dashboard listening on port {PORT}...')
with socketserver.TCPServer(('0.0.0.0', PORT), Handler) as httpd:
    httpd.serve_forever()
