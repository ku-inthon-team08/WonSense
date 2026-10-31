import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from postgrest.exceptions import APIError
from supabase import Client

from app.core.cache import TtlCache
from app.db.supabase import fetch_all, get_supabase
from app.services.heatmap import SEOUL_REGION
from app.services.menus import MENU_SOURCE, search_menus
from app.services.products import search_products
from app.services.restaurants import search_restaurant_prices
from app.services.search import english_name, is_restaurant_query, search_items, suggest

router = APIRouter(prefix="/api/items", tags=["items"])

logger = logging.getLogger(__name__)

PRODUCT_SOURCE = "한국소비자원 참가격 생필품 가격 (전국 마트·편의점)"
RESTAURANT_SOURCE = "웹 검색 기반 추정 (식당 목록: 카카오, 가격: Claude 웹 검색)"

_items = TtlCache()
_menus = TtlCache()
_products = TtlCache()
_restaurants = TtlCache()


def _load_items(supabase: Client) -> list[dict]:
    """품목마다 가장 최근 기준일의 서울 전체 행(price_stats region='seoul')을 붙여서 돌려준다."""
    rows = fetch_all(
        lambda: supabase.table("price_stats")
        .select(
            "item_id, price_min, price_avg, price_max, sample_count, source, reference_date, "
            "items(name_ko, name_en, aliases, category, unit)"
        )
        .eq("region", SEOUL_REGION)
        .order("reference_date", desc=True)
        .order("id")
    )

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
    return _items.get(lambda: _load_items(supabase))


def _cached_optional(cache: TtlCache, table: str, load: Callable[[], Any], empty: Any) -> Any:
    """마이그레이션 전이라 table이 없어도 나머지 검색은 되도록 빈 값으로 진행한다 (다음 요청에 다시 시도)."""
    try:
        return cache.get(load)
    except APIError as e:
        logger.warning("%s를 읽지 못했습니다: %s", table, e)
        return empty


def _load_menus(supabase: Client) -> dict:
    """식당 메뉴 가격 전체와 자치구 이름. 4천여 행이라 메모리에 두고 검색한다."""
    rows = fetch_all(
        lambda: supabase.table("menu_prices")
        .select("store_id, store_name, menu_name, industry, district_code, price, fetched_on")
        .order("store_id")
        .order("menu_name")
    )
    districts = {d["code"]: d["name_ko"] for d in supabase.table("districts").select("code, name_ko").execute().data}
    return {
        "rows": rows,
        "districts": districts,
        "reference_date": max((r["fetched_on"] for r in rows), default=None),
    }


def get_menus(supabase: Client = Depends(get_supabase)) -> dict:
    empty = {"rows": [], "districts": {}, "reference_date": None}
    return _cached_optional(_menus, "menu_prices", lambda: _load_menus(supabase), empty)


def _public(item: dict) -> dict:
    out = {k: v for k, v in item.items() if k != "aliases"}
    # 수집 데이터는 name_en에 한글이 들어 있으므로 사전으로 만든 영어 이름을 쓴다
    if out["name_en"] == out["name_ko"]:
        out["name_en"] = english_name(out["name_ko"])
    return out


def get_products(supabase: Client = Depends(get_supabase)) -> list[dict]:
    """마트·편의점 공산품 가격 요약 전체 (상품당 한 행, 600개 안팎)."""
    return _cached_optional(
        _products,
        "product_prices",
        lambda: fetch_all(lambda: supabase.table("product_prices").select("*").order("product_name")),
        [],
    )


def get_restaurants(supabase: Client = Depends(get_supabase)) -> list[dict]:
    """일반 식당 메뉴 가격 (LLM 웹 검색으로 수집, 출처 URL 포함)."""
    return _cached_optional(
        _restaurants,
        "restaurant_prices",
        lambda: fetch_all(lambda: supabase.table("restaurant_prices").select("*").order("place_id").order("menu")),
        [],
    )


@router.get("/search")
def search(
    q: str = Query(..., min_length=1, max_length=50, description="영어 또는 한국어 (예: soju, 소주)"),
    limit: int = Query(20, ge=1, le=50),
    items: list[dict] = Depends(get_items),
    menus: dict = Depends(get_menus),
    products: list[dict] = Depends(get_products),
    restaurants: list[dict] = Depends(get_restaurants),
) -> dict:
    """품목 검색.

    results: 장보기 품목. 가격은 서울 25개 자치구별 평균가의 최저~최고와 그 평균이다.
    menus: 식당 메뉴·서비스(착한가격업소 기준). 가격은 가게별 가격의 가운데 50% 범위와 중앙값이다.
    products: 마트·편의점 공산품(참가격, 전국). 가격은 판매점별 정상가의 가운데 50% 범위와 중앙값이다.
    web_menus: 일반 식당 메뉴(LLM 웹 검색 기반 추정). 식당별 가격의 가운데 50% 범위, 지역별 중앙값, 출처 링크.
    """
    hits = search_items(q, items, limit)
    menu_hits = search_menus(q, menus["rows"], menus["districts"])
    for m in menu_hits:
        m["source"] = MENU_SOURCE
        m["reference_date"] = menus["reference_date"]
    product_hits = [{**p, "source": PRODUCT_SOURCE} for p in search_products(q, products)]
    web_hits = [{**m, "source": RESTAURANT_SOURCE} for m in search_restaurant_prices(q, restaurants)]
    found = bool(hits or menu_hits or product_hits or web_hits)
    return {
        "query": q,
        "results": [_public(it) for it in hits],
        "menus": menu_hits,
        "products": product_hits,
        "web_menus": web_hits,
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
