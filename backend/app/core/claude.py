from functools import lru_cache

import anthropic

from app.core.config import get_settings


@lru_cache
def get_claude() -> anthropic.Anthropic:
    """Claude API 클라이언트 (FastAPI 의존성). 키는 backend/.env의 ANTHROPIC_API_KEY."""
    return anthropic.Anthropic(api_key=get_settings().anthropic_api_key)
