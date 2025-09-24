#!/usr/bin/env python3
"""
Serve the standalone HTML test page to verify API calls work without Streamlit

This helps isolate whether the webhook issue is Streamlit-specific.
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8502

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow API calls
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # Change to project root
    root = Path(__file__).parent.parent
    os.chdir(root)
    
    print("=" * 60)
    print("Starting HTML Test Server")
    print("=" * 60)
    print(f"Serving at: http://localhost:{PORT}/test_api_standalone.html")
    print("\nThis page tests the API directly without Streamlit")
    print("to help identify if the webhook issue is Streamlit-specific.")
    print("\nMake sure the backend is running:")
    print("  python -m uvicorn src.api.main:app --reload --port 8001")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server")
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    main()
