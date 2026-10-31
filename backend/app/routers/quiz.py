from datetime import date, timedelta
from functools import lru_cache

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.config import get_settings
from app.db.supabase import get_supabase
from app.services.heatmap import SEOUL_REGION
from app.services.quiz import RECENT_DAYS, generate_quiz_text, pick_item, today_kst

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@lru_cache
def get_claude() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=get_settings().anthropic_api_key)


def _create_daily_quiz(supabase: Client, claude: anthropic.Anthropic, day: date) -> None:
    items = supabase.table("items").select("id, name_ko, unit").eq("quiz_enabled", True).execute().data
    if not items:
        raise HTTPException(status_code=404, detail="퀴즈 대상 품목이 없습니다")

    since = (day - timedelta(days=RECENT_DAYS)).isoformat()
    recent = supabase.table("daily_quizzes").select("item_id").gte("date", since).execute().data
    item_id = pick_item([i["id"] for i in items], {r["item_id"] for r in recent}, day)
    item = next(i for i in items if i["id"] == item_id)

    stats = (
        supabase.table("price_stats")
        .select("price_min, price_avg, price_max, source, reference_date")
        .eq("item_id", item_id)
        .eq("region", SEOUL_REGION)
        .order("reference_date", desc=True)
        .limit(1)
        .execute()
        .data
    )
    if not stats:
        raise HTTPException(status_code=404, detail="해당 품목의 가격 데이터가 없습니다")

    try:
        text = generate_quiz_text(claude, item, stats[0])
    except (anthropic.APIError, ValueError) as e:
        raise HTTPException(status_code=503, detail=f"퀴즈 생성 실패: {e}")

    # 동시 요청이 겹쳐도 먼저 저장된 문제 하나만 남긴다
    supabase.table("daily_quizzes").upsert(
        {
            "date": day.isoformat(),
            "item_id": item_id,
            "question": text.question,
            "answer_price": stats[0]["price_avg"],
            "explanation": text.explanation,
        },
        on_conflict="date",
        ignore_duplicates=True,
    ).execute()


def _load_daily_quiz(supabase: Client, day: date) -> dict | None:
    rows = (
        supabase.table("daily_quizzes")
        .select("date, question, items(name_ko, unit)")
        .eq("date", day.isoformat())
        .execute()
        .data
    )
    return rows[0] if rows else None


@router.get("/today")
def get_today_quiz(
    supabase: Client = Depends(get_supabase),
    claude: anthropic.Anthropic = Depends(get_claude),
) -> dict:
    """오늘의 문제. 하루 한 번만 생성해 저장하고, 정답과 해설은 응답에 넣지 않는다."""
    day = today_kst()
    quiz = _load_daily_quiz(supabase, day)
    if quiz is None:
        _create_daily_quiz(supabase, claude, day)
        quiz = _load_daily_quiz(supabase, day)

    return {
        "date": quiz["date"],
        "question": quiz["question"],
        "name": quiz["items"]["name_ko"],
        "unit": quiz["items"]["unit"],
    }
