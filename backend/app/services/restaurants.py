"""F1 물가 검색의 일반 식당 가격 부분: restaurant_prices(LLM 웹 검색으로 수집)를 검색어에 매칭한다.

착한가격업소(menu_prices)는 일반 시세보다 싸게 나오므로, 일반 식당 가격을 따로 보여준다.
웹 검색 기반 추정이라 가격마다 출처 링크를 같이 내보내고, 사람이 확인한 개수(verified)도 알려준다.
메뉴 매칭은 식당 메뉴 사전(menus.MENU_DICT)을 그대로 쓴다.
"""
import re
from collections import defaultdict
from statistics import median

from app.services.menus import MENU_DICT, match_keywords, price_stats
from app.services.search import normalize

_HANGUL = re.compile(r"[가-힣]")


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def search_restaurant_prices(query: str, rows: list[dict], examples: int = 5) -> list[dict]:
    """검색어에 맞는 메뉴(restaurant_prices.menu)마다 가격 분포, 지역별 중앙값, 출처가 있는 예시 식당."""
    spellings: list[str] = []
    en_by_spelling: dict[str, str] = {}
    for key in match_keywords(query):
        en, sp, _ = MENU_DICT[key]
        spellings += sp
        en_by_spelling.update({s: en for s in sp})
    qc = _compact(normalize(query))
    if not spellings and _HANGUL.search(qc) and len(qc) >= 2:
        spellings = [qc]  # 사전에 없는 한글 검색어는 메뉴 이름에 그대로 들어 있으면 매칭

    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if any(s in _compact(r["menu"]) for s in spellings):
            groups[r["menu"]].append(r)

    out = []
    for menu, rs in groups.items():
        by_area: dict[str, list[int]] = defaultdict(list)
        for r in rs:
            by_area[r["area"]].append(r["price"])
        name_en = next((en for s, en in en_by_spelling.items() if s in _compact(menu)), None)
        picked = sorted(rs, key=lambda r: (not r.get("verified"), r["area"], r["price"]))[:examples]
        out.append(
            {
                "menu": menu,
                "name_en": name_en,
                **price_stats([r["price"] for r in rs]),
                "verified_count": sum(1 for r in rs if r.get("verified")),
                "by_area": sorted(
                    ({"area": a, "count": len(p), "price_median": int(round(median(p) / 100) * 100)} for a, p in by_area.items()),
                    key=lambda x: -x["price_median"],
                ),
                "examples": [
                    {
                        "place_name": r["place_name"],
                        "area": r["area"],
                        "price": r["price"],
                        "weight_g": r.get("weight_g"),
                        "source_url": r["source_url"],
                        "place_url": r.get("place_url"),
                        "verified": bool(r.get("verified")),
                    }
                    for r in picked
                ],
                "reference_date": max(r["checked_on"] for r in rs),
            }
        )
    return sorted(out, key=lambda m: -m["count"])
