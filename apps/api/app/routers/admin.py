"""后台管理路由：学生证认证审核。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.response import success
from app.models.user import User
from app.schemas.order import ArbitrateRequest, OrderOut
from app.schemas.verify import VerifyOut, VerifyReviewRequest
from app.services.order_service import OrderService
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


@router.post("/orders/{order_id}/arbitrate", summary="裁决申诉（退款/结算）")
def arbitrate_order(
    order_id: int,
    data: ArbitrateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    order = OrderService(db).arbitrate(admin, order_id, data.decision, data.remark)
    return success(data=OrderOut.model_validate(order).model_dump())


@router.post("/orders/check-overdue", summary="超时兜底（手动触发）")
def check_overdue(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    count = OrderService(db).check_overdue()
    return success(data={"processed": count})
