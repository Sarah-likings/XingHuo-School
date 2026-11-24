"""评价路由：提交评价。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_verified
from app.core.response import success
from app.models.user import User
from app.schemas.review import ReviewCreateRequest, ReviewOut
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", status_code=201, summary="提交评价")
def create_review(
    data: ReviewCreateRequest,
    user: User = Depends(require_verified),
    db: Session = Depends(get_db),
) -> dict:
    review = ReviewService(db).submit(user, data.order_id, data.score, data.comment)
    return success(data=ReviewOut.model_validate(review).model_dump())
