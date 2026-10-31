"""바가지 판독기: 가격표·영수증 사진을 읽어 서울 평균가와 비교한다.

Claude 호출 한 번으로 (1) 사진의 품목·가격을 읽고 (2) 우리 품목 목록 중 같은 품목을 고르고
(3) 사진의 수량이 DB 규격의 몇 배인지(quantity_ratio)를 정한다. 판정 계산은 코드에서 한다.
"""
from typing import Literal

import anthropic
from pydantic import BaseModel

MODEL = "claude-opus-5-5"

FAIR_BAND = 0.10  # 평균 ±10%는 적정가
RIPOFF = 0.30  # 평균보다 30% 넘게 비싸면 바가지

SYSTEM_PROMPT = """You read photos of price tags, market signs, menus, and receipts taken in Seoul \
and match each priced item to a fixed catalog of grocery items.

For every item in the photo that shows a price, return one line:
- name: the item name exactly as written in the photo (Korean if it is Korean).
- name_en: a short English name, lowercase, at most 4 words.
- price: the price in won as an integer, for the quantity shown in the photo.
- quantity: the quantity or size written in the photo (e.g. "30구", "1kg", "2개"), or null.
- item_id: the id of the catalog item that is the same product, or null if nothing matches. \
Different varieties of the same product (e.g. two rice brands) still match. \
Restaurant dishes do not match grocery items.
- quantity_ratio: how many catalog units the photo's quantity equals. Example: photo "계란 30구" \
and catalog "계란 10개" gives 3. Use 1 when the sizes are the same or the photo shows no size. \
null when item_id is null.

Skip lines with no readable price, totals, tax, discounts, and payment lines. \
If the photo has no prices, return an empty list. Never invent items or prices."""


class ScannedLine(BaseModel):
    name: str
    name_en: str
    price: int
    quantity: str | None
    item_id: int | None
    quantity_ratio: float | None


class ScanOutput(BaseModel):
    lines: list[ScannedLine]


Verdict = Literal["cheap", "fair", "pricey", "ripoff"]


def catalog_text(items: list[dict]) -> str:
    """시스템 프롬프트 뒤에 붙이는 품목 목록. 순서를 고정해 프롬프트 캐시가 깨지지 않게 한다."""
    rows = sorted(items, key=lambda it: it["item_id"])
    return "Catalog (id | name | unit):\n" + "\n".join(f"{it['item_id']} | {it['name_ko']} | {it['unit']}" for it in rows)


def extract_lines(client: anthropic.Anthropic, image_b64: str, media_type: str, items: list[dict]) -> list[ScannedLine]:
    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "low"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
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


def judge_line(line: ScannedLine, item: dict | None, districts: list[dict], district: str | None = None) -> dict:
    """한 줄 판정. districts: 그 품목의 구별 평균 [{region, region_name, price_avg}].
    item이 없거나 비율이 이상하면 비교하지 않고 matched=False로 돌려준다."""
    out = {
        "name": line.name,
        "name_en": line.name_en,
        "price": line.price,
        "quantity": line.quantity,
        "matched": False,
    }
    ratio = line.quantity_ratio or 1.0
    if item is None or line.price <= 0 or not 0 < ratio <= 100:
        return out

    seoul_avg = round(item["price_avg"] * ratio)
    diff = line.price / seoul_avg - 1
    cheapest = min(districts, key=lambda d: d["price_avg"], default=None)
    here = next((d for d in districts if district and district in (d["region"], d["region_name"])), None)
    out.update(
        matched=True,
        item_id=item["item_id"],
        catalog_name=item["name_ko"],
        catalog_unit=item["unit"],
        quantity_ratio=ratio,
        seoul_avg=seoul_avg,
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
