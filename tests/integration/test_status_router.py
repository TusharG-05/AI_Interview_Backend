
from fastapi.testclient import TestClient

def test_status_endpoint(client: TestClient):
    response = client.get("/api/status/")
    assert response.status_code == 200
    assert response.json() == {"status": "online", "mode": "API-Only"}
