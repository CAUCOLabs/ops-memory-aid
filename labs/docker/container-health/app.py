import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

MODE = os.getenv("MODE", "healthy")
PORT = 8000

if MODE == "crash":
    print("FATAL: Simulated application startup failure", flush=True)
    sys.exit(1)

if MODE not in {"healthy", "unhealthy"}:
    print(f"FATAL: Unsupported MODE={MODE}", flush=True)
    sys.exit(2)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            status = 200 if MODE == "healthy" else 503
            message = "OK" if status == 200 else "Service Unavailable"

            self.send_response(status)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(message.encode())
        else:
            self.send_error(404, "Not Found")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    print(f"Starting HTTP server on port {PORT} (mode={MODE})", flush=True)
    server.serve_forever()
