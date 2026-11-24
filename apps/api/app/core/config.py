"""应用配置：从环境变量 / .env 读取（键名与仓库根目录 .env.example 对齐）。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """集中管理全部配置，禁止在业务代码里硬编码。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- 应用 ----
    app_env: str = "development"
    app_base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"

    # ---- 鉴权（JWT 存 httpOnly Cookie）----
    jwt_secret: str = "xinghuo-dev-secret-change-me-in-production-32b"
    jwt_expire_minutes: int = 1440

    # ---- 认证规则 ----
    student_no_pattern: str = r"^\d{8,12}$"  # 学号段初筛正则（可配置）
    login_max_attempts: int = 5  # 登录失败锁定阈值
    login_lock_seconds: int = 900  # 锁定时长（秒）

    # ---- PostgreSQL ----
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "xinghuo"
    postgres_user: str = "xinghuo"
    postgres_password: str = "please-change-this-in-dev"

    # ---- Redis ----
    redis_url: str = "redis://cache:6379/0"

    # ---- 对象存储（S3 兼容；开发默认本地文件系统）----
    s3_backend: str = "local"  # local / s3
    s3_local_dir: str = "/data/uploads"  # 本地模式存储目录
    s3_endpoint: str = "http://storage:9000"
    s3_region: str = "us-east-1"
    s3_bucket: str = "xinghuo-private"
    s3_access_key: str = "please-change-this-in-dev"
    s3_secret_key: str = "please-change-this-in-dev"
    s3_sign_expire_seconds: int = 300

    # ---- 业务时限（配置项，禁止写死）----
    order_accept_timeout_hours: int = 48
    appeal_decide_timeout_hours: int = 72
    task_apply_limit: int = 5
    task_reward_max: int = 500

    # ---- 功能开关 ----
    feature_ai_draft: bool = True
    feature_ai_llm: bool = False
    feature_maintenance: bool = False
    readonly_mode: bool = False

    # ---- 限流与备份 ----
    rate_limit_per_minute: int = 60
    backup_keep_days: int = 7

    @property
    def database_url(self) -> str:
        """同步驱动的 PostgreSQL 连接串（psycopg 3）。"""
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
