import random

from app.services.quiz import (
    HL_MIN_GAP,
    build_guess,
    build_higher_lower,
    build_menu,
    grade,
    menu_stats,
)

ITEMS = [
    {
        "item_id": i,
        "quiz_name": name,
        "quiz_question": f"서울에서 {name}의 평균 가격은 얼마일까요?",
        "tip": "팁",
        "tolerance_correct": 0.10,
        "tolerance_close": 0.25,
        "price_avg": price,
        "source": "src",
        "reference_date": "2026-10-26",
    }
    for i, (name, price) in enumerate(
        [("계란 10개", 4142), ("우유 1L", 3159), ("맥주 500ml 1캔", 2309), ("생수 500ml", 600), ("라면 5개 묶음", 4434)],
        start=1,
    )
]


def test_grade_right_near_wrong_in_both_directions():
    assert grade(1050, 1000, 0.10, 0.25) == "right"
    assert grade(950, 1000, 0.10, 0.25) == "right"
    assert grade(1200, 1000, 0.10, 0.25) == "near"
    assert grade(800, 1000, 0.10, 0.25) == "near"
    assert grade(1400, 1000, 0.10, 0.25) == "wrong"
    assert grade(600, 1000, 0.10, 0.25) == "wrong"


def test_guess_uses_premade_question_and_skips_previous_item():
    for seed in range(30):
        q = build_guess(ITEMS, "item:1", random.Random(seed))
        assert q["type"] == "guess" and q["item_id"] != 1
        assert q["question"].startswith("서울에서 ") and q["answer_price"] > 0


def test_higher_lower_never_picks_close_prices_and_answer_is_right():
    for seed in range(200):
        q = build_higher_lower(ITEMS, None, random.Random(seed))
        b, t = q["base"]["price"], q["target"]["price"]
        assert abs(t - b) / min(t, b) >= HL_MIN_GAP
        assert q["answer"] == ("higher" if t > b else "lower")
        assert f"({b:,}원)" in q["question"] and f"{t:,}" not in q["question"]


def test_menu_stats_groups_food_only_with_enough_stores():
    rows = [{"menu_name": "김치찌개(1인)", "industry": "한식", "price": 6000 + i * 100} for i in range(25)]
    rows += [{"menu_name": "커트", "industry": "이미용", "price": 9000} for _ in range(30)]
    rows += [{"menu_name": "비빔밥", "industry": "한식", "price": 7000} for _ in range(5)]
    stats = menu_stats(rows)
    assert [s["menu_name"] for s in stats] == ["김치찌개"]
    assert stats[0]["count"] == 25


def test_menu_answer_matches_shown_price():
    stats = [{"menu_name": "김치찌개", "count": 182, "price_low": 6000, "price_median": 6500, "price_high": 7000,
              "price_min": 3000, "price_max": 9000}]
    seen = set()
    for seed in range(200):
        q = build_menu(stats, None, random.Random(seed))
        seen.add(q["answer"])
        if q["answer"] == "normal":
            assert 6000 <= q["shown_price"] <= 7000
        else:
            assert q["shown_price"] > 7000
        assert f"{q['shown_price']:,}원" in q["question"]
    assert seen == {"normal", "above"}
