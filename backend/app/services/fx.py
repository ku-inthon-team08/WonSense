"""환율 (퀴즈 아래 참고용). Frankfurter API의 중앙은행 기준 환율을 원화 기준으로 바꾼다.

API 키가 필요 없고 하루 한 번 갱신된다: https://frankfurter.dev
응답 행: {"date": "2026-10-31", "base": "KRW", "quote": "USD", "rate": 0.00074833} (1원 = rate 외화)
"""
from collections import defaultdict
from datetime import date, timedelta

import httpx

FX_URL = "https://api.frankfurter.dev/v2/rates"
FX_SOURCE = "Frankfurter"
# (통화, 표시 단위). 엔화는 관례대로 100엔 기준으로 보여준다
CURRENCIES: list[tuple[str, int]] = [("USD", 1), ("JPY", 100), ("CNY", 1), ("EUR", 1)]
HISTORY_POINTS = 14  # 스파크라인에 쓸 최근 일수 (Frankfurter는 주말 값도 준다)
LOOKBACK_DAYS = 24  # 데이터가 빠진 날이 있어도 14개가 채워지도록 넉넉히 조회


def fetch_rates(today: date | None = None, timeout: float = 8.0) -> list[dict]:
    today = today or date.today()
    params = {
        "base": "KRW",
        "quotes": ",".join(code for code, _ in CURRENCIES),
        "from": (today - timedelta(days=LOOKBACK_DAYS)).isoformat(),
        "to": today.isoformat(),
    }
    res = httpx.get(FX_URL, params=params, timeout=timeout)
    res.raise_for_status()
    return res.json()


def build_fx(rows: list[dict]) -> dict:
    """Frankfurter 행을 통화별 '단위당 원화' 시계열로 바꾼다. 마지막 값이 오늘(최신) 환율."""
    by_code: dict[str, dict[str, float]] = defaultdict(dict)
    for r in rows:
        if r.get("rate"):
            by_code[r["quote"].upper()][r["date"]] = r["rate"]

    currencies = []
    for code, unit in CURRENCIES:
        series = sorted(by_code.get(code, {}).items())[-HISTORY_POINTS:]
        if not series:
            continue
        history = [{"date": d, "krw": round(unit / rate, 2)} for d, rate in series]
        latest, prev = history[-1], (history[-2] if len(history) > 1 else None)
        currencies.append(
            {
                "code": code,
                "unit": unit,
                "krw": latest["krw"],
                "date": latest["date"],
                "change_pct": round((latest["krw"] / prev["krw"] - 1) * 100, 2) if prev else None,
                "history": history,
            }
        )
    if not currencies:
        raise ValueError("환율 데이터가 비어 있습니다")
    return {
        "base": "KRW",
        "date": max(c["date"] for c in currencies),
        "source": FX_SOURCE,
        "currencies": currencies,
    }
