import random
import re
from typing import Literal

import anthropic
from pydantic import BaseModel

MODEL = "claude-haiku-5-5"

SYSTEM_PROMPT = """You write two short fields for a price-guessing quiz for foreigners in Seoul.

Rules:
- name_en: the item's short English name in lowercase, at most 4 words, with no price, number, \
size, or Korean. Example: "instant ramyeon".
- tip: one simple sentence of 12 words or fewer with a practical tip for buying this item in Seoul. \
It must not contain any number, spelled-out number, size, or price.
- Use only the data you are given. Do not invent facts about prices."""


class QuizText(BaseModel):
    name_en: str
    tip: str


def pick_random(item_ids: list[int], exclude: int | None = None) -> int:
    """랜덤 품목. 바로 직전 품목(exclude)은 가능하면 피한다."""
    pool = [i for i in item_ids if i != exclude] or item_ids
    return random.choice(pool)


def make_question(name_en: str, name_ko: str) -> str:
    return f"Guess how much {name_en} ({name_ko}) normally costs in Seoul?"


def grade(guess: int, avg: int, tol_correct: float, tol_close: float) -> Literal["right", "near", "wrong"]:
    error = abs(guess - avg) / avg
    if error <= tol_correct:
        return "right"
    return "near" if error <= tol_close else "wrong"


def is_valid_text(text: QuizText) -> bool:
    """LLM 출력이 형식을 지켰는지 확인한다. 어긋난 값은 캐시에 남기지 않는다."""
    name_ok = re.fullmatch(r"[a-z][a-z' -]*", text.name_en) and len(text.name_en.split()) <= 4
    tip_ok = text.tip and not re.search(r"[\d₩]", text.tip) and len(text.tip.split()) <= 20
    return bool(name_ok and tip_ok)


def fallback_quiz_text(item: dict) -> QuizText:
    """Claude 호출이 실패해도 퀴즈는 계속 나가도록 하는 고정 문구 (캐시하지 않음)."""
    return QuizText(name_en=item["name_ko"], tip="")


def generate_quiz_text(client: anthropic.Anthropic, item: dict) -> QuizText:
    """Claude로 영어 이름과 팁을 만든다. 가격이 새지 않도록 가격 정보는 넘기지 않는다."""
    response = client.messages.parse(
        model=MODEL,
        max_tokens=1024,
        output_config={"effort": "low"},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Item: {item['name_ko']}\n"
                    f"Unit: {item['unit']}\n"
                    "Sold at: Seoul traditional markets and supermarkets"
                ),
            }
        ],
        output_format=QuizText,
    )
    text = response.parsed_output
    if text is None or not is_valid_text(text):
        raise ValueError(f"퀴즈 생성 실패 (stop_reason={response.stop_reason})")
    return text
