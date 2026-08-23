# -*- coding: utf-8 -*-
import http.server
import socketserver
import os
import re

PORT = int(os.environ.get('PORT', 10000))

def get_connection_info():
    info_html = []
    
    # 1. Check Playit log
    playit_log = "/home/user/app/playit.log"
    if os.path.exists(playit_log):
        try:
            with open(playit_log, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            claim = re.search(r'(https://playit\.gg/claim/[a-zA-Z0-9]+)', content)
            if claim:
                info_html.append(f'<p style="margin-bottom:12px;"><a href="{claim.group(1)}" target="_blank" style="color:#58a6ff; font-weight:bold; font-size:18px; text-decoration:underline;">👉 Click Here to Claim Your Playit 24/7 Domain: {claim.group(1)}</a></p>')
            domain = re.search(r'([a-zA-Z0-9\-]+\.(?:gl|ply|at)\.ply\.gg:\d+)', content)
            if domain:
                info_html.append(f'<p style="color:#3fb950; font-size:18px; font-weight:bold;">🎮 Playit Address: {domain.group(1)}</p>')
        except Exception as e:
            pass

    # 2. Check Bore logs
    bore_login = "/home/user/app/bore_login.log"
    bore_game = "/home/user/app/bore_game.log"
    bore_ports = []
    for path, name in [(bore_login, "Login (3001)"), (bore_game, "Game (7001)")]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read()
                m = re.search(r'bore\.pub:(\d+)', txt)
                if m:
                    bore_ports.append(f"<strong>{name}:</strong> bore.pub:{m.group(1)}")
            except:
                pass
    
    if bore_ports:
        info_html.append('<div style="margin-top:10px; color:#f0f6fc; font-size:16px;">' + " | ".join(bore_ports) + '</div>')

    if not info_html:
        return "<p style='color:#8b949e;'>Initializing connection network... Refreshing in 5s...</p>"
    
    return "".join(info_html)

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        conn_status = get_connection_info()
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
        {conn_status}
    </div>
    
    <p style="font-size:13px; color:#8b949e;">Page refreshes automatically. Login & 3D World services running.</p>
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
