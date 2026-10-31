import time

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from app.db.supabase import get_supabase
from app.services.heatmap import SEOUL_REGION
from app.services.search import english_name, is_restaurant_query, search_items, suggest

router = APIRouter(prefix="/api/items", tags=["items"])

PAGE = 1000
CACHE_TTL = 600  # 가격은 월 1회 갱신되므로 10분 캐시면 충분하다
_cache: dict = {"at": 0.0, "items": None}


def _load_items(supabase: Client) -> list[dict]:
    """품목마다 가장 최근 기준일의 서울 전체 행(price_stats region='seoul')을 붙여서 돌려준다."""
    rows: list[dict] = []
    start = 0
    while True:
        batch = (
            supabase.table("price_stats")
            .select(
                "item_id, price_min, price_avg, price_max, sample_count, source, reference_date, "
                "items(name_ko, name_en, aliases, category, unit)"
            )
            .eq("region", SEOUL_REGION)
            .order("reference_date", desc=True)
            .range(start, start + PAGE - 1)
            .execute()
            .data
        )
        rows.extend(batch)
        if len(batch) < PAGE:
            break
        start += PAGE

    latest: dict[int, dict] = {}
    for r in rows:
        if r.get("items") and r["item_id"] not in latest:
            latest[r["item_id"]] = r
    return [
        {
            "item_id": item_id,
            "name_ko": r["items"]["name_ko"],
            "name_en": r["items"]["name_en"],
            "aliases": r["items"].get("aliases") or [],
            "category": r["items"]["category"],
            "unit": r["items"]["unit"],
            "price_min": r["price_min"],
            "price_avg": r["price_avg"],
            "price_max": r["price_max"],
            "district_count": r["sample_count"],
            "source": r["source"],
            "reference_date": r["reference_date"],
        }
        for item_id, r in latest.items()
    ]


def get_items(supabase: Client = Depends(get_supabase)) -> list[dict]:
    now = time.monotonic()
    if _cache["items"] is None or now - _cache["at"] > CACHE_TTL:
        _cache["items"] = _load_items(supabase)
        _cache["at"] = now
    return _cache["items"]


def _public(item: dict) -> dict:
    out = {k: v for k, v in item.items() if k != "aliases"}
    # 수집 데이터는 name_en에 한글이 들어 있으므로 사전으로 만든 영어 이름을 쓴다
    if out["name_en"] == out["name_ko"]:
        out["name_en"] = english_name(out["name_ko"])
    return out


@router.get("/search")
def search(
    q: str = Query(..., min_length=1, max_length=50, description="영어 또는 한국어 (예: soju, 소주)"),
    limit: int = Query(20, ge=1, le=50),
    items: list[dict] = Depends(get_items),
) -> dict:
    """품목 검색. 가격은 서울 25개 자치구별 평균가의 최저~최고와 그 평균이다."""
    hits = search_items(q, items, limit)
    return {
        "query": q,
        "results": [_public(it) for it in hits],
        "suggestions": [] if hits else suggest(q, items),
        # 외식 메뉴·교통비는 아직 데이터가 없다는 안내용
        "not_covered": not hits and is_restaurant_query(q),
    }


@router.get("/{item_id}")
def get_item(item_id: int, items: list[dict] = Depends(get_items)) -> dict:
    item = next((it for it in items if it["item_id"] == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없습니다")
    return _public(item)
