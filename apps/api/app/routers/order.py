"""订单路由：选定冻结、交付、验收。"""

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_verified
from app.core.response import success
from app.models.user import User
from app.schemas.order import AppealRequest, OrderOut
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/{order_id}/assign", summary="选定接单人并冻结资金")
def assign_order(
    order_id: int,
    user: User = Depends(require_verified),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    order = OrderService(db).assign(user, order_id, idempotency_key)
    return success(data=OrderOut.model_validate(order).model_dump())


@router.post("/{order_id}/deliver", summary="交付")
def deliver_order(
    order_id: int,
    user: User = Depends(require_verified),
    db: Session = Depends(get_db),
) -> dict:
    order = OrderService(db).deliver(user, order_id)
    return success(data=OrderOut.model_validate(order).model_dump())


@router.post("/{order_id}/accept", summary="验收通过并结算")
def accept_order(
    order_id: int,
    user: User = Depends(require_verified),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    order = OrderService(db).accept(user, order_id, idempotency_key)
    return success(data=OrderOut.model_validate(order).model_dump())


@router.post("/{order_id}/appeal", summary="发起申诉")
def appeal_order(
    order_id: int,
    data: AppealRequest,
    user: User = Depends(require_verified),
    db: Session = Depends(get_db),
) -> dict:
    order = OrderService(db).appeal(user, order_id, data.reason)
    return success(data=OrderOut.model_validate(order).model_dump())
