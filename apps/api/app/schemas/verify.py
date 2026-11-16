"""实名认证出入参 schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VerifyUploadRequest(BaseModel):
    """学生证上传表单字段（文件经 UploadFile 单独接收）。"""

    student_no: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=64)
    college: str | None = Field(default=None, max_length=64)
    major: str | None = Field(default=None, max_length=64)
    grade: str | None = Field(default=None, max_length=16)


class VerifyReviewRequest(BaseModel):
    """管理员审核入参：通过 / 驳回。"""

    approve: bool
    reject_reason: str | None = Field(default=None, max_length=255)


class VerifyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    student_no: str
    name: str
    college: str | None
    major: str | None
    grade: str | None
    reject_reason: str | None
    reviewed_by: int | None
    reviewed_at: datetime | None
