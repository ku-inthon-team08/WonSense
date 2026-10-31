"""바가지 판독기: 가격표·영수증 사진을 읽어 서울 평균가와 비교한다.

Claude 호출 한 번으로 (1) 사진의 품목·가격을 읽고 (2) 우리 품목 목록 중 같은 품목을 고르고
(3) 사진의 수량이 기준 규격의 몇 배인지(quantity_ratio)를 정한다. 판정 계산은 코드에서 한다.

기준가는 두 가지다. 장보기 품목은 서울시 생필품 가격(DB)을 먼저 쓰고, DB에 없는 외식·교통·의류 등은
Numbeo 서울 생활물가(data/seoul_cost_of_living.json)로 추정한다.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel

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

Skip lines with no readable price, totals, tax, discounts, and payment lines. \
If the photo has no prices, return an empty list. Never invent items or prices."""


class ScannedLine(BaseModel):
    name: str
    name_en: str
    price: int
    quantity: str | None
    item_id: int | None
    reference_id: int | None = None
    quantity_ratio: float | None


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
        "diff_pct": round(diff * 100, 1),
        "verdict": verdict(diff),
        "district_avg": None,
        "cheapest_district": None,
        "source": ref["source"],
        "reference_date": ref["reference_date"],
    }


def judge_line(line: ScannedLine, item: dict | None, districts: list[dict], district: str | None = None) -> dict:
    """한 줄 판정. districts: 그 품목의 구별 평균 [{region, region_name, price_avg}].
    DB 품목이 없으면 Numbeo 기준가로 추정하고, 그것도 없거나 비율이 이상하면 matched=False."""
    out = {
        "name": line.name,
        "name_en": line.name_en,
        "price": line.price,
        "quantity": line.quantity,
        "matched": False,
    }
    ratio = line.quantity_ratio or 1.0
    if line.price <= 0 or not 0 < ratio <= 100:
        return out
    if item is None:
        entry = load_reference()["entries"].get(line.reference_id) if line.reference_id else None
        if entry:
            out.update(judge_reference(line, entry, ratio))
        return out

    seoul_avg = round(item["price_avg"] * ratio)
    diff = line.price / seoul_avg - 1
    cheapest = min(districts, key=lambda d: d["price_avg"], default=None)
    here = next((d for d in districts if district and district in (d["region"], d["region_name"])), None)
    out.update(
        matched=True,
        basis="official",
        item_id=item["item_id"],
        catalog_name=item["name_ko"],
        catalog_unit=item["unit"],
        quantity_ratio=ratio,
        seoul_avg=seoul_avg,
        seoul_range=[round(item[k] * ratio) if item.get(k) else None for k in ("price_min", "price_max")],
        diff_pct=round(diff * 100, 1),
        verdict=verdict(diff),
        district_avg=round(here["price_avg"] * ratio) if here else None,
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
    """맞춘 줄들의 합계 비교. 사진 전체가 평균보다 얼마나 비싼지."""
    matched = [line for line in lines if line["matched"]]
    if not matched:
        return {"matched_count": 0, "total_price": None, "total_seoul_avg": None, "diff_pct": None, "verdict": None}
    paid = sum(line["price"] for line in matched)
    avg = sum(line["seoul_avg"] for line in matched)
    diff = paid / avg - 1
    return {
        "matched_count": len(matched),
        "total_price": paid,
        "total_seoul_avg": avg,
        "diff_pct": round(diff * 100, 1),
        "verdict": verdict(diff),
    }
