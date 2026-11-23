"""实名认证业务：上传学生证与管理员审核。"""

import re
import uuid
from datetime import UTC, datetime
from io import BytesIO

from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import VerifyStatus
from app.core.exceptions import (
    ConflictError,
    DuplicateError,
    NotFoundError,
    ValidationFailedError,
)
from app.core.s3 import get_s3
from app.models.audit_log import AuditLog
from app.models.student_verify import StudentVerify
from app.models.user import User
from app.repositories.student_verify_repository import StudentVerifyRepository

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}


class VerifyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.verify_repo = StudentVerifyRepository(db)

    def submit(
        self,
        user: User,
        student_no: str,
        name: str,
        college: str | None,
        major: str | None,
        grade: str | None,
        file_data: bytes,
        content_type: str,
    ) -> StudentVerify:
        """提交实名认证：学号段初筛 + 图片校验 + 上传 S3 + 建待审记录。"""
        if user.verified:
            raise DuplicateError("已完成实名认证")
        if self.verify_repo.find_one(user_id=user.id):
            raise DuplicateError("已提交认证，请等待审核")
        if not re.fullmatch(settings.student_no_pattern, student_no):
            raise ValidationFailedError("学号格式不正确")
        self._validate_image(file_data, content_type)

        ext = "png" if content_type == "image/png" else "jpg"
        key = f"verify/{user.id}/{uuid.uuid4().hex}.{ext}"
        get_s3().upload_object(key, file_data, content_type)

        record = StudentVerify(
            user_id=user.id,
            status=VerifyStatus.PENDING.value,
            student_no=student_no,
            name=name,
            college=college,
            major=major,
            grade=grade,
            image_key=key,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def review(
        self,
        admin: User,
        verify_id: int,
        approve: bool,
        reject_reason: str | None,
    ) -> StudentVerify:
        """审核认证：通过则置 verified 并同步标签，驳回写原因；写审计日志。"""
        record = self.verify_repo.get(verify_id)
        if record is None or record.deleted_at is not None:
            raise NotFoundError("认证记录不存在")
        if record.status != VerifyStatus.PENDING.value:
            raise ConflictError("该认证已审核")
        user = self.db.get(User, record.user_id)
        if user is None or user.deleted_at is not None:
            raise NotFoundError("用户不存在")

        record.reviewed_by = admin.id
        record.reviewed_at = datetime.now(UTC)
        if approve:
            record.status = VerifyStatus.APPROVED.value
            user.verified = True
            user.student_no = record.student_no
            user.name = record.name
            user.college = record.college
            user.major = record.major
            user.grade = record.grade
        else:
            record.status = VerifyStatus.REJECTED.value
            record.reject_reason = reject_reason

        self.db.add(
            AuditLog(
                actor_id=admin.id,
                action="verify_review",
                target_type="student_verify",
                target_id=record.id,
                detail={"result": "approve"} if approve else {"result": "reject"},
            )
        )
        return record

    @staticmethod
    def _validate_image(data: bytes, content_type: str) -> None:
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationFailedError("仅支持 JPG/PNG 图片")
        if len(data) > MAX_UPLOAD_BYTES:
            raise ValidationFailedError("图片大小不能超过 5MB")
        try:
            image = Image.open(BytesIO(data))
            image.verify()
        except Exception as exc:
            raise ValidationFailedError("图片无法解析") from exc
