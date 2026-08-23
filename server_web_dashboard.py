# -*- coding: utf-8 -*-
import http.server
import socketserver
import os

PORT = int(os.environ.get('PORT', 10000))

HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>NeoSteam Global MMO Server</title>
<style>
body { background:#0d1117; color:#c9d1d9; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
.card { background:#161b22; border:1px solid #30363d; border-radius:12px; padding:32px; text-align:center; max-width:500px; }
h1 { color:#58a6ff; margin-bottom:8px; }
.badge { background:rgba(46,160,67,0.2); color:#3fb950; border:1px solid #2ea043; padding:6px 14px; border-radius:20px; font-weight:bold; }
</style>
</head>
<body>
<div class="card">
    <div class="badge">SERVER ONLINE 24/7</div>
    <h1>NeoSteam Global Server</h1>
    <p>Render Cloud Engine Active</p>
</div>
</body>
</html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(HTML.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(HTML.encode('utf-8'))
    def log_message(self, format, *args): pass

print(f'[HTTP] Dashboard listening on port {PORT}...')
with socketserver.TCPServer(('0.0.0.0', PORT), Handler) as httpd:
    httpd.serve_forever()
