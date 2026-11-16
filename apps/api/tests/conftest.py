"""pytest 共享 fixture：SQLite 内存库、FakeRedis、依赖覆盖。"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


class FakeRedis:
    """内存版 Redis，用于登录失败锁定计数（测试不依赖真实 Redis）。"""

    def __init__(self) -> None:
        self._store: dict[str, int] = {}

    def get(self, key: str) -> int | None:
        return self._store.get(key)

    def incr(self, key: str) -> int:
        self._store[key] = self._store.get(key, 0) + 1
        return self._store[key]

    def expire(self, key: str, seconds: int) -> None:
        # 测试不关心过期时间
        return None

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """SQLite 内存库，每个测试独立建表/拆表。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    """TestClient，覆盖 get_db 依赖并用 FakeRedis 替换真实 Redis。"""

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("app.services.auth_service.get_redis", lambda: FakeRedis())

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
