"""认证接口测试：注册、登录。"""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.wallet import Wallet


def _register(
    client: TestClient, student_no: str = "20230001", name: str = "张三", password: str = "abc12345"
):
    return client.post(
        "/api/auth/register",
        json={"student_no": student_no, "name": name, "password": password},
    )


def test_register_success(client: TestClient, db_session: Session) -> None:
    resp = _register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "OK"
    assert body["data"]["student_no"] == "20230001"
    assert body["data"]["verified"] is False
    # 注册自动创建钱包（一生一账户）
    wallet = db_session.scalar(select(Wallet).where(Wallet.user_id == body["data"]["id"]))
    assert wallet is not None


def test_register_duplicate(client: TestClient) -> None:
    _register(client)
    resp = _register(client)
    assert resp.status_code == 409
    assert resp.json()["code"] == "DUPLICATE"


def test_register_weak_password(client: TestClient) -> None:
    # 纯数字，缺少字母
    resp = _register(client, password="12345678")
    assert resp.status_code == 422


def test_register_invalid_student_no(client: TestClient) -> None:
    # 学号含字母，不匹配学号段正则
    resp = _register(client, student_no="abc")
    assert resp.status_code == 422


def test_login_success(client: TestClient) -> None:
    _register(client)
    resp = client.post("/api/auth/login", json={"student_no": "20230001", "password": "abc12345"})
    assert resp.status_code == 200
    assert resp.json()["code"] == "OK"
    assert resp.cookies.get("access_token") is not None


def test_login_wrong_password(client: TestClient) -> None:
    _register(client)
    resp = client.post("/api/auth/login", json={"student_no": "20230001", "password": "wrongpass1"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "UNAUTHORIZED"


def test_login_user_not_found(client: TestClient) -> None:
    resp = client.post("/api/auth/login", json={"student_no": "99999999", "password": "abc12345"})
    assert resp.status_code == 401
