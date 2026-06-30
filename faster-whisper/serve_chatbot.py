import http.server
import socketserver
import os
from pathlib import Path

PORT = 7860
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def run_server():
    Handler = MyHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🌐 Chatbot server running on:")
        print(f"   http://localhost:{PORT}")
        print(f"   http://127.0.0.1:{PORT}")
        print(f"\n📝 Open in Chrome for microphone support")
        print(f"Press CTRL+C to stop")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
