import time
from collections.abc import Callable
from typing import Any

CACHE_TTL = 600  # 가격은 월 1회 갱신되므로 10분 캐시면 충분하다


class TtlCache:
    """load()의 결과를 ttl초 동안 프로세스 메모리에 둔다. load가 예외를 내면 저장하지 않는다."""

    def __init__(self, ttl: float = CACHE_TTL):
        self.ttl = ttl
        self._at = 0.0
        self._value: Any = None

    def get(self, load: Callable[[], Any]) -> Any:
        now = time.monotonic()
        if self._value is None or now - self._at > self.ttl:
            self._value = load()
            self._at = now
        return self._value
