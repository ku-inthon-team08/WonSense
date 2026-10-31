import re
import time
from collections import defaultdict, deque

import bcrypt

# 리뷰 응답에 포함할 컬럼. password_hash는 절대 넣지 않는다
REVIEW_COLUMNS = (
    "id, nickname, title, body, paid_price, price_feeling, rating, created_at, updated_at, "
    "store:stores(id, name, category, district)"
)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def clean_search_term(q: str | None) -> str:
    """PostgREST 필터 문법에 쓰이는 문자(, . ( ) * % : " \\)를 지워 검색어로 안전하게 쓴다."""
    if not q:
        return ""
    return re.sub(r'[,.()*%:"\\]', " ", q).strip()


class AttemptLimiter:
    """비밀번호 무차별 대입을 막기 위해 (클라이언트, 리뷰)별 실패 횟수를 제한한다.

    프로세스 메모리에 저장하므로 서버를 재시작하거나 여러 인스턴스로 띄우면 초기화된다 (MVP용).
    """

    def __init__(self, max_failures: int = 5, window_seconds: int = 600):
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures: dict[tuple[str, int], deque[float]] = defaultdict(deque)

    def _recent(self, key: tuple[str, int]) -> deque[float]:
        failures = self._failures[key]
        cutoff = time.monotonic() - self.window_seconds
        while failures and failures[0] < cutoff:
            failures.popleft()
        return failures

    def is_blocked(self, client: str, review_id: int) -> bool:
        return len(self._recent((client, review_id))) >= self.max_failures

    def record_failure(self, client: str, review_id: int) -> None:
        self._recent((client, review_id)).append(time.monotonic())

    def reset(self, client: str, review_id: int) -> None:
        self._failures.pop((client, review_id), None)


password_limiter = AttemptLimiter()
