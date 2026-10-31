from functools import lru_cache

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.config import get_settings
from app.db.supabase import get_supabase
from app.services.heatmap import SEOUL_REGION
from app.services.quiz import QuizText, fallback_quiz_text, generate_quiz_text, make_question, pick_random

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@lru_cache
def get_claude() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=get_settings().anthropic_api_key)


def _latest_seoul_stats(supabase: Client, item_ids: list[int]) -> dict[int, dict]:
    rows = (
        supabase.table("price_stats")
        .select("item_id, price_avg, source, reference_date")
        .in_("item_id", item_ids)
        .eq("region", SEOUL_REGION)
        .order("reference_date", desc=True)
        .execute()
        .data
    )
    latest: dict[int, dict] = {}
    for r in rows:
        latest.setdefault(r["item_id"], r)
    return latest


def _quiz_text(supabase: Client, claude: anthropic.Anthropic, item: dict, stat: dict) -> QuizText:
    """캐시에 있으면 그대로 쓰고, 없으면 Claude로 만들어 저장한다. 실패하면 고정 문구."""
    cached = (
        supabase.table("quiz_texts")
        .select("name_en, tip")
        .eq("item_id", item["id"])
        .eq("reference_date", stat["reference_date"])
        .execute()
        .data
    )
    if cached:
        return QuizText(**cached[0])

    try:
        text = generate_quiz_text(claude, item)
    except (anthropic.APIError, ValueError):
        return fallback_quiz_text(item)

    supabase.table("quiz_texts").upsert(
        {
            "item_id": item["id"],
            "reference_date": stat["reference_date"],
            "name_en": text.name_en,
            "tip": text.tip,
        },
        on_conflict="item_id,reference_date",
        ignore_duplicates=True,
    ).execute()
    return text


@router.get("/random")
def get_random_quiz(
    exclude: int | None = None,
    supabase: Client = Depends(get_supabase),
    claude: anthropic.Anthropic = Depends(get_claude),
) -> dict:
    """랜덤 퀴즈 한 문제. 로그인이 없으므로 정답과 팁을 함께 보내고 채점은 프론트에서 한다.
    exclude: 직전 품목 id (같은 문제가 연속으로 나오지 않게)."""
    items = (
        supabase.table("items")
        .select("id, name_ko, unit, quiz_tolerance_correct, quiz_tolerance_close")
        .eq("quiz_enabled", True)
        .execute()
        .data
    )
    stats = _latest_seoul_stats(supabase, [i["id"] for i in items]) if items else {}
    candidates = [i for i in items if i["id"] in stats]
    if not candidates:
        raise HTTPException(status_code=404, detail="퀴즈 대상 품목이 없습니다")

    item_id = pick_random([i["id"] for i in candidates], exclude)
    item = next(i for i in candidates if i["id"] == item_id)
    stat = stats[item_id]
    text = _quiz_text(supabase, claude, item, stat)

    return {
        "item_id": item_id,
        "name_ko": item["name_ko"],
        "name_en": text.name_en,
        "unit": item["unit"],
        "question": make_question(text.name_en, item["name_ko"]),
        "answer_price": stat["price_avg"],
        "tolerance_correct": float(item["quiz_tolerance_correct"]),
        "tolerance_close": float(item["quiz_tolerance_close"]),
        "tip": text.tip,
        "source": stat["source"],
        "reference_date": stat["reference_date"],
    }
