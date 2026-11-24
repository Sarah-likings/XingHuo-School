"""订单状态机：迁移表（单一来源）。

订单状态只能通过 services/order_service.py 的 `transition()` 迁移，
任何位置禁止直接 `UPDATE "order" SET status`。迁移边与《详细设计》P0403 一致。
"""

ALLOWED: dict[str, set[str]] = {
    "OPEN": {"ASSIGNED", "CANCELLED"},
    "ASSIGNED": {"DELIVERED", "OPEN", "APPEALING"},
    "DELIVERED": {"COMPLETED", "APPEALING"},
    "APPEALING": {"COMPLETED", "REFUNDED"},
    "CANCELLED": {"REFUNDED"},
    "COMPLETED": set(),
    "REFUNDED": set(),
}


def can_transition(frm: str, to: str) -> bool:
    """判断从 frm 迁移到 to 是否合法。"""
    return to in ALLOWED.get(frm, set())
