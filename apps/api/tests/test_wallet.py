"""钱包接口测试。"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


def _create_user(db_session: Session, account: str) -> None:
    user = User(
        account=account,
        nickname="张三",
        password_hash=hash_password("abc12345"),
        role="student",
        verified=False,
        credit_score=60,
    )
    db_session.add(user)
    db_session.commit()


def _login(client: TestClient, account: str) -> dict[str, str]:
    resp = client.post("/api/auth/login", json={"account": account, "password": "abc12345"})
    return dict(resp.cookies)


def test_wallet_requires_auth(client: TestClient) -> None:
    resp = client.get("/api/wallet")
    assert resp.status_code == 401


def test_wallet_summary(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "13800138000")
    cookies = _login(client, "13800138000")
    resp = client.get("/api/wallet", cookies=cookies)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["available"] == "0.00"
    assert data["frozen"] == "0.00"
    assert data["total_income"] == "0.00"
