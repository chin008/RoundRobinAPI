import requests
import subprocess
import time
import pytest

ROUTER_URL = "http://localhost:8000"


@pytest.fixture(autouse=True)
def ensure_all_backends():
    """Ensure all backends are running before each test."""
    subprocess.run(["docker", "start", "backend1", "backend2", "backend3"])
    time.sleep(2)  # give them time to start
    yield
    # cleanup: start again (in case tests stopped them)
    subprocess.run(["docker", "start", "backend1", "backend2", "backend3"])
    time.sleep(2)


def test_router_health():
    """Router should respond healthy."""
    resp = requests.get(f"{ROUTER_URL}/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "router ok"


def test_round_robin_distribution():
    """Router should distribute requests across all 3 backends."""
    seen = set()
    for _ in range(6):
        resp = requests.post(ROUTER_URL, json={"msg": "test"})
        assert resp.status_code == 200
        seen.add(resp.json()["handled_by"])
    assert len(seen) == 3  # all 3 backends should be hit


def test_backend_failure():
    """Router should skip a failed backend."""
    # Stop backend2
    subprocess.run(["docker", "stop", "backend2"])
    time.sleep(3)  # let router detect failure

    seen = set()
    for _ in range(6):
        resp = requests.post(ROUTER_URL, json={"msg": "failure simulation"})
        assert resp.status_code == 200
        seen.add(resp.json()["handled_by"])

    assert 5002 not in seen  # backend2 should not handle requests

    # Restart backend2
    subprocess.run(["docker", "start", "backend2"])
    time.sleep(5)  # allow health-check to mark it healthy again


def test_backend_recovery():
    """Router should recover a backend after it comes back online."""
    # Stop backend3
    subprocess.run(["docker", "stop", "backend3"])
    time.sleep(3)

    # Restart backend3
    subprocess.run(["docker", "start", "backend3"])
    time.sleep(6)  # allow router health check to recover it

    seen = set()
    for _ in range(9):
        resp = requests.post(ROUTER_URL, json={"msg": "recovery test"})
        assert resp.status_code == 200
        seen.add(resp.json()["handled_by"])

    assert 5003 in seen  # backend3 should be back in rotation


def test_all_backends_down():
    """If all backends are down, router should return 502."""
    subprocess.run(["docker", "stop", "backend1"])
    subprocess.run(["docker", "stop", "backend2"])
    subprocess.run(["docker", "stop", "backend3"])
    time.sleep(3)

    resp = requests.post(ROUTER_URL, json={"msg": "no backends"})
    assert resp.status_code == 502
    assert "All backends failed" in resp.text

    # restart all
    subprocess.run(["docker", "start", "backend1", "backend2", "backend3"])
    time.sleep(5)


def test_backend_slow(monkeypatch):
    """Simulate a slow backend and ensure router skips it."""
    # Stop backend1 temporarily and replace with a dummy slow response
    subprocess.run(["docker", "stop", "backend1"])
    time.sleep(2)

    seen = set()
    for _ in range(5):
        resp = requests.post(ROUTER_URL, json={"msg": "slow test"})
        assert resp.status_code == 200
        seen.add(resp.json()["handled_by"])

    assert 5001 not in seen  # router should skip backend1 if it’s unresponsive

    # Restart backend1
    subprocess.run(["docker", "start", "backend1"])
    time.sleep(5)
