"""F2 물가 퀴즈. LLM 없이 DB 값과 고정 문구만으로 문제를 만든다.

문제 유형 3가지 (로그인이 없으므로 정답을 같이 보내고 채점은 프론트에서 한다):
- guess:        장보기 품목의 서울 평균 가격 맞히기 (items.quiz_question, price_stats)
- higher_lower: 두 품목 중 어느 쪽이 더 비싼지 (price_stats)
- menu:         착한가격업소 메뉴 가격이 '보통'인지 '비싼 편'인지 (menu_prices, F1 검색과 같은 기준)

빌더 함수는 순수 함수라서 random.Random을 넘겨 테스트할 수 있다.
"""
import random
from typing import Literal

from app.services.menus import MENU_DICT, contains_any, price_stats, round_to

QuizType = Literal["guess", "higher_lower", "menu"]
QUIZ_TYPES: tuple[QuizType, ...] = ("guess", "higher_lower", "menu")

HL_MIN_GAP = 0.15  # 더 비쌀까? 문제에서 두 가격이 이 비율보다 가까우면 고르지 않는다 (찍기 방지)
MENU_MIN_STORES = 20  # 메뉴 퀴즈는 가게가 이만큼 이상 조사된 메뉴만 쓴다
MENU_SOURCE = "서울시 착한가격업소 기준"
FOOD_INDUSTRIES = {"한식", "중식", "경양식/일식", "기타외식업"}
NON_FOOD_MENUS = {"커트", "파마", "염색"}
# 가격 감 익히기에서 "이 돈이면 몇 개"로 보여줄 익숙한 기준 품목
ANCHOR_ITEMS = {"생수 500ml 1병", "소주 360ml, 1병", "맥주 500ml 1캔", "계란 10개"}
ANCHOR_MENUS = {"아메리카노", "김밥", "김치찌개", "삼겹살"}


def _pick(pool: list, key, exclude: str | None, rng: random.Random):
    """직전 문제(exclude)와 같은 대상은 가능하면 피한다."""
    fresh = [p for p in pool if key(p) != exclude] or pool
    return rng.choice(fresh)


def build_guess(items: list[dict], exclude: str | None, rng: random.Random) -> dict:
    item = _pick(items, lambda i: f"item:{i['item_id']}", exclude, rng)
    return {
        "type": "guess",
        "key": f"item:{item['item_id']}",
        "item_id": item["item_id"],
        "quiz_name": item["quiz_name"],
        "quiz_name_en": item.get("quiz_name_en"),  # 영어 문제 문장은 프론트가 이 이름으로 만든다
        "question": item["quiz_question"],
        "answer_price": item["price_avg"],
        "tolerance_correct": item["tolerance_correct"],
        "tolerance_close": item["tolerance_close"],
        "tip": item["tip"],
        "tip_en": item.get("tip_en"),
        "source": item["source"],
        "reference_date": item["reference_date"],
    }


def build_higher_lower(items: list[dict], exclude: str | None, rng: random.Random) -> dict:
    """기준 품목(가격 공개)과 대상 품목(가격 숨김). 가격 차이가 HL_MIN_GAP 이상인 쌍만 고른다."""
    for _ in range(50):
        base, target = rng.sample(items, 2)
        gap = abs(target["price_avg"] - base["price_avg"]) / min(target["price_avg"], base["price_avg"])
        if gap >= HL_MIN_GAP and f"item:{target['item_id']}" != exclude:
            break
    else:
        raise ValueError("가격 차이가 충분한 품목 쌍을 찾지 못했습니다")

    def public(i: dict) -> dict:
        return {"item_id": i["item_id"], "name": i["quiz_name"], "name_en": i.get("quiz_name_en"), "price": i["price_avg"]}

    return {
        "type": "higher_lower",
        "key": f"item:{target['item_id']}",
        # '의'와 '보다'는 받침과 상관없이 붙어서 조사 처리가 필요 없다
        "question": f"{target['quiz_name']}의 가격은 {base['quiz_name']}({base['price_avg']:,}원)보다 비쌀까요, 쌀까요?",
        "base": public(base),
        "target": public(target),
        "answer": "higher" if target["price_avg"] > base["price_avg"] else "lower",
        "source": target["source"],
        "reference_date": target["reference_date"],
    }


def menu_stats(rows: list[dict]) -> list[dict]:
    """F1 검색과 같은 메뉴 묶음(MENU_DICT)과 같은 '보통' 기준(가운데 50%)으로 메뉴별 가격 분포를 낸다."""
    food = [r for r in rows if r.get("industry") in FOOD_INDUSTRIES and r.get("price", 0) > 0]
    out = []
    for key, (_en, spellings, _aliases) in MENU_DICT.items():
        if key in NON_FOOD_MENUS:
            continue
        prices = [r["price"] for r in food if contains_any(r["menu_name"], spellings)]
        if len(prices) >= MENU_MIN_STORES:
            out.append({"menu_name": key, **price_stats(prices)})
    return out


def build_price_cards(items: list[dict], menus: list[dict]) -> dict:
    """가격 감 익히기(금액 슬라이더·가격 사다리)에 쓰는 카드. 채점이 없어서 한 번 받아 브라우저에서 돌린다.
    100g 단위 품목은 "이 돈이면 몇 개"로 읽히지 않아서 뺀다."""
    groceries = [i for i in items if "100g" not in i["quiz_name"]]
    cards = [
        {
            "key": f"item:{i['item_id']}",
            "kind": "grocery",
            "name": i["quiz_name"],
            "name_en": i.get("quiz_name_en"),
            "price": i["price_avg"],
            "anchor": i.get("source_key") in ANCHOR_ITEMS,
            "tip": i["tip"] or None,
            "tip_en": i.get("tip_en"),
        }
        for i in groceries
    ]
    cards += [
        {
            "key": f"menu:{m['menu_name']}",
            "kind": "dish",
            "name": m["menu_name"],
            "name_en": MENU_DICT[m["menu_name"]][0],
            "price": m["price_median"],
            "anchor": m["menu_name"] in ANCHOR_MENUS,
            "tip": None,
            "tip_en": None,
        }
        for m in menus
    ]
    return {"cards": cards, "reference_date": max((i["reference_date"] for i in groceries), default=None)}


def build_menu(stats: list[dict], exclude: str | None, rng: random.Random) -> dict:
    """반반 확률로 '보통'(가운데 50% 범위 안) 또는 '비싼 편'(위쪽 경계보다 20~60% 비싼) 가격을 보여준다."""
    m = _pick(stats, lambda s: f"menu:{s['menu_name']}", exclude, rng)
    low, high = m["price_low"], m["price_high"]
    if rng.random() < 0.5:
        shown = round_to(rng.uniform(low, high), 500)
        if not low <= shown <= high:
            shown = round_to(rng.uniform(low, high), 100)
        answer = "normal"
    else:
        shown = max(round_to(high * rng.uniform(1.2, 1.6), 500), high + 500)
        answer = "above"
    return {
        "type": "menu",
        "key": f"menu:{m['menu_name']}",
        "menu_name": m["menu_name"],
        "menu_name_en": MENU_DICT[m["menu_name"]][0],
        "question": f"착한가격업소에서 {m['menu_name']} {shown:,}원, 보통 가격일까요 비싼 편일까요?",
        "shown_price": shown,
        "median_price": m["price_median"],
        "normal_low": low,
        "normal_high": high,
        "store_count": m["count"],
        "answer": answer,
        "source": MENU_SOURCE,
    }
