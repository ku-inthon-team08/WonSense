import base64
import binascii
import logging
from typing import Literal

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from supabase import Client

from app.db.supabase import get_supabase
from app.routers.items import get_items, get_menus
from app.core.claude import get_claude
from app.services.heatmap import SEOUL_REGION
from app.services.scan import extract_lines, judge_line, summarize

router = APIRouter(prefix="/api/scan", tags=["scan"])

logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # Claude 이미지 한 장 제한


class ScanRequest(BaseModel):
    # base64 문자열. 프론트에서 FileReader로 만든 data URL("data:image/jpeg;base64,...")도 받는다
    image: str = Field(..., min_length=1, max_length=8_000_000)
    media_type: Literal["image/jpeg", "image/png", "image/webp", "image/gif"] = "image/jpeg"
    district: str | None = Field(None, description="지금 있는 자치구 코드 또는 이름 (예: 마포구)")


def _decode(image: str) -> str:
    data = image.split(",", 1)[1] if image.startswith("data:") else image
    try:
        raw = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="이미지가 올바른 base64가 아닙니다")
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="이미지는 5MB 이하여야 합니다")
    return data


def _district_stats(supabase: Client, matched: list[dict]) -> dict[int, list[dict]]:
    """품목별 구 평균가 (각 품목의 최신 기준일 기준)."""
    if not matched:
        return {}
    rows = (
        supabase.table("price_stats")
        .select("item_id, region, region_name, price_avg, reference_date")
        .in_("item_id", [it["item_id"] for it in matched])
        .in_("reference_date", sorted({it["reference_date"] for it in matched}))
        .neq("region", SEOUL_REGION)
        .execute()
        .data
    )
    ref = {it["item_id"]: it["reference_date"] for it in matched}
    out: dict[int, list[dict]] = {}
    for r in rows:
        if r["reference_date"] == ref[r["item_id"]]:
            out.setdefault(r["item_id"], []).append(r)
    return out


@router.post("")
def scan(
    body: ScanRequest,
    items: list[dict] = Depends(get_items),
    menus: dict = Depends(get_menus),
    supabase: Client = Depends(get_supabase),
    claude: anthropic.Anthropic = Depends(get_claude),
) -> dict:
    """가격표·메뉴판·영수증 사진 한 장을 읽어 품목마다 평균가와 비교하고, 메뉴는 영어로 풀어 준다.
    verdict: cheap(10%↓ 저렴) / fair(±10%) / pricey(10~30% 비쌈) / ripoff(30%↑ 바가지)."""
    image = _decode(body.image)
    try:
        lines = extract_lines(claude, image, body.media_type, items)
    except (anthropic.APIError, ValueError) as e:
        logger.warning("사진 판독 실패: %s", e)
        raise HTTPException(status_code=502, detail="사진을 읽지 못했습니다. 다시 찍어 주세요")

    by_id = {it["item_id"]: it for it in items}
    matched = [by_id[line.item_id] for line in lines if line.item_id in by_id]
    districts = _district_stats(supabase, list({it["item_id"]: it for it in matched}.values()))

    results = [
        judge_line(line, by_id.get(line.item_id), districts.get(line.item_id, []), body.district, menus)
        for line in lines
    ]
    return {"lines": results, "summary": summarize(results)}
