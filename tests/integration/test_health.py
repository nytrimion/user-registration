from datetime import datetime

from fastapi.testclient import TestClient


def test_health_endpoint_returns_200(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200


def test_health_endpoint_has_status_ok(client: TestClient) -> None:
    response = client.get("/health")
    data = response.json()

    assert "status" in data
    assert data["status"] == "ok"


def test_health_endpoint_has_valid_iso_timestamp(client: TestClient) -> None:
    response = client.get("/health")
    data = response.json()

    assert "timestamp" in data
    timestamp = datetime.fromisoformat(data["timestamp"])
    assert isinstance(timestamp, datetime)
