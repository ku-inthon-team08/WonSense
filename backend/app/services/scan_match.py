"""Claude가 아닌 모델(DeepSeek 등)용: 사진에서 읽은 줄을 코드로 기준가에 연결한다.

DeepSeek은 '읽기 + 품목 125개 대조 + 수량 비율'을 한 번에 시키면 생각(thinking)이 길어져
출력 한도를 다 쓰고 답을 못 내는 일이 잦았다. 그래서 모델에는 읽기·번역만 맡기고
품목 대조(search_items), 수량 비율, Numbeo 항목 고르기는 여기서 한다.
"""
import re

from app.services.search import search_items

# 같은 단위로 볼 개수 단위 묶음. 나머지 개수 단위는 글자가 같을 때만 비교한다 (1팩 vs 10개는 비교 불가).
_COUNT_SYNONYMS = {"구": "개", "ea": "개"}
_UNIT = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(kg|g|ml|l|liter|litre|개입|개|구|입|봉|병|캔|마리|포기|송이|팩|모|단|통|장|ea)(?![a-z])",
    re.IGNORECASE,
)


def parse_amount(text: str | None) -> tuple[float, str] | None:
    """'계란 30구' → (30, '개'), '1.5L' → (1500, 'ml'), '500 g' → (500, 'g'). 첫 번째 수량만 본다."""
    if not text:
        return None
    m = _UNIT.search(text)
    if not m:
        return None
    value = float(m.group(1).replace(",", ""))
    unit = m.group(2).lower()
    if unit == "kg":
        return value * 1000, "g"
    if unit in ("l", "liter", "litre"):
        return value * 1000, "ml"
    if unit == "개입":
        unit = "개"
    return value, _COUNT_SYNONYMS.get(unit, unit)


def quantity_ratio(photo: str | None, reference: str | None) -> float:
    """사진 속 수량이 기준 규격의 몇 배인지. 단위가 다르거나 모르면 1."""
    a, b = parse_amount(photo), parse_amount(reference)
    if not a or not b or a[1] != b[1] or b[0] <= 0:
        return 1.0
    return round(a[0] / b[0], 3)


# name_en에 이 단어가 있으면 Numbeo 항목(이름 앞부분)으로 추정한다. 위에서부터 먼저 맞는 것.
REFERENCE_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("taxi",), "Taxi Start"),
    (("subway", "metro", "bus fare", "transit"), "One-Way Ticket"),
    (("cinema", "movie"), "Cinema Ticket"),
    (("cappuccino", "latte", "americano", "coffee", "espresso"), "Cappuccino"),
    (("cola", "coke", "pepsi", "soda", "cider", "soft drink"), "Soft Drink"),
    (("water",), "Bottled Water (0.33"),
    (("imported beer",), "Imported Beer (0.33 Liter Bottle)"),
    (("beer",), "Domestic Draft Beer"),
    (("wine",), "Bottle of Wine"),
    (("cigarette",), "Cigarettes"),
    (("milk",), "Milk"),
    (("bread",), "Fresh White Bread"),
    (("cheese",), "Local Cheese"),
    (("apple",), "Apples"),
    (("banana",), "Bananas"),
    (("orange",), "Oranges"),
    (("tomato",), "Tomatoes"),
    (("potato",), "Potatoes"),
    (("onion",), "Onions"),
    (("lettuce",), "Lettuce"),
]
DISH_FALLBACK = "Meal at an Inexpensive Restaurant"


def reference_for(name_en: str, kind: str, entries: dict[int, dict]) -> int | None:
    """Numbeo 항목 id. 식당 음식인데 맞는 단어가 없으면 '저렴한 식당 한 끼'로 본다."""
    text = name_en.lower()
    for words, prefix in REFERENCE_KEYWORDS:
        if any(w in text for w in words):
            hit = next((i for i, e in entries.items() if e["item"].startswith(prefix)), None)
            if hit:
                return hit
    if kind == "dish":
        return next((i for i, e in entries.items() if e["item"].startswith(DISH_FALLBACK)), None)
    return None


def match_line(name: str, name_en: str, quantity: str | None, kind: str, items: list[dict], entries: dict[int, dict]):
    """(item_id, reference_id, quantity_ratio). 식당 음식은 장보기 품목과 맞추지 않는다
    ('김치찌개'가 '김치 3.3kg'에 걸리지 않게). 식당 메뉴 가격은 judge_line이 따로 찾는다."""
    if kind != "dish":
        hit = search_items(name, items, 1)
        if hit:
            item = hit[0]
            return item["item_id"], None, quantity_ratio(quantity or name, item.get("unit") or item["name_ko"])
    ref = reference_for(name_en, kind, entries)
    if ref is None:
        return None, None, None
    return None, ref, quantity_ratio(quantity or name, entries[ref]["item"])
