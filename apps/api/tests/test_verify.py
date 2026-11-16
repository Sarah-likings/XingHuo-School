"""实名认证接口测试：上传、审核。"""

import io

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


class FakeS3:
    """内存 S3 打桩，避免测试依赖 MinIO。"""

    def __init__(self) -> None:
        self.uploaded_keys: list[str] = []

    def upload_object(self, key: str, data: bytes, content_type: str) -> None:
        self.uploaded_keys.append(key)


def _make_png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), "red").save(buf, format="PNG")
    return buf.getvalue()


def _register_and_login(
    client: TestClient, student_no: str = "20230001", password: str = "abc12345"
) -> dict[str, str]:
    client.post(
        "/api/auth/register",
        json={"student_no": student_no, "name": "张三", "password": password},
    )
    resp = client.post("/api/auth/login", json={"student_no": student_no, "password": password})
    return dict(resp.cookies)


def _upload(client: TestClient, cookies: dict[str, str], student_no: str = "20230001"):
    return client.post(
        "/api/verify/upload",
        data={"student_no": student_no, "name": "张三"},
        files={"file": ("card.png", _make_png(), "image/png")},
        cookies=cookies,
    )


def test_upload_requires_auth(client: TestClient) -> None:
    resp = _upload(client, cookies={})
    assert resp.status_code == 401


def test_upload_invalid_student_no(client: TestClient) -> None:
    cookies = _register_and_login(client)
    resp = _upload(client, cookies, student_no="abc")
    assert resp.status_code == 422


def test_admin_review_forbidden(client: TestClient) -> None:
    cookies = _register_and_login(client)
    resp = client.post("/api/admin/verify/1", json={"approve": True}, cookies=cookies)
    assert resp.status_code == 403


def test_full_verify_flow(client: TestClient, db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr("app.services.verify_service.get_s3", lambda: FakeS3())
    cookies = _register_and_login(client)

    # 上传学生证
    resp = client.post(
        "/api/verify/upload",
        data={
            "student_no": "20230001",
            "name": "张三",
            "college": "计算机学院",
            "major": "软件工程",
            "grade": "2023",
        },
        files={"file": ("card.png", _make_png(), "image/png")},
        cookies=cookies,
    )
    assert resp.status_code == 201
    verify_id = resp.json()["data"]["id"]

    # 创建管理员并登录
    admin = User(
        student_no="admin001",
        name="管理员",
        password_hash=hash_password("admin12345"),
        role="admin",
        verified=True,
        credit_score=100,
    )
    db_session.add(admin)
    db_session.commit()
    admin_login = client.post(
        "/api/auth/login", json={"student_no": "admin001", "password": "admin12345"}
    )
    admin_cookies = dict(admin_login.cookies)

    # 审核通过
    resp = client.post(
        f"/api/admin/verify/{verify_id}", json={"approve": True}, cookies=admin_cookies
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "APPROVED"

    # 用户 verified 置为 True，并同步学院/专业/年级
    user = db_session.scalar(select(User).where(User.student_no == "20230001"))
    assert user is not None
    assert user.verified is True
    assert user.college == "计算机学院"
