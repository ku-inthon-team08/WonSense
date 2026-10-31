import random

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.cache import TtlCache
from app.db.supabase import fetch_all, get_supabase
from app.routers.items import get_menus
from app.services.heatmap import SEOUL_REGION
from app.services.quiz import (
    QUIZ_TYPES,
    QuizType,
    build_guess,
    build_higher_lower,
    build_menu,
    build_price_cards,
    menu_stats,
)

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

_items = TtlCache()
_menu_stats = TtlCache()


def _load_quiz_items(supabase: Client) -> list[dict]:
    """출제 대상 품목 + 최신 서울 평균가. 문제 문구와 팁은 items에 미리 넣어 둔 값을 쓴다."""
    items = (
        supabase.table("items")
        # quiz_name_en / tip_en은 20261101000900_quiz_english.sql에서 추가된다. 아직 적용 전인 DB에서도
        # 깨지지 않도록 *로 읽고 .get()으로 꺼낸다
        .select("*")
        .eq("quiz_enabled", True)
        .not_.is_("quiz_question", "null")
        .execute()
        .data
    )
    stats: dict[int, dict] = {}
    for r in fetch_all(
        lambda: supabase.table("price_stats")
        .select("item_id, price_avg, source, reference_date")
        .eq("region", SEOUL_REGION)
        .order("reference_date", desc=True)
        .order("id")
    ):
        stats.setdefault(r["item_id"], r)

    return [
        {
            "item_id": i["id"],
            "source_key": i.get("source_key"),
            "quiz_name": i["quiz_name"],
            "quiz_question": i["quiz_question"],
            "tip": i["tip_ko"] or "",
            "quiz_name_en": i.get("quiz_name_en"),
            "tip_en": i.get("tip_en"),
            "tolerance_correct": float(i["quiz_tolerance_correct"]),
            "tolerance_close": float(i["quiz_tolerance_close"]),
            "price_avg": stats[i["id"]]["price_avg"],
            "source": stats[i["id"]]["source"],
            "reference_date": stats[i["id"]]["reference_date"],
        }
        for i in items
        if i["id"] in stats and stats[i["id"]]["price_avg"] > 0
    ]


def get_quiz_items(supabase: Client = Depends(get_supabase)) -> list[dict]:
    return _items.get(lambda: _load_quiz_items(supabase))


def get_menu_stats(menus: dict = Depends(get_menus)) -> list[dict]:
    return _menu_stats.get(lambda: menu_stats(menus["rows"]))


@router.get("/random")
def get_random_quiz(
    type: QuizType | None = None,
    exclude: str | None = None,
    items: list[dict] = Depends(get_quiz_items),
    menus: list[dict] = Depends(get_menu_stats),
) -> dict:
    """랜덤 퀴즈 한 문제. type을 안 주면 세 유형 중 하나를 고른다.
    exclude: 직전 문제의 key (예: "item:9", "menu:김치찌개") — 같은 대상이 연속으로 나오지 않게."""
    rng = random.Random()
    needs = {"guess": len(items) >= 1, "higher_lower": len(items) >= 2, "menu": len(menus) >= 1}
    available = [t for t in QUIZ_TYPES if needs[t]]
    if type is not None and type not in available:
        raise HTTPException(status_code=404, detail="이 유형의 퀴즈 데이터가 없습니다")
    if not available:
        raise HTTPException(status_code=404, detail="퀴즈 대상 데이터가 없습니다")

    chosen = type or rng.choice(available)
    if chosen == "guess":
        return build_guess(items, exclude, rng)
    if chosen == "higher_lower":
        try:
            return build_higher_lower(items, exclude, rng)
        except ValueError:
            return build_guess(items, exclude, rng)
    return build_menu(menus, exclude, rng)


@router.get("/prices")
def get_price_cards(
    items: list[dict] = Depends(get_quiz_items),
    menus: list[dict] = Depends(get_menu_stats),
) -> dict:
    """가격 감 익히기: 장보기 품목과 식당 메뉴의 가격 카드. 최신 서울 평균가와 메뉴 중앙값이다."""
    return build_price_cards(items, menus)
