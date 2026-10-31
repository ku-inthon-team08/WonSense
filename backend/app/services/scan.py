"""바가지 판독기: 가격표·영수증 사진을 읽어 서울 평균가와 비교한다.

Claude 호출 한 번으로 (1) 사진의 품목·가격을 읽고 (2) 우리 품목 목록 중 같은 품목을 고르고
(3) 사진의 수량이 기준 규격의 몇 배인지(quantity_ratio)를 정한다. 판정 계산은 코드에서 한다.

기준가 순서: (1) 장보기 품목은 서울시 생필품 가격(DB), (2) 식당 메뉴는 서울시 착한가격업소 메뉴 가격,
(3) 나머지(카페·교통·의류 등)는 Numbeo 서울 생활물가(data/seoul_cost_of_living.json) 추정.

메뉴판 통역: 같은 호출에서 메뉴마다 영어 설명·매운 정도·들어간 재료도 받는다.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel

from app.services.menus import search_menus

MODEL = "claude-haiku-5-5"

FAIR_BAND = 0.10  # 평균 ±10%는 적정가
RIPOFF = 0.30  # 평균보다 30% 넘게 비싸면 바가지

REFERENCE_PATH = Path(__file__).resolve().parent.parent / "data" / "seoul_cost_of_living.json"
# 가격표·메뉴판에 나올 만한 분류만 쓴다 (월세·집값·연봉·학비 제외)
REFERENCE_CATEGORIES = ("Restaurants", "Markets", "Transportation", "Sports And Leisure", "Clothing And Shoes")
REFERENCE_MAX_PRICE = 1_000_000  # 자동차 가격 같은 항목 제외

SYSTEM_PROMPT = """You read photos of price tags, market signs, menus, and receipts taken in Seoul \
and match each priced item to a grocery catalog or, failing that, a list of reference prices.

For every item in the photo that shows a price, return one line:
- name: the item name exactly as written in the photo (Korean if it is Korean).
- name_en: a short English name, lowercase, at most 4 words.
- price: the price in won as an integer, for the quantity shown in the photo.
- quantity: the quantity or size written in the photo (e.g. "30구", "1kg", "2개"), or null.
- item_id: the id of the grocery catalog item that is the same product, or null if nothing matches. \
Different varieties of the same product (e.g. two rice brands) still match. \
Restaurant dishes do not match grocery items.
- reference_id: only when item_id is null, the id of the reference price for the same kind of \
thing (e.g. a meal at an inexpensive restaurant for 김치찌개, a cappuccino, a taxi start fare), or null.
- quantity_ratio: how many units of the matched entry the photo's quantity equals. Example: photo \
"계란 30구" and catalog "계란 10개" gives 3; photo "콜라 500ml" and reference "0.33 Liter" gives 1.5. \
Use 1 when the sizes are the same or the photo shows no size. null when nothing matches.

Also explain each item to a foreign visitor who cannot read Korean:
- description_en: one plain English sentence of at most 15 words saying what it is, \
e.g. "Spicy stew of aged kimchi, pork, and tofu, served with rice." No prices.
- spice_level: for food, 0 not spicy, 1 mild, 2 medium, 3 very spicy; null for anything that is not food.
- contains: main ingredients a visitor may need to avoid, only from this list: \
pork, beef, chicken, seafood, egg, dairy, wheat, nuts, soy, alcohol. Empty list if none or not food.
- vegetarian: true only if the usual recipe has no meat, fish, or seafood (including broth and fish sauce); \
false if it does; null if you are not sure or it is not food.
Base these on the usual Korean recipe for that dish name.

