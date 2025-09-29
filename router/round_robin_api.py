from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request, urllib.error, json, threading, time, os, logging


os.makedirs("/logs", exist_ok=True)  
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/logs/router.log"), 
        logging.StreamHandler()                  
    ]
)


BACKENDS = os.getenv(
    "BACKENDS",
    "http://backend1:5001,http://backend2:5002,http://backend3:5003"
).split(",")

backend_status = {b: {"healthy": True, "failures": 0} for b in BACKENDS}
current_index = 0
FAILURE_THRESHOLD = 3
HEALTH_CHECK_INTERVAL = 5


def health_check():
    """Background thread: periodically tries to recover unhealthy backends."""
    while True:
        for backend in BACKENDS:
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
                            logging.info(f"[HEALTH] {backend} recovered")
                except Exception:
                    pass
        time.sleep(HEALTH_CHECK_INTERVAL)


class RoundRobinHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global current_index
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        attempts = 0
        while attempts < len(BACKENDS):
            backend = BACKENDS[current_index]
            current_index = (current_index + 1) % len(BACKENDS)
            attempts += 1

            if not backend_status[backend]["healthy"]:
                continue

            try:
                logging.info(f"[Router] Forwarding request to {backend}")
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
                logging.error(f"[ERROR] {backend} failed ({backend_status[backend]['failures']}): {e}")
                if backend_status[backend]["failures"] >= FAILURE_THRESHOLD:
                    backend_status[backend]["healthy"] = False
                    logging.warning(f"[HEALTH] Marking {backend} as UNHEALTHY")

        self.send_response(502)
        self.end_headers()
        self.wfile.write(b'{"error":"All backends failed"}')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"router ok"}')
        logging.info("[Router] Health check endpoint called")


def run(port=8000):
    threading.Thread(target=health_check, daemon=True).start()
    server = HTTPServer(("0.0.0.0", port), RoundRobinHandler)
    logging.info(f"Router running on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    run(8000)
