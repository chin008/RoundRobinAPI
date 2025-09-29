from http.server import BaseHTTPRequestHandler, HTTPServer
import json, sys, logging, os


os.makedirs("/logs", exist_ok=True)  
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/logs/backend.log"),  
        logging.StreamHandler()                   
    ]
)

class EchoHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data)
            data["handled_by"] = self.server.server_port

            
            logging.info(f"[Backend {self.server.server_port}] Received: {data}")

            response = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        except json.JSONDecodeError:
            logging.error(f"[Backend {self.server.server_port}] Invalid JSON received")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error":"Invalid JSON"}')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')
        logging.info(f"[Backend {self.server.server_port}] Health check received")

def run(port):
    server = HTTPServer(("0.0.0.0", port), EchoHandler)
    logging.info(f"Backend running on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    run(port)
