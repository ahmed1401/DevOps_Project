from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "request_id" in body


def test_create_and_list_items():
    create = client.post("/items", json={"name": "widget"})
    assert create.status_code == 201
    item = create.json()["item"]
    assert item["id"] == 1
    assert item["name"] == "widget"

    listing = client.get("/items")
    assert listing.status_code == 200
    body = listing.json()
    assert body["count"] >= 1
    assert any(x["name"] == "widget" for x in body["items"])


def test_metrics_endpoint():
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "http_requests_total" in res.text