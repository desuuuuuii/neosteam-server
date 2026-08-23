# -*- coding: utf-8 -*-
import http.server
import socketserver
import os
import re

PORT = int(os.environ.get('PORT', 10000))

def get_playit_info():
    log_path = "/home/user/app/playit.log"
    if not os.path.exists(log_path):
        return "Initializing Playit router (please wait ~5s)..."
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        # Search for claim URL or assigned domain
        claim_match = re.search(r'(https://playit\.gg/claim/[a-zA-Z0-9]+)', content)
        if claim_match:
            return f'''<div style="margin-bottom:12px;"><a href="{claim_match.group(1)}" target="_blank" style="background:#238636; color:#fff; padding:12px 24px; border-radius:8px; text-decoration:none; font-weight:bold; font-size:16px; display:inline-block;">👉 CLICK HERE TO CLAIM YOUR GAME DOMAIN 👈</a></div><div style="font-size:13px; color:#8b949e; margin-top:8px;">Claim URL: {claim_match.group(1)}</div>'''
        
        domain_match = re.search(r'([a-zA-Z0-9\-]+\.(?:gl|ply|at)\.ply\.gg:\d+)', content)
        if domain_match:
            return f'<span style="color:#3fb950; font-size:22px; font-weight:bold;">🎮 Game Address: {domain_match.group(1)}</span>'
        
        # Show recent log snippet if still starting
        lines = [line.strip() for line in content.splitlines() if line.strip()][-6:]
        return f'<div style="text-align:left; font-family:monospace; font-size:12px; color:#58a6ff; background:#161b22; padding:10px; border-radius:6px;">' + '<br>'.join(lines) + '</div>'
    except Exception as e:
        return f"Status: {e}"

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        playit_status = get_playit_info()
        html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="5">
<title>NeoSteam Global MMO Server</title>
<style>
body {{ background:#0d1117; color:#c9d1d9; font-family:system-ui, sans-serif; display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0; padding:20px; }}
.card {{ background:#161b22; border:1px solid #30363d; border-radius:12px; padding:32px; text-align:center; max-width:640px; width:100%; box-shadow:0 8px 24px rgba(0,0,0,0.5); }}
h1 {{ color:#58a6ff; margin-bottom:8px; }}
.badge {{ background:rgba(46,160,67,0.2); color:#3fb950; border:1px solid #2ea043; padding:6px 14px; border-radius:20px; font-weight:bold; display:inline-block; margin-bottom:20px; }}
.info-box {{ background:#21262d; border:1px solid #30363d; border-radius:8px; padding:20px; margin:20px 0; }}
</style>
</head>
<body>
<div class="card">
    <div class="badge">● SERVER ONLINE 24/7</div>
    <h1>NeoSteam Global Server</h1>
    <p style="color:#8b949e; margin-bottom:16px;">Render Cloud Engine Active ($0 / month)</p>
    
    <div class="info-box">
        {playit_status}
    </div>
    
    <p style="font-size:13px; color:#8b949e;">Login & World Services active. Page refreshes every 5s automatically.</p>
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
