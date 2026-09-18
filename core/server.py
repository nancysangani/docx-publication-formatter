"""
Local API Server Module (Phase 5 Microservice Integration)
-----------------------------------------------------------
Enables the standalone application binary to serve as an completely offline local network 
background engine listening on a port for direct microservice processing requests from MS Word.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from core.classifier import ElementClassifier

# Global runtime state allocation
classifier = ElementClassifier()

class LocalAddinHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS pre-flight authorization requests safely inside local environments"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """Processes real-time typography blocks transmitted from the integrated UI frame"""
        if self.path == "/classify-block":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data)
            
            # Unpack block stream payload targets
            block = payload["block"]
            total_blocks = payload["total_blocks"]
            
            # Execute high-precision validation check logic rules directly
            result = classifier.classify(block, total_blocks)
            
            # Return classified data block tags securely back to local pane layout frame
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(result).encode('utf-8'))

def run_server(port=8080):
    server = HTTPServer(('127.0.0.1', port), LocalAddinHandler)
    print(f"CodeNomad Architecture Core API Server Active on http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Local Core API Server thread...")
        server.server_close()
