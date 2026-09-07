from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BACKEND_DIR / ".env"), extra="ignore")

    env: str = "development"

    database_url: str = "postgresql+psycopg://coolgrid:coolgrid_dev_password@localhost:5432/coolgrid"

    jwt_secret_key: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    cors_origins: str = "http://localhost:3000"

    # CoolGrid's demo climatology has a real Pune-like seasonal cycle (hot
    # Mar-Jun, cooler monsoon Jun-Sep, mild winter). Anchoring "today" to a
    # fixed pre-monsoon peak-heat date means the dashboard/hotspots/demo flow
    # reliably shows dramatic hotspots and cooling opportunities no matter
    # which real calendar day the demo is actually run on. This only affects
    # which synthetic date's weather is sampled -- it is not a fake system
    # clock.
    demo_reference_date: str = "2026-04-20"

    demo_user_email: str = "demo@coolgrid.app"
    demo_user_password: str = "CoolGrid#Demo2026"
    demo_admin_email: str = "admin@coolgrid.app"
    demo_admin_password: str = "CoolGrid#Admin2026"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ml_artifacts_dir(self) -> Path:
        return REPO_ROOT / "data" / "demo" / "models"

    @property
    def seed_dir(self) -> Path:
        return REPO_ROOT / "data" / "demo" / "seed"

    @property
    def generated_reports_dir(self) -> Path:
        return REPO_ROOT / "data" / "generated_reports"

    def effective_today(self):
        from datetime import date

        return date.fromisoformat(self.demo_reference_date)


@lru_cache
def get_settings() -> Settings:
    return Settings()
