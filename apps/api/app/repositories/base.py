"""数据访问层基类：只做增删改查与查询组装，不写业务分支。

具体实体的 repository 继承本类，业务规则一律放 service 层。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base


class BaseRepository[ModelT: Base]:
    def __init__(self, db: Session, model: type[ModelT]) -> None:
        self.db = db
        self.model = model

    def get(self, id_: int) -> ModelT | None:
        return self.db.get(self.model, id_)

    def find_one(self, **filters) -> ModelT | None:
        return self.db.scalar(select(self.model).filter_by(**filters))

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
