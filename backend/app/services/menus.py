"""F1 물가 검색의 식당 메뉴 부분: 검색어를 menu_prices의 메뉴 이름에 매칭하고 가격 분포를 낸다.

메뉴 이름은 가게마다 자유롭게 적혀 있다 ("김치찌개", "김치찌개(1인)", "물냉면").
그래서 대표 메뉴마다 한글 표기들을 두고, 메뉴 이름에 그 표기가 들어 있으면 같은 메뉴로 본다.
사전에 없는 한글 검색어도 메뉴 이름에 들어 있으면 그대로 묶어서 보여준다 (예: 청국장).
"""
import re
from statistics import median, quantiles

from app.services.search import normalize

# 대표 메뉴(한글) → (영어 표시 이름, 메뉴 이름에서 찾을 한글 표기들, 영어 검색어들). 검색어는 소문자.
MENU_DICT: dict[str, tuple[str, list[str], list[str]]] = {
    "김치찌개": ("Kimchi stew", ["김치찌개", "김치찌게"], ["kimchi stew", "kimchi jjigae", "kimchijjigae"]),
    "된장찌개": ("Soybean paste stew", ["된장찌개", "된장찌게"], ["doenjang jjigae", "soybean paste stew", "doenjang stew"]),
    "순두부찌개": ("Soft tofu stew", ["순두부"], ["sundubu", "sundubu jjigae", "soft tofu stew", "tofu stew"]),
    "부대찌개": ("Army stew", ["부대찌개", "부대찌게"], ["budae jjigae", "army stew", "army base stew"]),
    "청국장": ("Rich soybean paste stew", ["청국장"], ["cheonggukjang"]),
    "비빔밥": ("Bibimbap", ["비빔밥"], ["bibimbap", "bibim bap", "mixed rice"]),
    "백반": ("Korean set meal (baekban)", ["백반"], ["baekban", "set meal", "korean set meal"]),
    "냉면": ("Cold noodles (naengmyeon)", ["냉면"], ["naengmyeon", "naengmyun", "cold noodles"]),
    "칼국수": ("Knife-cut noodle soup", ["칼국수"], ["kalguksu", "knife cut noodles", "noodle soup"]),
    "잔치국수": ("Banquet noodles", ["잔치국수"], ["janchi guksu", "banquet noodles"]),
    "비빔국수": ("Spicy mixed noodles", ["비빔국수"], ["bibim guksu", "spicy noodles"]),
    "짜장면": ("Black bean noodles (jajangmyeon)", ["짜장", "자장"], ["jajangmyeon", "jjajangmyeon", "jajangmyun", "black bean noodles"]),
    "짬뽕": ("Spicy seafood noodle soup (jjamppong)", ["짬뽕"], ["jjamppong", "champon", "spicy seafood noodles"]),
    "탕수육": ("Sweet and sour pork", ["탕수육"], ["tangsuyuk", "sweet and sour pork"]),
    "볶음밥": ("Fried rice", ["볶음밥"], ["fried rice", "bokkeumbap"]),
    "삼겹살": ("Pork belly (samgyeopsal)", ["삼겹살"], ["samgyeopsal", "pork belly", "korean bbq"]),
    "불고기": ("Bulgogi", ["불고기"], ["bulgogi"]),
    "제육볶음": ("Spicy stir-fried pork", ["제육"], ["jeyuk", "jeyuk bokkeum", "spicy pork"]),
    "갈비탕": ("Short rib soup", ["갈비탕"], ["galbitang", "short rib soup"]),
    "설렁탕": ("Ox bone soup", ["설렁탕"], ["seolleongtang", "ox bone soup"]),
    "삼계탕": ("Ginseng chicken soup", ["삼계탕"], ["samgyetang", "ginseng chicken soup"]),
    "국밥": ("Rice soup (gukbap)", ["국밥"], ["gukbap", "rice soup"]),
    "해장국": ("Hangover soup", ["해장국"], ["haejangguk", "hangover soup"]),
    "김밥": ("Gimbap", ["김밥"], ["kimbap", "gimbap"]),
    "떡볶이": ("Tteokbokki", ["떡볶이", "떡뽁이"], ["tteokbokki", "ddeokbokki", "topokki", "rice cake"]),
    "만두": ("Dumplings (mandu)", ["만두"], ["mandu", "dumpling", "dumplings"]),
    "라면": ("Ramyeon (restaurant)", ["라면"], ["ramen", "ramyeon", "ramyun"]),
    "돈가스": ("Pork cutlet (tonkatsu)", ["돈가스", "돈까스", "돈카츠"], ["tonkatsu", "donkatsu", "pork cutlet"]),
    "치킨": ("Fried chicken", ["치킨", "통닭"], ["fried chicken", "chicken"]),
    "아메리카노": ("Americano", ["아메리카노"], ["americano", "coffee"]),
    "카페라떼": ("Caffe latte", ["라떼", "라테"], ["latte", "cafe latte", "caffe latte"]),
    "커트": ("Haircut", ["커트", "컷트"], ["haircut", "hair cut"]),
    "파마": ("Perm", ["파마", "펌"], ["perm", "permanent"]),
    "염색": ("Hair dye", ["염색"], ["hair dye", "dye", "hair color"]),
}

