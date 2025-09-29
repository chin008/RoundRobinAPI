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

   
Router: Exposes :8000 and forwards requests.

Backends: Run on ports 5001, 5002, 5003.

Health Check Thread: Monitors unhealthy backends and recovers them automatically.