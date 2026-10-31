from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from app.core.cache import TtlCache
from app.db.supabase import fetch_all, get_supabase
from app.services.heatmap import SEOUL_REGION, build_heatmap

router = APIRouter(prefix="/api/heatmap", tags=["heatmap"])

_latest = TtlCache()  # 최신 기준일의 스냅샷. 홈 화면마다 부르는 API라 요청마다 DB를 읽지 않는다


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


def _load_snapshot(supabase: Client, ref: str) -> dict:
    """한 기준일의 price_stats 전체 (구별 행 + 서울 행). 세 API가 이 행들을 걸러서 쓴다."""
    rows = fetch_all(
        lambda: supabase.table("price_stats")
        .select("item_id, region, region_name, price_avg, source, items(name_ko, unit)")
        .eq("reference_date", ref)
        .order("id")
    )
    return {"reference_date": ref, "rows": rows}


def get_snapshot(
    reference_date: str | None = Query(None, description="YYYY-MM-DD, 없으면 최신 기준일"),
    supabase: Client = Depends(get_supabase),
) -> dict:
    if reference_date:
        return _load_snapshot(supabase, reference_date)

    def load_latest() -> dict:
        ref = _latest_reference_date(supabase)
        if ref is None:
            raise HTTPException(status_code=404, detail="가격 데이터가 아직 없습니다")
        return _load_snapshot(supabase, ref)

    return _latest.get(load_latest)


@router.get("")
def get_heatmap(
    item_id: int | None = Query(None, description="없으면 전체 지수"),
    snapshot: dict = Depends(get_snapshot),
) -> dict:
    rows = [r for r in snapshot["rows"] if r["region"] != SEOUL_REGION and item_id in (None, r["item_id"])]
    if not rows:
        raise HTTPException(status_code=404, detail="해당 조건의 가격 데이터가 없습니다")

    return {
        "item_id": item_id,
        "reference_date": snapshot["reference_date"],
        "source": rows[0]["source"],
        **build_heatmap(rows),
    }


@router.get("/items")
def get_heatmap_items(snapshot: dict = Depends(get_snapshot)) -> dict:
    """품목 선택 목록: 기준일에 서울 평균가가 있는 품목들 (이름순)."""
    items = [
        {"item_id": r["item_id"], "name": r["items"]["name_ko"], "unit": r["items"]["unit"], "seoul_avg": r["price_avg"]}
        for r in snapshot["rows"]
        if r["region"] == SEOUL_REGION and r.get("items")
    ]
    return {"reference_date": snapshot["reference_date"], "items": sorted(items, key=lambda i: i["name"])}


@router.get("/districts/{region}")
def get_district_detail(region: str, snapshot: dict = Depends(get_snapshot)) -> dict:
    """구 상세 패널: 품목별 구 평균가와 서울 평균 대비 차이(%)."""
    seoul = {r["item_id"]: r for r in snapshot["rows"] if r["region"] == SEOUL_REGION}
    mine = [r for r in snapshot["rows"] if r["region"] == region]
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
        "reference_date": snapshot["reference_date"],
        "items": sorted(items, key=lambda i: i["diff_pct"], reverse=True),
    }
