"""健康检查接口冒烟测试。"""

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == "OK"
    assert body["msg"] == "成功"
    assert body["data"]["status"] == "ok"


def test_health_has_trace_id_header(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.headers.get("X-Trace-Id")
