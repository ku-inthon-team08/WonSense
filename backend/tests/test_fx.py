import pytest

from app.routers import fx as fx_router
from app.services.fx import HISTORY_POINTS, build_fx


def _rows(days: int) -> list[dict]:
    rows = []
    for i in range(days):
        d = f"2026-10-{i + 1:02d}"
        rows += [
            {"date": d, "base": "KRW", "quote": "USD", "rate": 0.00075 - i * 0.000001},
            {"date": d, "base": "KRW", "quote": "JPY", "rate": 0.118},
        ]
    return rows


def test_build_fx_converts_to_krw_per_unit_and_keeps_recent_history():
    data = build_fx(_rows(20))
    usd, jpy = data["currencies"]
    assert [c["code"] for c in data["currencies"]] == ["USD", "JPY"]  # 데이터 없는 통화는 빠진다
    assert len(usd["history"]) == HISTORY_POINTS
    assert usd["history"][-1]["date"] == "2026-10-20" == data["date"]
    assert usd["krw"] == round(1 / (0.00075 - 19 * 0.000001), 2)
    assert jpy["unit"] == 100 and jpy["krw"] == round(100 / 0.118, 2)  # 100엔 기준
    assert usd["change_pct"] > 0 and jpy["change_pct"] == 0  # 원화 약세 = 달러당 원화가 오름


def test_build_fx_single_day_has_no_change_and_empty_fails():
    assert build_fx(_rows(1))["currencies"][0]["change_pct"] is None
    with pytest.raises(ValueError):
        build_fx([])


def test_router_serves_stale_cache_when_upstream_fails(monkeypatch):
    monkeypatch.setattr(fx_router, "_cache", {"at": 0.0, "data": None})
    monkeypatch.setattr(fx_router, "fetch_rates", lambda: _rows(3))
    first = fx_router.get_fx()

    def boom():
        raise RuntimeError("network down")

    monkeypatch.setattr(fx_router, "fetch_rates", boom)
    fx_router._cache["at"] = float("-inf")  # 캐시 만료
    assert fx_router.get_fx() == first

    monkeypatch.setattr(fx_router, "_cache", {"at": 0.0, "data": None})
    with pytest.raises(fx_router.HTTPException):
        fx_router.get_fx()
