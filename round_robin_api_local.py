from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import urllib.request
import urllib.error
import threading
import time

# Backend application API instances
backends = [
    "http://localhost:5001",
    "http://localhost:5002",
    "http://localhost:5003"
]

# Health state for each backend
backend_status = {b: {"healthy": True, "failures": 0} for b in backends}

current_index = 0
FAILURE_THRESHOLD = 3
HEALTH_CHECK_INTERVAL = 5


def health_check():
    """Periodically check if unhealthy backends are back online."""
    while True:
        for backend in backends:
            if not backend_status[backend]["healthy"]:
                try:
                    req = urllib.request.Request(
                        backend,
                        data=b"{}",
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=2) as resp:
                        if resp.status == 200:
                            backend_status[backend]["healthy"] = True
                            backend_status[backend]["failures"] = 0
                            print(f"[HEALTH] Backend {backend} is healthy again")
                except Exception:
                    pass
        time.sleep(HEALTH_CHECK_INTERVAL)


class RoundRobinHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global current_index

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        attempts = 0
        while attempts < len(backends):
            backend = backends[current_index]
            current_index = (current_index + 1) % len(backends)
            attempts += 1

            if not backend_status[backend]["healthy"]:
                continue

            try:
                # 👇 Log which backend the router is forwarding to
                print(f"[Router] Forwarding request to {backend}")

                req = urllib.request.Request(
                    backend,
                    data=post_data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    response_data = resp.read()
                    self.send_response(resp.getcode())
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data)
                    return

            except Exception as e:
                backend_status[backend]["failures"] += 1
                print(f"[ERROR] Backend {backend} failed ({backend_status[backend]['failures']} times): {e}")
                if backend_status[backend]["failures"] >= FAILURE_THRESHOLD:
                    backend_status[backend]["healthy"] = False
                    print(f"[HEALTH] Marking backend {backend} as UNHEALTHY")

        self.send_response(502)
        self.end_headers()
        self.wfile.write(b'{"error":"All backends failed"}')


def run(port=8000):
    checker = threading.Thread(target=health_check, daemon=True)
    checker.start()

    server = HTTPServer(("localhost", port), RoundRobinHandler)
    print(f"Round Robin API running on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Router] Shutting down...")
        server.server_close()

if __name__ == "__main__":
    run(8000)
