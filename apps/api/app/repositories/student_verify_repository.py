"""实名认证数据访问。"""

from sqlalchemy.orm import Session

from app.models.student_verify import StudentVerify
from app.repositories.base import BaseRepository


class StudentVerifyRepository(BaseRepository[StudentVerify]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, StudentVerify)
