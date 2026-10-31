from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .env에 아직 쓰지 않는 키가 있어도 서버가 뜨도록 extra="ignore"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str = ""
    # 서울 열린데이터광장 인증키. 예전 이름 SEOUL_API_KEY도 받는다
    seoul_openapi_key: str = Field("", validation_alias=AliasChoices("SEOUL_OPENAPI_KEY", "SEOUL_API_KEY"))
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @field_validator("supabase_url")
    @classmethod
    def check_supabase_url(cls, v: str) -> str:
        # 대시보드 주소를 넣으면 모든 요청이 HTML 200으로 응답해 오류가 드러나지 않는다
        if "supabase.com/dashboard" in v:
            raise ValueError("SUPABASE_URL은 대시보드 주소가 아니라 https://<project-ref>.supabase.co 형식이어야 합니다")
        return v.rstrip("/")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
