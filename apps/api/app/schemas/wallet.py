"""钱包出入参 schema。"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class WalletOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    available: Decimal
    frozen: Decimal
    total_income: Decimal
