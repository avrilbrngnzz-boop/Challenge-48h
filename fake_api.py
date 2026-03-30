# fake_api.py
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = [
            {
                "station_id": "FR_69001",
                "latitude": 45.748,
                "longitude": 4.847,
                "pollution_index": 42.5
            }
        ]
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

HTTPServer(("localhost", 8001), Handler).serve_forever()