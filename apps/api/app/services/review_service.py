"""评价业务：提交评价 + 信用分回流。"""

from sqlalchemy.orm import Session

from app.core.enums import OrderStatus
from app.core.exceptions import ConflictError, DuplicateError, ForbiddenError, NotFoundError
from app.models.order import Order
from app.models.review import Review
from app.models.user import User
from app.repositories.review_repository import ReviewRepository

# 信用分调整：好评 +3，中评 +2，差评 -5（与概设 2.7 Q3 经验值一致）
_SCORE_DELTA = {5: 3, 4: 3, 3: 2, 2: -5, 1: -5}


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.review_repo = ReviewRepository(db)

    def submit(self, user: User, order_id: int, score: int, comment: str | None) -> Review:
        """提交评价：已完成订单双方各评一次，并更新被评价人信用分。"""
        order = self.db.get(Order, order_id)
        if order is None or order.deleted_at is not None:
            raise NotFoundError("订单不存在")
        if order.status != OrderStatus.COMPLETED.value:
            raise ConflictError("订单未完成，暂不可评价")
        if user.id not in (order.employer_id, order.taker_id):
            raise ForbiddenError("仅订单双方可评价")
        to_user = order.taker_id if user.id == order.employer_id else order.employer_id
        if to_user is None:
            raise ConflictError("订单缺少接单者信息")
        if self.review_repo.find_one(order_id=order_id, from_user=user.id):
            raise DuplicateError("已评价过该订单")

        review = Review(
            order_id=order_id,
            from_user=user.id,
            to_user=to_user,
            score=score,
            comment=comment,
            is_late=False,
        )
        self.db.add(review)
        self.db.flush()

        # 更新被评价人信用分（钳制 [0, 100]）
        target = self.db.get(User, to_user)
        if target is not None:
            target.credit_score = max(0, min(100, target.credit_score + _SCORE_DELTA[score]))
        return review
