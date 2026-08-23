# -*- coding: utf-8 -*-
"""
NeoSteam Global Cloud Server - Live Web Status Dashboard
Runs on Port 7860 for Hugging Face Spaces
"""

import http.server
import socketserver
import os
import time
import json
import psutil

PORT = 7860

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NeoSteam Global MMO Server - Status</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Roboto, sans-serif; }
        body { background: #0d1117; color: #c9d1d9; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 32px; max-width: 600px; width: 100%; box-shadow: 0 8px 24px rgba(0,0,0,0.5); text-align: center; }
        .badge { display: inline-flex; align-items: center; gap: 8px; background: rgba(46,160,67,0.15); color: #3fb950; border: 1px solid #2ea043; padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 14px; margin-bottom: 20px; }
        .dot { width: 10px; height: 10px; background: #3fb950; border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.2); } 100% { opacity: 1; transform: scale(1); } }
        h1 { color: #58a6ff; font-size: 28px; margin-bottom: 8px; font-weight: 700; }
        p.subtitle { color: #8b949e; margin-bottom: 28px; font-size: 15px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 28px; text-align: left; }
        .box { background: #21262d; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
        .box-title { color: #8b949e; font-size: 12px; text-transform: uppercase; margin-bottom: 4px; font-weight: 600; }
        .box-value { color: #f0f6fc; font-size: 18px; font-weight: 700; }
        .footer { color: #8b949e; font-size: 13px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="badge"><div class="dot"></div> SERVER ONLINE (24/7)</div>
        <h1>NeoSteam Global Server</h1>
        <p class="subtitle">Cloud-Hosted on Enterprise 16 GB RAM Infrastructure</p>
        
        <div class="grid">
            <div class="box">
                <div class="box-title">Server Status</div>
                <div class="box-value" style="color:#3fb950;">Active & Ready</div>
            </div>
            <div class="box">
                <div class="box-title">Hardware</div>
                <div class="box-value">2 vCPU / 16 GB RAM</div>
            </div>
            <div class="box">
                <div class="box-title">World Zones</div>
                <div class="box-value">8001 / 8002 / 8003 / 8004</div>
            </div>
            <div class="box">
                <div class="box-title">Connection Protocol</div>
                <div class="box-value" style="color:#58a6ff;">Direct TCP 3001/7001</div>
            </div>
        </div>

        <div class="footer">
            To play, launch <strong>nsstarter.exe</strong> on your PC.
        </div>
    </div>
</body>
</html>
"""

class StatusHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(HTML_TEMPLATE.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(HTML_TEMPLATE.encode('utf-8'))

    def log_message(self, format, *args):
        pass

def run():
    print(f"[HTTP] Status Web Dashboard listening on port {PORT}...")
    with socketserver.TCPServer(("", PORT), StatusHandler) as httpd:
        httpd.serve_forever()

if __name__ == '__main__':
    run()
