#!/usr/bin/env python3
"""app.py - 1-Click Launch for the YouTube Agent Web Dashboard.
Opens http://localhost:5000 in your browser automatically.
"""
import sys
import webbrowser
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from web import server

def open_browser(port):
    time.sleep(0.8)
    url = f"http://localhost:{port}"
    print(f"Opening browser at: {url} ...")
    webbrowser.open(url)

def main():
    port = 5000
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    srv = server.start_server(port)
    try:
        print(f"Server is running at http://localhost:{port} (Press Ctrl+C to stop)")
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping YouTube Agent Dashboard.")
        srv.server_close()

if __name__ == "__main__":
    main()
