"""枚举单一来源。

订单状态、任务分类、错误码等枚举**只在本文件定义一处**，前后端都从它派生，
禁止在业务代码里写字符串字面量。前端对应 `apps/web/lib/constants.ts`（由后端导出/生成）。
取值与《数据库设计说明书》4.1.14 节枚举字典一致。
"""

from enum import StrEnum


class Role(StrEnum):
    """用户角色。管理员不可参与交易。"""

    STUDENT = "student"
    ADMIN = "admin"


class OrderStatus(StrEnum):
    """订单状态机 7 个状态（唯一入口 services/order_service.transition）。"""

    OPEN = "OPEN"  # 待接单（申请中）
    ASSIGNED = "ASSIGNED"  # 已选定接单人（资金冻结）
    DELIVERED = "DELIVERED"  # 已交付（等待验收）
    COMPLETED = "COMPLETED"  # 已完成（已结算）
    APPEALING = "APPEALING"  # 申诉中（仲裁）
    CANCELLED = "CANCELLED"  # 已取消
    REFUNDED = "REFUNDED"  # 已退款


class TaskStatus(StrEnum):
    """任务层面的粗状态（区别于订单状态机）。"""

    OPEN = "OPEN"  # 待接单（申请中，大厅可见）
    ASSIGNED = "ASSIGNED"  # 已选定接单人
    CANCELLED = "CANCELLED"  # 已取消


class TaskCategory(StrEnum):
    """任务分类（6 类）。"""

    EXPRESS = "EXPRESS"  # 快递代拿
    TUTOR = "TUTOR"  # 课程辅导
    REPAIR = "REPAIR"  # 电脑维修
    PRINT = "PRINT"  # 资料打印
    ERRAND = "ERRAND"  # 跑腿
    OTHER = "OTHER"  # 其他


class VerifyStatus(StrEnum):
    """学生证实名认证状态。"""

    PENDING = "PENDING"  # 待审核
    APPROVED = "APPROVED"  # 已通过
    REJECTED = "REJECTED"  # 已驳回


class FundFlowType(StrEnum):
    """资金流水类型（fund_flow 只增不改）。"""

    RECHARGE = "RECHARGE"  # 充值（管理员入账）
    FREEZE = "FREEZE"  # 担保冻结
    SETTLE = "SETTLE"  # 验收打款
    REFUND = "REFUND"  # 退款
    CLEAR = "CLEAR"  # 清算


class MessageType(StrEnum):
    """私聊消息类型。"""

    TEXT = "TEXT"
    IMAGE = "IMAGE"


class ReportStatus(StrEnum):
    """举报 / 申诉处理状态。"""

    PENDING = "PENDING"  # 待处理
    DECIDED = "DECIDED"  # 已裁决
    REJECTED = "REJECTED"  # 已驳回


class PostAuditStatus(StrEnum):
    """生活帖内容审核状态。"""

    PENDING = "PENDING"  # 待审核
    APPROVED = "APPROVED"  # 已通过
    REJECTED = "REJECTED"  # 已驳回


class ErrorCode(StrEnum):
    """业务错误码（与《技术要求》2.3 错误码表对齐）。"""

    OK = "OK"
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    FORBIDDEN = "FORBIDDEN"
    NOT_VERIFIED = "NOT_VERIFIED"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    TASK_TAKEN = "TASK_TAKEN"
    DUPLICATE = "DUPLICATE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
