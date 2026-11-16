"""对象存储客户端（S3 兼容 / 本地文件系统）。

学生证影像与凭证图片经由此封装统一读写。
开发环境默认走本地文件系统（MinIO 官方镜像已停止免费分发）；生产切 S3，
接口保持不变，业务层无需感知后端差异。
"""

from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings


class S3Client:
    """封装 boto3 S3 客户端，提供上传 / 签名 URL / 删除。"""

    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = settings.s3_bucket

    def upload_object(self, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    def presigned_get_url(self, key: str) -> str:
        """生成短时有效的下载签名 URL。"""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=settings.s3_sign_expire_seconds,
        )

    def delete_object(self, key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False


class LocalStorage:
    """本地文件系统存储（开发模式），接口与 S3Client 对齐。"""

    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)

    def upload_object(self, key: str, data: bytes, content_type: str) -> None:
        path = self.base_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def presigned_get_url(self, key: str) -> str:
        return f"/uploads/{key}"

    def delete_object(self, key: str) -> None:
        (self.base_dir / key).unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return (self.base_dir / key).exists()


_client: S3Client | LocalStorage | None = None


def get_s3() -> S3Client | LocalStorage:
    """惰性获取对象存储客户端：本地模式返回 LocalStorage，否则返回 S3Client。"""
    global _client
    if _client is None:
        if settings.s3_backend == "local":
            _client = LocalStorage(settings.s3_local_dir)
        else:
            _client = S3Client()
    return _client
