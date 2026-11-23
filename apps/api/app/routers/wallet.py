"""钱包路由：余额查询。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models.user import User
from app.schemas.wallet import WalletOut
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("", summary="我的钱包")
def get_wallet(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    wallet = WalletService(db).summary(user.id)
    return success(data=WalletOut.model_validate(wallet).model_dump())
