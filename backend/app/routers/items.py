import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from postgrest.exceptions import APIError
from supabase import Client

from app.db.supabase import get_supabase
from app.services.heatmap import SEOUL_REGION
from app.services.menus import search_menus
from app.services.products import search_products
from app.services.search import english_name, is_restaurant_query, search_items, suggest

router = APIRouter(prefix="/api/items", tags=["items"])

logger = logging.getLogger(__name__)

PAGE = 1000
CACHE_TTL = 600  # 가격은 월 1회 갱신되므로 10분 캐시면 충분하다
_cache: dict = {"at": 0.0, "items": None}
MENU_SOURCE = "서울시 가격안정 모범업소(착한가격업소) 상품목록"
PRODUCT_SOURCE = "한국소비자원 참가격 생필품 가격 (전국 마트·편의점)"


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


_menu_cache: dict = {"at": 0.0, "data": None}


def _load_menus(supabase: Client) -> dict:
    """식당 메뉴 가격 전체와 자치구 이름. 4천여 행이라 메모리에 두고 검색한다."""
    rows: list[dict] = []
    start = 0
    while True:
        batch = (
            supabase.table("menu_prices")
            .select("store_id, store_name, menu_name, industry, district_code, price, fetched_on")
            .range(start, start + PAGE - 1)
            .execute()
            .data
        )
        rows.extend(batch)
        if len(batch) < PAGE:
            break
        start += PAGE
    districts = {d["code"]: d["name_ko"] for d in supabase.table("districts").select("code, name_ko").execute().data}
    return {
        "rows": rows,
        "districts": districts,
        "reference_date": max((r["fetched_on"] for r in rows), default=None),
    }


def get_menus(supabase: Client = Depends(get_supabase)) -> dict:
    now = time.monotonic()
    if _menu_cache["data"] is None or now - _menu_cache["at"] > CACHE_TTL:
        try:
            _menu_cache["data"] = _load_menus(supabase)
        except APIError as e:
            # menu_prices 마이그레이션 전이어도 장보기 검색은 되도록 메뉴 없이 진행한다 (다음 요청에 다시 시도)
            logger.warning("menu_prices를 읽지 못했습니다: %s", e)
            return {"rows": [], "districts": {}, "reference_date": None}
        _menu_cache["at"] = now
    return _menu_cache["data"]


def _public(item: dict) -> dict:
    out = {k: v for k, v in item.items() if k != "aliases"}
    # 수집 데이터는 name_en에 한글이 들어 있으므로 사전으로 만든 영어 이름을 쓴다
    if out["name_en"] == out["name_ko"]:
        out["name_en"] = english_name(out["name_ko"])
    return out


_product_cache: dict = {"at": 0.0, "data": None}


def _load_products(supabase: Client) -> list[dict]:
    """마트·편의점 공산품 가격 요약 전체 (상품당 한 행, 600개 안팎)."""
    rows: list[dict] = []
    start = 0
    while True:
        batch = supabase.table("product_prices").select("*").range(start, start + PAGE - 1).execute().data
        rows.extend(batch)
        if len(batch) < PAGE:
            break
        start += PAGE
    return rows


def get_products(supabase: Client = Depends(get_supabase)) -> list[dict]:
    now = time.monotonic()
    if _product_cache["data"] is None or now - _product_cache["at"] > CACHE_TTL:
        try:
            _product_cache["data"] = _load_products(supabase)
        except APIError as e:
            # product_prices 마이그레이션 전이어도 나머지 검색은 되도록 상품 없이 진행한다
            logger.warning("product_prices를 읽지 못했습니다: %s", e)
            return []
        _product_cache["at"] = now
    return _product_cache["data"]


@router.get("/search")
def search(
    q: str = Query(..., min_length=1, max_length=50, description="영어 또는 한국어 (예: soju, 소주)"),
    limit: int = Query(20, ge=1, le=50),
    items: list[dict] = Depends(get_items),
    menus: dict = Depends(get_menus),
    products: list[dict] = Depends(get_products),
) -> dict:
    """품목 검색.

    results: 장보기 품목. 가격은 서울 25개 자치구별 평균가의 최저~최고와 그 평균이다.
    menus: 식당 메뉴·서비스(착한가격업소 기준). 가격은 가게별 가격의 가운데 50% 범위와 중앙값이다.
    products: 마트·편의점 공산품(참가격, 전국). 가격은 판매점별 정상가의 가운데 50% 범위와 중앙값이다.
    """
    hits = search_items(q, items, limit)
    menu_hits = search_menus(q, menus["rows"], menus["districts"])
    for m in menu_hits:
        m["source"] = MENU_SOURCE
        m["reference_date"] = menus["reference_date"]
    product_hits = [{**p, "source": PRODUCT_SOURCE} for p in search_products(q, products)]
    found = bool(hits or menu_hits or product_hits)
    return {
        "query": q,
        "results": [_public(it) for it in hits],
        "menus": menu_hits,
        "products": product_hits,
        "suggestions": [] if found else suggest(q, items),
        # 교통비 등 아직 데이터가 없는 외식/서비스 검색어 안내용
        "not_covered": not found and is_restaurant_query(q),
    }


@router.get("/{item_id}")
def get_item(item_id: int, items: list[dict] = Depends(get_items)) -> dict:
    item = next((it for it in items if it["item_id"] == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없습니다")
    return _public(item)
