from types import SimpleNamespace

import pytest

from app.core.cache import TtlCache
from app.db.supabase import PAGE, fetch_all
from app.services.menus import contains_any, round_to
from app.services.search import compact, free_korean_term


class FakePagedQuery:
    """range로 자른 만큼만 돌려주는 가짜 쿼리. 진짜 빌더처럼 range는 한 번만 부를 수 있다."""

    def __init__(self, rows):
        self.rows = rows
        self.ranged = False

    def range(self, start, end):
        assert not self.ranged, "range가 쌓이므로 페이지마다 쿼리를 새로 만들어야 한다"
        self.ranged = True
        self.slice = self.rows[start : end + 1]
        return self

    def execute(self):
        return SimpleNamespace(data=self.slice)


@pytest.mark.parametrize("count", [0, 1, PAGE - 1, PAGE, PAGE + 1, PAGE * 2 + 5])
def test_fetch_all_reads_every_page(count):
    rows = [{"id": i} for i in range(count)]
    assert fetch_all(lambda: FakePagedQuery(rows)) == rows


def test_ttl_cache_keeps_value_until_expired_and_skips_failures():
    calls = []

    def load():
        calls.append(1)
        return len(calls)

    cache = TtlCache(ttl=60)
    assert cache.get(load) == 1
    assert cache.get(load) == 1  # 캐시에서

    cache.ttl = -1  # 만료
    assert cache.get(load) == 2

    def boom():
        raise RuntimeError("db down")

    with pytest.raises(RuntimeError):
        TtlCache().get(boom)


def test_ttl_cache_keeps_empty_results():
    calls = []
    cache = TtlCache()
    cache.get(lambda: calls.append(1) or [])
    cache.get(lambda: calls.append(1) or [])
    assert len(calls) == 1  # 빈 목록도 결과다 (None만 "아직 없음")


def test_text_helpers():
    assert compact(" 김치  찌개 ") == "김치찌개"
    assert contains_any("김치 찌개(1인)", ["된장찌개", "김치찌개"])
    assert not contains_any("물냉면", ["김치찌개"])
    assert free_korean_term("청국 장") == "청국장"
    assert free_korean_term("김") is None  # 한 글자는 너무 많이 걸린다
    assert free_korean_term("pizza") is None
    assert round_to(1234, 100) == 1200 and round_to(1300, 500) == 1500
