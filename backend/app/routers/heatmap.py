from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from app.db.supabase import get_supabase
from app.services.heatmap import SEOUL_REGION, build_heatmap

router = APIRouter(prefix="/api/heatmap", tags=["heatmap"])

PAGE = 1000  # Supabase 응답 기본 행 제한


def _latest_reference_date(supabase: Client) -> str | None:
    res = (
        supabase.table("price_stats")
        .select("reference_date")
        .neq("region", SEOUL_REGION)
        .order("reference_date", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0]["reference_date"] if res.data else None


@router.get("")
def get_heatmap(
    item_id: int | None = Query(None, description="없으면 전체 지수"),
    reference_date: str | None = Query(None, description="YYYY-MM-DD, 없으면 최신 기준일"),
    supabase: Client = Depends(get_supabase),
) -> dict:
    ref = reference_date or _latest_reference_date(supabase)
    if ref is None:
        raise HTTPException(status_code=404, detail="가격 데이터가 아직 없습니다")

    rows: list[dict] = []
    start = 0
    while True:
        query = (
            supabase.table("price_stats")
            .select("item_id, region, region_name, price_avg, source")
            .neq("region", SEOUL_REGION)
            .eq("reference_date", ref)
            .range(start, start + PAGE - 1)
        )
        if item_id is not None:
            query = query.eq("item_id", item_id)
        batch = query.execute().data
        rows.extend(batch)
        if len(batch) < PAGE:
            break
        start += PAGE

    if not rows:
        raise HTTPException(status_code=404, detail="해당 조건의 가격 데이터가 없습니다")

    return {
        "item_id": item_id,
        "reference_date": ref,
        "source": rows[0]["source"],
        **build_heatmap(rows),
    }


@router.get("/districts/{region}")
def get_district_detail(
    region: str,
    reference_date: str | None = Query(None),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """구 상세 패널: 품목별 구 평균가와 서울 평균 대비 차이(%)."""
    ref = reference_date or _latest_reference_date(supabase)
    if ref is None:
        raise HTTPException(status_code=404, detail="가격 데이터가 아직 없습니다")

    rows: list[dict] = []
    start = 0
    while True:
        batch = (
            supabase.table("price_stats")
            .select("item_id, price_avg, items(name_ko, unit)")
            .eq("region", SEOUL_REGION)
            .eq("reference_date", ref)
            .range(start, start + PAGE - 1)
            .execute()
            .data
        )
        rows.extend(batch)
        if len(batch) < PAGE:
            break
        start += PAGE
    seoul = {r["item_id"]: r for r in rows}

    mine = (
        supabase.table("price_stats")
        .select("item_id, region_name, price_avg")
        .eq("region", region)
        .eq("reference_date", ref)
        .execute()
        .data
    )
    if not mine:
        raise HTTPException(status_code=404, detail="해당 구의 데이터가 없습니다")

    items = []
    for m in mine:
        s = seoul.get(m["item_id"])
        if not s or s["price_avg"] <= 0:
            continue
        items.append(
            {
                "item_id": m["item_id"],
                "name": s["items"]["name_ko"],
                "unit": s["items"]["unit"],
                "price_avg": m["price_avg"],
                "seoul_avg": s["price_avg"],
                "diff_pct": round((m["price_avg"] / s["price_avg"] - 1) * 100, 1),
            }
        )
    return {
        "region": region,
        "name": mine[0]["region_name"],
        "reference_date": ref,
        "items": sorted(items, key=lambda i: i["diff_pct"], reverse=True),
    }
