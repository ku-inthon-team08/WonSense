import random

import anthropic
from pydantic import BaseModel

MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = """You write a price-guessing quiz for foreigners visiting or living in Seoul.

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


def pick_random(item_ids: list[int], exclude: int | None = None) -> int:
    """랜덤 품목. 바로 직전 품목(exclude)은 가능하면 피한다."""
    pool = [i for i in item_ids if i != exclude] or item_ids
    return random.choice(pool)


def is_correct(guess: int, answer: int, tolerance: float) -> bool:
    return abs(guess - answer) / answer <= tolerance


def fallback_quiz_text(item: dict) -> QuizText:
    """Claude 호출이 실패해도 퀴즈는 계속 나가도록 하는 고정 문구 (캐시하지 않음)."""
    return QuizText(
        question=f"Guess the average price in Seoul: {item['name_ko']} ({item['unit']})",
        explanation="Prices are averages from Seoul traditional markets and supermarkets.",
    )


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
