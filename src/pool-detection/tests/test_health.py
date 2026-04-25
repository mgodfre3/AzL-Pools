"""Pool detection service tests."""

from fastapi.testclient import TestClient


def test_health():
    from service import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "model_loaded" in resp.json()
