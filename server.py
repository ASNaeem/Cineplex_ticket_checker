import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from checker import run_checker

# Fix encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check endpoint to keep cloud service awake 24/7."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {"status": "alive", "service": "Cineplex Ticket Checker"}
        self.wfile.write(str(response).encode('utf-8'))

    def log_message(self, format, *args):
        # Suppress verbose HTTP ping logs
        return

def start_http_server(port=8080):
    server = HTTPServer(('0.0.0.0', port), PingHandler)
    print(f"🌐 Keep-Alive HTTP Health Server listening on port {port}...")
    server.serve_forever()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    
    # Start HTTP server in background thread to prevent sleep on Render/Railway
    http_thread = threading.Thread(target=start_http_server, args=(port,), daemon=True)
    http_thread.start()

    # Start main ticket checking loop
    run_checker()
