"""认证接口测试：注册、登录。"""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.wallet import Wallet


def _register(
    client: TestClient,
    account: str = "13800138000",
    password: str = "abc12345",
    nickname: str = "张三",
):
    return client.post(
        "/api/auth/register",
        json={"account": account, "password": password, "nickname": nickname},
    )


def test_register_success(client: TestClient, db_session: Session) -> None:
    resp = _register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "OK"
    assert body["data"]["account"] == "13800138000"
    assert body["data"]["nickname"] == "张三"
    assert body["data"]["verified"] is False
    assert body["data"]["credit_score"] == 60
    assert body["data"]["student_no"] is None
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


def test_register_invalid_account(client: TestClient) -> None:
    # 非手机号也非邮箱
    resp = _register(client, account="abc")
    assert resp.status_code == 422


def test_register_invalid_nickname(client: TestClient) -> None:
    # 昵称长度不足 2 字
    resp = _register(client, nickname="a")
    assert resp.status_code == 422


def test_login_success(client: TestClient) -> None:
    _register(client)
    resp = client.post("/api/auth/login", json={"account": "13800138000", "password": "abc12345"})
    assert resp.status_code == 200
    assert resp.json()["code"] == "OK"
    assert resp.cookies.get("access_token") is not None


def test_login_with_email(client: TestClient) -> None:
    _register(client, account="a@b.edu.cn")
    resp = client.post("/api/auth/login", json={"account": "a@b.edu.cn", "password": "abc12345"})
    assert resp.status_code == 200


def test_login_wrong_password(client: TestClient) -> None:
    _register(client)
    resp = client.post("/api/auth/login", json={"account": "13800138000", "password": "wrongpass1"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "UNAUTHORIZED"


def test_login_user_not_found(client: TestClient) -> None:
    resp = client.post("/api/auth/login", json={"account": "13900139000", "password": "abc12345"})
    assert resp.status_code == 401