_HANGUL = re.compile(r"[가-힣]")


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def match_keywords(query: str) -> list[str]:
    """검색어에 해당하는 대표 메뉴들. 영어 이름·검색어와 일치하거나, 한글 표기가 검색어에 들어 있으면 매칭."""
    q = normalize(query)
    qc = _compact(q)
    if not qc:
        return []
    hits = []
    for key, (en, spellings, aliases) in MENU_DICT.items():
        en_keys = {normalize(en), *(normalize(a) for a in aliases)}
        if q in en_keys or qc in {_compact(k) for k in en_keys}:
            hits.append(key)
        elif _HANGUL.search(qc) and (qc in {_compact(s) for s in spellings} or any(s in qc for s in spellings) or qc in key):
            hits.append(key)
    return hits


def price_stats(prices: list[int]) -> dict:
    """'보통' 범위는 가운데 50% (25~75번째 백분위), 대표값은 중앙값. 극단값에 덜 흔들린다."""
    prices = sorted(prices)
    if len(prices) >= 4:
        q1, _, q3 = quantiles(prices, n=4, method="inclusive")
    else:
        q1, q3 = prices[0], prices[-1]
    return {
        "count": len(prices),
        "price_low": int(round(q1 / 100) * 100),  # 100원 단위로 반올림
        "price_median": int(round(median(prices) / 100) * 100),
        "price_high": int(round(q3 / 100) * 100),
        "price_min": prices[0],
        "price_max": prices[-1],
    }


def _examples(rows: list[dict], district_names: dict[str, str], n: int = 3) -> list[dict]:
    """중앙값에 가까운 가게 몇 곳 (자치구가 서로 다르게)."""
    mid = median(r["price"] for r in rows)
    out, seen = [], set()
    for r in sorted(rows, key=lambda r: (abs(r["price"] - mid), r["store_name"])):
        gu = r.get("district_code")
        if gu in seen:
            continue
        seen.add(gu)
        out.append(
            {
                "store_name": r["store_name"],
                "menu_name": r["menu_name"],
                "price": r["price"],
                "district": district_names.get(gu or "", None),
            }
        )
        if len(out) == n:
            break
    return out


def search_menus(query: str, rows: list[dict], district_names: dict[str, str], min_count: int = 3) -> list[dict]:
    """검색어에 맞는 메뉴 묶음마다 가격 분포를 돌려준다. 가게 수가 min_count 미만이면 버린다."""
    groups: list[tuple[str, str | None, list[dict]]] = []
    for key in match_keywords(query):
        en, spellings, _ = MENU_DICT[key]
        matched = [r for r in rows if any(s in _compact(r["menu_name"]) for s in spellings)]
        groups.append((key, en, matched))

    # 사전에 없는 한글 검색어: 메뉴 이름에 그대로 들어 있으면 묶는다
    qc = _compact(normalize(query))
    if not groups and _HANGUL.search(qc) and len(qc) >= 2:
        groups.append((qc, None, [r for r in rows if qc in _compact(r["menu_name"])]))

    out = []
    for key, en, matched in groups:
        if len({r["store_id"] for r in matched}) < min_count:
            continue
        out.append(
            {
                "name_ko": key,
                "name_en": en,
                **price_stats([r["price"] for r in matched]),
                "store_count": len({r["store_id"] for r in matched}),
                "examples": _examples(matched, district_names),
            }
        )
    out.sort(key=lambda m: -m["count"])
    return out
