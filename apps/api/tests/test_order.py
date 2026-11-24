"""订单接口测试：选定冻结、交付、验收。"""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.fund_flow import FundFlow
from app.models.order import Order
from app.models.task import Task
from app.models.user import User
from app.models.wallet import Wallet


def _create_user(db_session: Session, account: str, balance: str = "100.00") -> User:
    user = User(
        account=account,
        nickname="张三",
        password_hash=hash_password("abc12345"),
        role="student",
        verified=True,
        credit_score=60,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(
        Wallet(
            user_id=user.id,
            available=Decimal(balance),
            frozen=Decimal("0.00"),
            total_income=Decimal("0.00"),
        )
    )
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client: TestClient, account: str) -> dict[str, str]:
    resp = client.post("/api/auth/login", json={"account": account, "password": "abc12345"})
    return dict(resp.cookies)


def _create_task(db_session: Session, publisher_id: int, reward: str = "20.00") -> Task:
    task = Task(
        publisher_id=publisher_id,
        category="EXPRESS",
        title="帮忙取快递",
        description="帮我在学校快递点取一个快递，谢谢",
        reward=Decimal(reward),
        place="东门快递点",
        status="OPEN",
        apply_count=0,
        ai_draft=False,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


def _create_apply(db_session: Session, task_id: int, employer_id: int, taker_id: int) -> Order:
    order = Order(task_id=task_id, employer_id=employer_id, taker_id=taker_id, status="OPEN")
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


def _get_wallet(db_session: Session, user_id: int) -> Wallet | None:
    return db_session.scalar(select(Wallet).where(Wallet.user_id == user_id))


def test_assign_success(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000", balance="100.00")
    taker = _create_user(db_session, "13900139000", balance="0.00")
    task = _create_task(db_session, employer.id)
    apply = _create_apply(db_session, task.id, employer.id, taker.id)

    cookies = _login(client, "13800138000")
    resp = client.post(f"/api/orders/{apply.id}/assign", cookies=cookies)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ASSIGNED"

    # 雇主钱包：available 100→80，frozen 0→20
    wallet = _get_wallet(db_session, employer.id)
    assert wallet is not None
    assert wallet.available == Decimal("80.00")
    assert wallet.frozen == Decimal("20.00")


def test_assign_insufficient_balance(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000", balance="10.00")
    taker = _create_user(db_session, "13900139000")
    task = _create_task(db_session, employer.id)
    apply = _create_apply(db_session, task.id, employer.id, taker.id)

    cookies = _login(client, "13800138000")
    resp = client.post(f"/api/orders/{apply.id}/assign", cookies=cookies)
    assert resp.status_code == 402
    assert resp.json()["code"] == "INSUFFICIENT_BALANCE"


def test_assign_not_employer(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000")
    taker = _create_user(db_session, "13900139000")
    _create_user(db_session, "13700137000")
    task = _create_task(db_session, employer.id)
    apply = _create_apply(db_session, task.id, employer.id, taker.id)

    cookies = _login(client, "13700137000")
    resp = client.post(f"/api/orders/{apply.id}/assign", cookies=cookies)
    assert resp.status_code == 403


def test_deliver_success(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000")
    taker = _create_user(db_session, "13900139000")
    task = _create_task(db_session, employer.id)
    apply = _create_apply(db_session, task.id, employer.id, taker.id)

    employer_cookies = _login(client, "13800138000")
    client.post(f"/api/orders/{apply.id}/assign", cookies=employer_cookies)

    taker_cookies = _login(client, "13900139000")
    resp = client.post(f"/api/orders/{apply.id}/deliver", cookies=taker_cookies)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "DELIVERED"


def test_deliver_not_taker(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000")
    taker = _create_user(db_session, "13900139000")
    task = _create_task(db_session, employer.id)
    apply = _create_apply(db_session, task.id, employer.id, taker.id)

    employer_cookies = _login(client, "13800138000")
    client.post(f"/api/orders/{apply.id}/assign", cookies=employer_cookies)

    resp = client.post(f"/api/orders/{apply.id}/deliver", cookies=employer_cookies)
    assert resp.status_code == 403


def test_accept_success(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000", balance="100.00")
    taker = _create_user(db_session, "13900139000", balance="0.00")
    task = _create_task(db_session, employer.id)
    apply = _create_apply(db_session, task.id, employer.id, taker.id)

    employer_cookies = _login(client, "13800138000")
    client.post(f"/api/orders/{apply.id}/assign", cookies=employer_cookies)
    taker_cookies = _login(client, "13900139000")
    client.post(f"/api/orders/{apply.id}/deliver", cookies=taker_cookies)

    resp = client.post(f"/api/orders/{apply.id}/accept", cookies=employer_cookies)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "COMPLETED"

    # 资金：雇主 frozen 归零，接单者 available 入账 20
    employer_wallet = _get_wallet(db_session, employer.id)
    taker_wallet = _get_wallet(db_session, taker.id)
    assert employer_wallet is not None
    assert taker_wallet is not None
    assert employer_wallet.frozen == Decimal("0.00")
    assert taker_wallet.available == Decimal("20.00")
    assert taker_wallet.total_income == Decimal("20.00")

    # SETTLE 流水已写
    settle = db_session.scalar(
        select(FundFlow).where(FundFlow.order_id == apply.id, FundFlow.type == "SETTLE")
    )
    assert settle is not None


def test_accept_not_employer(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000")
    taker = _create_user(db_session, "13900139000")
    task = _create_task(db_session, employer.id)
    apply = _create_apply(db_session, task.id, employer.id, taker.id)

    employer_cookies = _login(client, "13800138000")
    client.post(f"/api/orders/{apply.id}/assign", cookies=employer_cookies)
    taker_cookies = _login(client, "13900139000")
    client.post(f"/api/orders/{apply.id}/deliver", cookies=taker_cookies)

    resp = client.post(f"/api/orders/{apply.id}/accept", cookies=taker_cookies)
    assert resp.status_code == 403


def _create_admin(db_session: Session, account: str = "admin001") -> User:
    admin = User(
        account=account,
        nickname="管理员",
        password_hash=hash_password("admin12345"),
        role="admin",
        verified=True,
        credit_score=60,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


def test_appeal_success(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000")
    taker = _create_user(db_session, "13900139000")
    task = _create_task(db_session, employer.id)
    apply = _create_apply(db_session, task.id, employer.id, taker.id)

    employer_cookies = _login(client, "13800138000")
    client.post(f"/api/orders/{apply.id}/assign", cookies=employer_cookies)

    taker_cookies = _login(client, "13900139000")
    resp = client.post(
        f"/api/orders/{apply.id}/appeal", json={"reason": "雇主不验收"}, cookies=taker_cookies
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "APPEALING"


def test_appeal_not_party(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000")
    taker = _create_user(db_session, "13900139000")
    _create_user(db_session, "13700137000")
    task = _create_task(db_session, employer.id)
    apply = _create_apply(db_session, task.id, employer.id, taker.id)

    employer_cookies = _login(client, "13800138000")
    client.post(f"/api/orders/{apply.id}/assign", cookies=employer_cookies)

    other_cookies = _login(client, "13700137000")
    resp = client.post(
        f"/api/orders/{apply.id}/appeal", json={"reason": "申诉"}, cookies=other_cookies
    )
    assert resp.status_code == 403


def test_arbitrate_refund(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000", balance="100.00")
    taker = _create_user(db_session, "13900139000", balance="0.00")
    _create_admin(db_session)
    task = _create_task(db_session, employer.id)
    apply = _create_apply(db_session, task.id, employer.id, taker.id)

    employer_cookies = _login(client, "13800138000")
    client.post(f"/api/orders/{apply.id}/assign", cookies=employer_cookies)
    taker_cookies = _login(client, "13900139000")
    client.post(f"/api/orders/{apply.id}/appeal", json={"reason": "申诉"}, cookies=taker_cookies)

    admin_cookies = dict(
        client.post(
            "/api/auth/login", json={"account": "admin001", "password": "admin12345"}
        ).cookies
    )

    resp = client.post(
        f"/api/admin/orders/{apply.id}/arbitrate",
        json={"decision": "REFUND", "remark": "裁定退款"},
        cookies=admin_cookies,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "REFUNDED"

    # 冻结退回雇主
    employer_wallet = _get_wallet(db_session, employer.id)
    assert employer_wallet is not None
    assert employer_wallet.frozen == Decimal("0.00")
    assert employer_wallet.available == Decimal("100.00")


def test_arbitrate_not_admin(client: TestClient, db_session: Session) -> None:
    employer = _create_user(db_session, "13800138000")
    taker = _create_user(db_session, "13900139000")
    task = _create_task(db_session, employer.id)
    apply = _create_apply(db_session, task.id, employer.id, taker.id)

    employer_cookies = _login(client, "13800138000")
    client.post(f"/api/orders/{apply.id}/assign", cookies=employer_cookies)
    taker_cookies = _login(client, "13900139000")
    client.post(f"/api/orders/{apply.id}/appeal", json={"reason": "申诉"}, cookies=taker_cookies)

    resp = client.post(
        f"/api/admin/orders/{apply.id}/arbitrate",
        json={"decision": "REFUND"},
        cookies=employer_cookies,
    )
    assert resp.status_code == 403


def test_check_overdue(client: TestClient, db_session: Session) -> None:
    from datetime import UTC, datetime, timedelta

    employer = _create_user(db_session, "13800138000", balance="100.00")
    taker = _create_user(db_session, "13900139000", balance="0.00")
    _create_admin(db_session)
    task = _create_task(db_session, employer.id)

    # 直接构造超时 DELIVERED 订单（delivered_at 超 48h）
    overdue = Order(
        task_id=task.id,
        employer_id=employer.id,
        taker_id=taker.id,
        status="DELIVERED",
        reward=Decimal("20.00"),
        delivered_at=datetime.now(UTC) - timedelta(hours=49),
    )
    db_session.add(overdue)
    # 冻结资金（模拟已选定冻结）
    wallet = _get_wallet(db_session, employer.id)
    assert wallet is not None
    wallet.available -= Decimal("20.00")
    wallet.frozen += Decimal("20.00")
    db_session.commit()
    db_session.refresh(overdue)

    admin_cookies = dict(
        client.post(
            "/api/auth/login", json={"account": "admin001", "password": "admin12345"}
        ).cookies
    )
    resp = client.post("/api/admin/orders/check-overdue", cookies=admin_cookies)
    assert resp.status_code == 200
    assert resp.json()["data"]["processed"] == 1

    # 订单已自动完成
    db_session.refresh(overdue)
    assert overdue.status == "COMPLETED"
    taker_wallet = _get_wallet(db_session, taker.id)
    assert taker_wallet is not None
    assert taker_wallet.available == Decimal("20.00")
