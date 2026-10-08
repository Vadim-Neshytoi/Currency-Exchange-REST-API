import os
from dataclasses import dataclass, field
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class AppSecurityConfig:
    cors_allowed_origins: list[str]
    max_body_size: int


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    db_path: Path
    log_path: Path
    security: AppSecurityConfig

    @classmethod
    def load_from_env(cls) -> 'Settings':
        HOST: str = os.getenv("HOST", "0.0.0.0")
        PORT: int = int(os.getenv("PORT", 8000))

        default_db = BASE_DIR / "data" / "currency_exchange.db"
        DB_PATH: Path = Path(os.getenv("DB_PATH", default_db))

        default_log = BASE_DIR / "server_app.log"
        LOG_PATH: Path = Path(os.getenv("LOG_PATH", default_log))

        raw_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8080")
        security_cfg = AppSecurityConfig(
            cors_allowed_origins=[org.strip() for org in raw_origins.split(",")],
            max_body_size=int(os.getenv("MAX_BODY_SIZE", 1 * 1024 * 1024))
        )

        return cls(host=HOST,
                   port=PORT,
                   db_path=DB_PATH,
                   log_path=LOG_PATH,
                   security=security_cfg
                   )
























