from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_LLM_MODEL = "claude-haiku-5-5"


class Settings(BaseSettings):
    # .env에 아직 쓰지 않는 키가 있어도 서버가 뜨도록 extra="ignore"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str
    supabase_service_role_key: str
    # 서울 열린데이터광장 인증키. 예전 이름 SEOUL_API_KEY도 받는다
    seoul_openapi_key: str = Field("", validation_alias=AliasChoices("SEOUL_OPENAPI_KEY", "SEOUL_API_KEY"))
    anthropic_api_key: str = ""
    # LLM (바가지 판독기). 비워 두면 Claude API를 ANTHROPIC_API_KEY로 쓴다.
    # Lablup Token Factory 같은 Anthropic 호환 게이트웨이를 쓰려면 셋 다 넣는다:
    #   LLM_BASE_URL=https://api.console.lablup.ai/anthropic
    #   LLM_API_KEY=<console.lablup.ai에서 발급한 키>
    #   LLM_MODEL=DeepSeek-V4.1-Flash-B300
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = DEFAULT_LLM_MODEL
    # 공공데이터포털 일반 인증키 (Decoding). 한국소비자원 참가격 생필품 가격 수집에 쓴다
    data_go_kr_api_key: str = ""
    # 카카오 디벨로퍼스 REST API 키 (로컬 장소 검색). 식당 가격 수집 스크립트에서만 쓴다
    kakao_rest_api_key: str = ""
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    # 배포된 프론트(Vercel 프로덕션 won-sense.vercel.app + 프리뷰 won-sense-*.vercel.app)를 허용.
    # CORS_ORIGINS는 .env로 덮어쓰면 기본값이 사라지므로 따로 둔다. 비우면 정규식 허용을 끈다
    cors_origin_regex: str = r"https://won-sense(-[a-z0-9-]+)?\.vercel\.app"

    @field_validator("llm_model")
    @classmethod
    def default_llm_model(cls, v: str) -> str:
        # .env.example처럼 LLM_MODEL= 로 비워 두면 기본 Claude 모델을 쓴다
        return v.strip() or DEFAULT_LLM_MODEL

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
