"""实名认证路由：上传学生证发起认证。"""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models.user import User
from app.schemas.verify import VerifyOut
from app.services.verify_service import VerifyService

router = APIRouter(prefix="/verify", tags=["verify"])


@router.post("/upload", status_code=201, summary="上传学生证发起认证")
def upload(
    file: UploadFile = File(...),
    student_no: str = Form(...),
    name: str = Form(...),
    college: str | None = Form(None),
    major: str | None = Form(None),
    grade: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    file_data = file.file.read()
    record = VerifyService(db).submit(
        user=user,
        student_no=student_no,
        name=name,
        college=college,
        major=major,
        grade=grade,
        file_data=file_data,
        content_type=file.content_type or "",
    )
    return success(data=VerifyOut.model_validate(record).model_dump())
