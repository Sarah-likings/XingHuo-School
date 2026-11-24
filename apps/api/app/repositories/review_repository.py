"""评价数据访问。"""

from sqlalchemy.orm import Session

from app.models.review import Review
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Review)
