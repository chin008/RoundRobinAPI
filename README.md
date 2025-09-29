A simple Round Robin Load Balancer built in Python to distribute traffic across multiple backend services.
The project includes:

Router: Forwards requests in round-robin order, with failure and health-check logic.

Backend: Lightweight echo APIs that respond with payload + their port.

Tests: Pytest suite to validate distribution, failure handling, and recovery.

                  ┌─────────────┐
                  │   Client    │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │   Router    │
                  │ Round Robin │
                  │ + HealthChk │
                  └───┬───┬───┬─┘
                      │   │   │
        ┌─────────────┘   │   └─────────────┐
        ▼                 ▼                 ▼
   Backend1 (5001)   Backend2 (5002)   Backend3 (5003)

   


The Round Robin API consists of:
- **Router (port 8000)**: Forwards requests in round robin order and monitors backend health.
- **Backends (ports 5001–5003)**: Echo APIs that return the payload + their port.
- **Health Checker**: Marks failed backends unhealthy and recovers them automatically.

Router: Exposes :8000 and forwards requests.

Backends: Run on ports 5001, 5002, 5003.

Health Check Thread: Monitors unhealthy backends and recovers them automatically.

Test Scenarios

Normal Round Robin
Requests rotate between 5001 → 5002 → 5003


Start Services
docker-compose up --build


Expected Results:

backend1  | Backend running on port 5001
backend2  | Backend running on port 5002
backend3  | Backend running on port 5003
router    | Router running on port 8000

Test Locally

Send 3 requests:
curl -X POST http://localhost:8000 -H "Content-Type: application/json" -d '{"msg":"demo"}'

Expected responses (round robin):

{"msg":"demo","handled_by":5001}
{"msg":"demo","handled_by":5002}
{"msg":"demo","handled_by":5003}

Expose with ngrok

ngrok http 8000


Output:

Forwarding    https://palmira-balneological-loni.ngrok-free.dev -> http://localhost:8000


Test external access:

curl -X POST https://palmira-balneological-loni.ngrok-free.dev \
     -H "Content-Type: application/json" \
     -d '{"msg":"public demo"}'


Response rotates like local test.

Simulate Backend Failure
Stop backend2:
docker stop backend2


Router logs:

[ERROR] http://backend2:5002 failed (3 times)
[HEALTH] Marking http://backend2:5002 as UNHEALTHY


Send request:

curl -X POST http://localhost:8000 -H "Content-Type: application/json" -d '{"msg":"after failure"}'


✅ Response rotates only between backend1 & backend3.

🔹 5. Simulate Backend Slowness

Edit backend3 app_api.py:

if self.server.server_port == 5003:
    import time; time.sleep(10)


Rebuild:

docker-compose up --build


Router times out after 3s, skips backend3.
Requests rotate between backend1 & backend2.

Automated Tests
pytest -v tests/


Expected output:

test_router_health PASSED
test_round_robin_distribution PASSED
test_backend_failure PASSED
test_backend_slow PASSED
