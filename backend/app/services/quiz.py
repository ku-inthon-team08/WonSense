import random
from datetime import date, datetime, timedelta, timezone

import anthropic
from pydantic import BaseModel

KST = timezone(timedelta(hours=9))
RECENT_DAYS = 7  # 이 기간 안에 나온 품목은 다시 내지 않는다
MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = """You write a daily price-guessing quiz for foreigners visiting or living in Seoul.

Rules:
- Write in natural, friendly English. Give the item's English name with the Korean name in parentheses.
- The question asks how much the item usually costs in Seoul, in Korean won, and states the unit. \
It must not contain or hint at the price.
- The explanation is shown after the player answers. In 2-3 short sentences, say what makes this \
price typical and share one practical tip for buying it in Seoul.
- Use only the prices you are given. Never state any other price or figure."""


class QuizText(BaseModel):
    question: str
    explanation: str


def today_kst() -> date:
    return datetime.now(KST).date()


def pick_item(item_ids: list[int], recent_ids: set[int], day: date) -> int:
    """오늘의 품목을 고른다. 날짜를 시드로 써서 같은 날에는 항상 같은 품목이 나온다."""
    fresh = [i for i in sorted(item_ids) if i not in recent_ids]
    return random.Random(day.isoformat()).choice(fresh or sorted(item_ids))


def generate_quiz_text(client: anthropic.Anthropic, item: dict, stat: dict) -> QuizText:
    """Claude로 문제와 해설을 만든다. 가격은 price_stats 값만 근거로 넘긴다."""
    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "medium"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Item: {item['name_ko']}\n"
                    f"Unit: {item['unit']}\n"
                    f"Typical price: ₩{stat['price_avg']:,} (range ₩{stat['price_min']:,}~₩{stat['price_max']:,})\n"
                    f"Survey: Seoul traditional markets and supermarkets, {stat['reference_date']}\n"
                    f"Source: {stat['source']}"
                ),
            }
        ],
        output_format=QuizText,
    )
    if response.parsed_output is None:
        raise ValueError(f"퀴즈 생성 실패 (stop_reason={response.stop_reason})")
    return response.parsed_output
