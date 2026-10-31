"""환율 (퀴즈 아래 참고용). Frankfurter API의 중앙은행 기준 환율을 원화 기준으로 바꾼다.

API 키가 필요 없고 하루 한 번 갱신된다: https://frankfurter.dev
응답 행: {"date": "2026-10-31", "base": "KRW", "quote": "USD", "rate": 0.00074833} (1원 = rate 외화)
"""
from collections import defaultdict
from datetime import date, timedelta

import httpx

FX_URL = "https://api.frankfurter.dev/v2/rates"
FX_SOURCE = "Frankfurter"
# (통화, 표시 단위). 엔화·동·루피아처럼 단위가 작은 통화는 관례대로 100 단위로 보여준다
CURRENCIES: list[tuple[str, int]] = [("USD", 1), ("JPY", 100), ("CNY", 1), ("EUR", 1)]  # 홈 화면용 주요 통화
# 환율 페이지에서 더 보여줄 통화: 서울을 찾는 외국인이 많은 나라 위주
EXTRA_CURRENCIES: list[tuple[str, int]] = [
    ("GBP", 1), ("AUD", 1), ("CAD", 1), ("NZD", 1), ("CHF", 1),
    ("HKD", 1), ("TWD", 1), ("SGD", 1), ("THB", 1), ("VND", 100),
    ("PHP", 1), ("IDR", 100), ("MYR", 1), ("INR", 1), ("MNT", 100),
    ("RUB", 1), ("KZT", 1), ("UZS", 100),
]
ALL_CURRENCIES = CURRENCIES + EXTRA_CURRENCIES
HISTORY_POINTS = 14  # 스파크라인에 쓸 최근 일수 (Frankfurter는 주말 값도 준다)
LOOKBACK_DAYS = 24  # 데이터가 빠진 날이 있어도 14개가 채워지도록 넉넉히 조회


def fetch_rates(today: date | None = None, timeout: float = 8.0) -> list[dict]:
    today = today or date.today()
    params = {
        "base": "KRW",
        "quotes": ",".join(code for code, _ in ALL_CURRENCIES),
        "from": (today - timedelta(days=LOOKBACK_DAYS)).isoformat(),
        "to": today.isoformat(),
    }
    res = httpx.get(FX_URL, params=params, timeout=timeout)
    res.raise_for_status()
    return res.json()


def build_fx(rows: list[dict], currencies: list[tuple[str, int]] = ALL_CURRENCIES) -> dict:
    """Frankfurter 행을 통화별 '단위당 원화' 시계열로 바꾼다. 마지막 값이 오늘(최신) 환율."""
    by_code: dict[str, dict[str, float]] = defaultdict(dict)
    for r in rows:
        if r.get("rate"):
            by_code[r["quote"].upper()][r["date"]] = r["rate"]

    out = []
    for code, unit in currencies:
        series = sorted(by_code.get(code, {}).items())[-HISTORY_POINTS:]
        if not series:
            continue
        history = [{"date": d, "krw": round(unit / rate, 2)} for d, rate in series]
        latest, prev = history[-1], (history[-2] if len(history) > 1 else None)
        out.append(
            {
                "code": code,
                "unit": unit,
                "krw": latest["krw"],
                "date": latest["date"],
                "change_pct": round((latest["krw"] / prev["krw"] - 1) * 100, 2) if prev else None,
                "history": history,
            }
        )
    if not out:
        raise ValueError("환율 데이터가 비어 있습니다")
    return {
        "base": "KRW",
        "date": max(c["date"] for c in out),
        "source": FX_SOURCE,
        "currencies": out,
    }


def main_only(fx: dict) -> dict:
    """홈 화면용: 주요 통화(CURRENCIES)만 남긴다."""
    main = {code for code, _ in CURRENCIES}
    return {**fx, "currencies": [c for c in fx["currencies"] if c["code"] in main]}
