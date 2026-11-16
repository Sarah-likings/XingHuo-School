"""后台管理路由：学生证认证审核。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.response import success
from app.models.user import User
from app.schemas.verify import VerifyOut, VerifyReviewRequest
from app.services.verify_service import VerifyService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/verify/{verify_id}", summary="审核学生证认证")
def review_verify(
    verify_id: int,
    data: VerifyReviewRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    record = VerifyService(db).review(admin, verify_id, data.approve, data.reject_reason)
    return success(data=VerifyOut.model_validate(record).model_dump())
