"""任务接口测试：发布、大厅列表、详情、申请接单。"""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


def _create_user(db_session: Session, account: str, verified: bool = True) -> User:
    user = User(
        account=account,
        nickname="张三",
        password_hash=hash_password("abc12345"),
        role="student",
        verified=verified,
        credit_score=60,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client: TestClient, account: str) -> dict[str, str]:
    resp = client.post("/api/auth/login", json={"account": account, "password": "abc12345"})
    return dict(resp.cookies)


def _publish(client: TestClient, cookies: dict[str, str], **overrides) -> dict:
    payload = {
        "category": "EXPRESS",
        "title": "帮忙取快递",
        "description": "帮我在学校快递点取一个快递，谢谢",
        "reward": "20.00",
        "place": "东门快递点",
        "deadline": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
    }
    payload.update(overrides)
    return client.post("/api/tasks", json=payload, cookies=cookies).json()


def test_publish_requires_verified(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "13800138000", verified=False)
    cookies = _login(client, "13800138000")
    resp = _publish(client, cookies)
    assert resp["code"] == "NOT_VERIFIED"


def test_publish_success(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "13800138000")
    cookies = _login(client, "13800138000")
    resp = _publish(client, cookies)
    assert resp["code"] == "OK"
    assert resp["data"]["status"] == "OPEN"


def test_publish_invalid_title(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "13800138000")
    cookies = _login(client, "13800138000")
    resp = _publish(client, cookies, title="短")
    assert resp["code"] == "VALIDATION_FAILED"


def test_publish_sensitive_word(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "13800138000")
    cookies = _login(client, "13800138000")
    resp = _publish(client, cookies, description="帮人代考高数，价格面议谢谢")
    assert resp["code"] == "VALIDATION_FAILED"


def test_publish_duplicate(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "13800138000")
    cookies = _login(client, "13800138000")
    _publish(client, cookies)
    resp = _publish(client, cookies)
    assert resp["code"] == "DUPLICATE"


def test_list_tasks(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "13800138000")
    cookies = _login(client, "13800138000")
    _publish(client, cookies)
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["total"] >= 1
    assert len(body["data"]["items"]) >= 1


def test_task_detail(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "13800138000")
    cookies = _login(client, "13800138000")
    task_id = _publish(client, cookies)["data"]["id"]
    resp = client.get(f"/api/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["publisher_nickname"] == "张三"


def test_apply_success(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "13800138000")
    cookies = _login(client, "13800138000")
    task_id = _publish(client, cookies)["data"]["id"]
    _create_user(db_session, "13900139000")
    taker_cookies = _login(client, "13900139000")
    resp = client.post(
        f"/api/tasks/{task_id}/apply", json={"note": "我可以"}, cookies=taker_cookies
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["status"] == "OPEN"


def test_apply_own_task(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "13800138000")
    cookies = _login(client, "13800138000")
    task_id = _publish(client, cookies)["data"]["id"]
    resp = client.post(f"/api/tasks/{task_id}/apply", json={}, cookies=cookies)
    assert resp.status_code == 409


def test_apply_duplicate(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "13800138000")
    cookies = _login(client, "13800138000")
    task_id = _publish(client, cookies)["data"]["id"]
    _create_user(db_session, "13900139000")
    taker_cookies = _login(client, "13900139000")
    client.post(f"/api/tasks/{task_id}/apply", json={}, cookies=taker_cookies)
    resp = client.post(f"/api/tasks/{task_id}/apply", json={}, cookies=taker_cookies)
    assert resp.status_code == 409
    assert resp.json()["code"] == "DUPLICATE"
