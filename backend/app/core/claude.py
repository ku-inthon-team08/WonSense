from functools import lru_cache

import anthropic

from app.core.config import get_settings


@lru_cache
def get_claude() -> anthropic.Anthropic:
    """LLM 클라이언트 (FastAPI 의존성). Anthropic Messages API 형식으로 부른다.

    - 기본: Claude API (ANTHROPIC_API_KEY)
    - LLM_BASE_URL이 있으면 그 Anthropic 호환 게이트웨이(예: Lablup Token Factory)로 보낸다.
      게이트웨이는 Claude Code처럼 Authorization: Bearer 헤더로 키를 받는다.
    """
    s = get_settings()
    if s.llm_base_url:
        return anthropic.Anthropic(base_url=s.llm_base_url.rstrip("/"), auth_token=s.llm_api_key, api_key=None)
    return anthropic.Anthropic(api_key=s.llm_api_key or s.anthropic_api_key)


def get_llm_model() -> str:
    return get_settings().llm_model


def is_claude_model(model: str) -> bool:
    """구조화 출력(messages.parse)·effort·프롬프트 캐시는 Claude 모델에서만 쓴다."""
    return model.startswith("claude")
