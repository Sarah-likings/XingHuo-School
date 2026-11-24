"""评价接口测试。"""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.order import Order
from app.models.task import Task
from app.models.user import User
from app.models.wallet import Wallet


def _create_user(db_session: Session, account: str, credit: int = 60) -> User:
    user = User(
        account=account,
        nickname="张三",
        password_hash=hash_password("abc12345"),
        role="student",
        verified=True,
        credit_score=credit,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(Wallet(user_id=user.id, available=Decimal("0.00"), frozen=Decimal("0.00")))
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client: TestClient, account: str) -> dict[str, str]:
    resp = client.post("/api/auth/login", json={"account": account, "password": "abc12345"})
    return dict(resp.cookies)


def _create_completed_order(db_session: Session, employer_id: int, taker_id: int) -> Order:
    task = Task(
        publisher_id=employer_id,
        category="EXPRESS",
        title="帮忙取快递",
        description="帮我在学校快递点取一个快递，谢谢",
        reward=Decimal("20.00"),
        place="东门快递点",
        status="ASSIGNED",
        apply_count=1,
        ai_draft=False,
    )
    db_session.add(task)
    db_session.flush()
    order = Order(
        task_id=task.id,
        employer_id=employer_id,
        taker_id=taker_id,
        status="COMPLETED",
        reward=Decimal("20.00"),
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


def _get_user(db_session: Session, user_id: int) -> User | None:
    return db_session.get(User, user_id)


def test_review_success(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000")
    taker = _create_user(db_session, "13900139000")
    order = _create_completed_order(db_session, employer.id, taker.id)

    # 雇主好评接单者
    cookies = _login(client, "13800138000")
    resp = client.post(
        "/api/reviews",
        json={"order_id": order.id, "score": 5, "comment": "很靠谱"},
        cookies=cookies,
    )
    assert resp.status_code == 201

    # 接单者信用分 60 → 63
    taker_after = _get_user(db_session, taker.id)
    assert taker_after is not None
    assert taker_after.credit_score == 63

    # 接单者回评雇主
    taker_cookies = _login(client, "13900139000")
    resp = client.post(
        "/api/reviews",
        json={"order_id": order.id, "score": 4, "comment": "讲信用"},
        cookies=taker_cookies,
    )
    assert resp.status_code == 201
    employer_after = _get_user(db_session, employer.id)
    assert employer_after is not None
    assert employer_after.credit_score == 63


def test_review_duplicate(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000")
    taker = _create_user(db_session, "13900139000")
    order = _create_completed_order(db_session, employer.id, taker.id)

    cookies = _login(client, "13800138000")
    client.post("/api/reviews", json={"order_id": order.id, "score": 5}, cookies=cookies)
    resp = client.post("/api/reviews", json={"order_id": order.id, "score": 3}, cookies=cookies)
    assert resp.status_code == 409
    assert resp.json()["code"] == "DUPLICATE"


def test_review_not_party(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000")
    taker = _create_user(db_session, "13900139000")
    _create_user(db_session, "13700137000")
    order = _create_completed_order(db_session, employer.id, taker.id)

    cookies = _login(client, "13700137000")
    resp = client.post("/api/reviews", json={"order_id": order.id, "score": 5}, cookies=cookies)
    assert resp.status_code == 403


def test_review_not_completed(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000")
    taker = _create_user(db_session, "13900139000")
    order = _create_completed_order(db_session, employer.id, taker.id)
    # 改为未完成状态
    order.status = "DELIVERED"
    db_session.commit()

    cookies = _login(client, "13800138000")
    resp = client.post("/api/reviews", json={"order_id": order.id, "score": 5}, cookies=cookies)
    assert resp.status_code == 409


def test_review_credit_clamp(client: TestClient, db_session: Session) -> None:
    # 接单者信用分 99，好评 +3 后钳制到 100
    employer = _create_user(db_session, "13800138000")
    taker = _create_user(db_session, "13900139000", credit=99)
    order = _create_completed_order(db_session, employer.id, taker.id)

    cookies = _login(client, "13800138000")
    resp = client.post("/api/reviews", json={"order_id": order.id, "score": 5}, cookies=cookies)
    assert resp.status_code == 201

    taker_after = _get_user(db_session, taker.id)
    assert taker_after is not None
    assert taker_after.credit_score == 100
