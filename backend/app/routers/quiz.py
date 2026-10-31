import random
import time

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.db.supabase import get_supabase
from app.routers.items import get_menus
from app.services.heatmap import SEOUL_REGION
from app.services.quiz import QUIZ_TYPES, QuizType, build_guess, build_higher_lower, build_menu, menu_stats

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

PAGE = 1000
CACHE_TTL = 600  # 가격은 월 1회 갱신되므로 10분 캐시면 충분하다
_cache: dict = {"at": 0.0, "items": None, "menus_at": 0.0, "menus": None}


def _load_quiz_items(supabase: Client) -> list[dict]:
    """출제 대상 품목 + 최신 서울 평균가. 문제 문구와 팁은 items에 미리 넣어 둔 값을 쓴다."""
    items = (
        supabase.table("items")
        .select("id, quiz_name, quiz_question, tip_ko, quiz_tolerance_correct, quiz_tolerance_close")
        .eq("quiz_enabled", True)
        .not_.is_("quiz_question", "null")
        .execute()
        .data
    )
    stats: dict[int, dict] = {}
    start = 0
    while True:
        batch = (
            supabase.table("price_stats")
            .select("item_id, price_avg, source, reference_date")
            .eq("region", SEOUL_REGION)
            .order("reference_date", desc=True)
            .range(start, start + PAGE - 1)
            .execute()
            .data
        )
        for r in batch:
            stats.setdefault(r["item_id"], r)
        if len(batch) < PAGE:
            break
        start += PAGE

    return [
        {
            "item_id": i["id"],
            "quiz_name": i["quiz_name"],
            "quiz_question": i["quiz_question"],
            "tip": i["tip_ko"] or "",
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
    now = time.monotonic()
    if _cache["items"] is None or now - _cache["at"] > CACHE_TTL:
        _cache["items"] = _load_quiz_items(supabase)
        _cache["at"] = now
    return _cache["items"]


def get_menu_stats(menus: dict = Depends(get_menus)) -> list[dict]:
    now = time.monotonic()
    if _cache["menus"] is None or now - _cache["menus_at"] > CACHE_TTL:
        _cache["menus"] = menu_stats(menus["rows"])
        _cache["menus_at"] = now
    return _cache["menus"]


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