Skip lines with no readable price, totals, tax, discounts, and payment lines. \
If the photo has no prices, return an empty list. Never invent items or prices."""


class ScannedLine(BaseModel):
    name: str
    name_en: str
    price: int
    quantity: str | None
    item_id: int | None
    # 기본값을 두지 않는다: 구조화 출력 스키마에서 선택 필드가 되면 모델이 빠뜨릴 수 있다
    reference_id: int | None
    quantity_ratio: float | None
    description_en: str | None
    spice_level: Literal[0, 1, 2, 3] | None
    contains: list[Literal["pork", "beef", "chicken", "seafood", "egg", "dairy", "wheat", "nuts", "soy", "alcohol"]]
    vegetarian: bool | None


class ScanOutput(BaseModel):
    lines: list[ScannedLine]


Verdict = Literal["cheap", "fair", "pricey", "ripoff"]


@lru_cache
def load_reference() -> dict:
    """Numbeo 기준가. id는 파일 순서대로 1부터 매긴다."""
    data = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    entries = [
        {"category": cat, **row}
        for cat in REFERENCE_CATEGORIES
        for row in data["categories"].get(cat, [])
        if row.get("price") and row["price"] < REFERENCE_MAX_PRICE
    ]
    src = data["source"]
    return {
        "entries": dict(enumerate(entries, 1)),
        "source": f"{src['site']} ({src['title']})",
        "reference_date": src["last_update"],
    }


def catalog_text(items: list[dict]) -> str:
    """시스템 프롬프트 뒤에 붙이는 품목 목록. 순서를 고정해 프롬프트 캐시가 깨지지 않게 한다."""
    rows = sorted(items, key=lambda it: it["item_id"])
    grocery = "\n".join(f"{it['item_id']} | {it['name_ko']} | {it['unit']}" for it in rows)
    reference = "\n".join(f"{i} | {e['item']} | {e['category']}" for i, e in load_reference()["entries"].items())
    return (
        f"Grocery catalog (id | name | unit):\n{grocery}\n\n"
        f"Reference prices, use only when no grocery item matches (id | item | category):\n{reference}"
    )


def extract_lines(client: anthropic.Anthropic, image_b64: str, media_type: str, items: list[dict]) -> list[ScannedLine]:
    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "low"},
        system=[
            {"type": "text", "text": SYSTEM_PROMPT},
            {"type": "text", "text": catalog_text(items), "cache_control": {"type": "ephemeral"}},
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
                    {"type": "text", "text": "Read every priced item in this photo."},
                ],
            }
        ],
        output_format=ScanOutput,
    )
    out = response.parsed_output
    if out is None:
        raise ValueError(f"사진 판독 실패 (stop_reason={response.stop_reason})")
    return out.lines


def verdict(diff: float) -> Verdict:
    if diff < -FAIR_BAND:
        return "cheap"
    if diff <= FAIR_BAND:
        return "fair"
    return "pricey" if diff <= RIPOFF else "ripoff"


def judge_reference(line: ScannedLine, entry: dict, ratio: float) -> dict:
    """DB에 없는 품목을 Numbeo 기준가로 추정한다. 구별 데이터는 없다."""
    ref = load_reference()
    avg = round(entry["price"] * ratio)
    diff = line.price / avg - 1
    return {
        "matched": True,
        "basis": "estimate",
        "item_id": None,
        "catalog_name": entry["item"],
        "catalog_unit": None,
        "quantity_ratio": ratio,
        "seoul_avg": avg,
        "seoul_range": [round(entry[k] * ratio) if entry.get(k) else None for k in ("min", "max")],
        "seoul_diff_pct": round(diff * 100, 1),
        "compare_avg": avg,
        "compare_region": None,
        "diff_pct": round(diff * 100, 1),
        "verdict": verdict(diff),
        "district_avg": None,
        "district_prices": {},
        "cheapest_district": None,
        "source": ref["source"],
        "reference_date": ref["reference_date"],
    }


MENU_SOURCE = "서울시 가격안정 모범업소(착한가격업소) 상품목록"


def judge_menu(line: ScannedLine, menu: dict, reference_date: str | None) -> dict:
    """식당 메뉴를 착한가격업소 가격과 비교한다. 착한가격업소는 일부러 싸게 받는 가게라
    중앙값이 아니라 '보통' 범위의 위쪽 끝(75번째 백분위)을 기준가로 쓴다. 한 그릇 기준이라 수량 비율은 쓰지 않는다."""
    avg = menu["price_high"]
    diff = line.price / avg - 1
    return {
        "matched": True,
        "basis": "menu",
        "item_id": None,
        "catalog_name": menu["name_en"] or menu["name_ko"],
        "catalog_unit": None,
        "quantity_ratio": 1.0,
        "seoul_avg": avg,
        "seoul_range": [menu["price_low"], menu["price_high"]],
        "seoul_diff_pct": round(diff * 100, 1),
        "compare_avg": avg,
        "compare_region": None,
        "diff_pct": round(diff * 100, 1),
        "verdict": verdict(diff),
        "district_avg": None,
        "district_prices": {},
        "cheapest_district": None,
        "store_count": menu["store_count"],
        "source": MENU_SOURCE,
        "reference_date": reference_date,
    }


def judge_line(
    line: ScannedLine,
    item: dict | None,
    districts: list[dict],
    district: str | None = None,
    menus: dict | None = None,
) -> dict:
    """한 줄 판정. districts: 그 품목의 구별 평균 [{region, region_name, price_avg}].
    district(지금 있는 구)를 주면 그 구 평균과 비교하고, 없거나 그 구 데이터가 없으면 서울 평균과 비교한다.
    DB 품목이 없으면 착한가격업소 메뉴(menus: {rows, districts, reference_date}) → Numbeo 순으로 찾고,
    그것도 없거나 비율이 이상하면 matched=False. 통역 필드(설명·매운 정도·재료)는 항상 붙인다."""
    out = {
        "name": line.name,
        "name_en": line.name_en,
        "price": line.price,
        "quantity": line.quantity,
        "description_en": line.description_en,
        "spice_level": line.spice_level,
        "contains": line.contains,
        "vegetarian": line.vegetarian,
        "matched": False,
    }
    ratio = line.quantity_ratio or 1.0
    if line.price <= 0 or not 0 < ratio <= 100:
        return out
    if item is None:
        menu = search_menus(line.name, menus["rows"], menus["districts"]) if menus else []
        if menu:
            out.update(judge_menu(line, menu[0], menus["reference_date"]))
            return out
        entry = load_reference()["entries"].get(line.reference_id) if line.reference_id else None
        if entry:
            out.update(judge_reference(line, entry, ratio))
        return out

    seoul_avg = round(item["price_avg"] * ratio)
    cheapest = min(districts, key=lambda d: d["price_avg"], default=None)
    here = next((d for d in districts if district and district in (d["region"], d["region_name"])), None)
    district_avg = round(here["price_avg"] * ratio) if here else None
    compare_avg = district_avg or seoul_avg
    diff = line.price / compare_avg - 1
    out.update(
        matched=True,
        basis="official",
        item_id=item["item_id"],
        catalog_name=item["name_ko"],
        catalog_unit=item["unit"],
        quantity_ratio=ratio,
        seoul_avg=seoul_avg,
        seoul_range=[round(item[k] * ratio) if item.get(k) else None for k in ("price_min", "price_max")],
        seoul_diff_pct=round((line.price / seoul_avg - 1) * 100, 1),
        compare_avg=compare_avg,
        compare_region=here["region_name"] if here else None,
        diff_pct=round(diff * 100, 1),
        verdict=verdict(diff),
        district_avg=district_avg,
        # 프론트에서 구를 바꾸면 Claude를 다시 부르지 않고 이 값으로 다시 판정한다
        district_prices={d["region_name"]: round(d["price_avg"] * ratio) for d in districts},
        cheapest_district=(
            {"region": cheapest["region"], "name": cheapest["region_name"], "price_avg": round(cheapest["price_avg"] * ratio)}
            if cheapest
            else None
        ),
        source=item["source"],
        reference_date=item["reference_date"],
    )
    return out


def summarize(lines: list[dict]) -> dict:
    """맞춘 줄들의 합계 비교. 사진 전체가 비교 기준(구 또는 서울) 평균보다 얼마나 비싼지."""
    matched = [line for line in lines if line["matched"]]
    if not matched:
        return {"matched_count": 0, "total_price": None, "total_avg": None, "diff_pct": None, "verdict": None}
    paid = sum(line["price"] for line in matched)
    avg = sum(line["compare_avg"] for line in matched)
    diff = paid / avg - 1
    return {
        "matched_count": len(matched),
        "total_price": paid,
        "total_avg": avg,
        "diff_pct": round(diff * 100, 1),
        "verdict": verdict(diff),
    }
