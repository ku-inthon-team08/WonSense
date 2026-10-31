import random

from fastapi.testclient import TestClient

from app.main import app
from app.routers.quiz import get_menu_stats, get_quiz_items
from app.services.quiz import (
    HL_MIN_GAP,
    build_guess,
    build_higher_lower,
    build_menu,
    build_price_cards,
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


def test_english_fields_pass_through_and_tolerate_missing_columns():
    item = {**ITEMS[0], "quiz_name_en": "Eggs, 10", "tip_en": "Tip"}
    g = build_guess([item], None, random.Random(0))
    assert g["quiz_name_en"] == "Eggs, 10" and g["tip_en"] == "Tip"
    # 마이그레이션 적용 전 DB: 영어 값이 없으면 None
    hl = build_higher_lower(ITEMS, None, random.Random(0))
    assert hl["base"]["name_en"] is None and hl["target"]["name_en"] is None


def test_menu_quiz_has_english_menu_name():
    stats = [{"menu_name": "김치찌개", "count": 182, "price_low": 6000, "price_median": 6500, "price_high": 7000,
              "price_min": 3000, "price_max": 9000}]
    assert build_menu(stats, None, random.Random(0))["menu_name_en"] == "Kimchi stew"


MENU_STATS = [{"menu_name": "김치찌개", "count": 182, "price_low": 6000, "price_median": 7000, "price_high": 7500,
               "price_min": 3000, "price_max": 9000},
              {"menu_name": "칼국수", "count": 147, "price_low": 5000, "price_median": 6000, "price_high": 7000,
               "price_min": 3000, "price_max": 9000}]


def test_price_cards_skip_per_100g_items_and_mark_familiar_ones():
    items = [
        {**ITEMS[0], "source_key": "계란 10개", "quiz_name_en": "Eggs, 10", "tip_en": "Tip"},
        {**ITEMS[1], "source_key": "우유 1L", "tip": ""},
        {**ITEMS[2], "quiz_name": "감자 100g", "reference_date": "2026-12-01"},
    ]
    out = build_price_cards(items, MENU_STATS)
    by_key = {c["key"]: c for c in out["cards"]}

    assert "item:3" not in by_key  # "100g당 몇 개"는 읽히지 않는다
    assert out["reference_date"] == "2026-10-26"  # 뺀 품목의 날짜는 쓰지 않는다
    assert by_key["item:1"]["anchor"] is True and by_key["item:2"]["anchor"] is False
    assert by_key["item:1"]["name_en"] == "Eggs, 10" and by_key["item:1"]["tip_en"] == "Tip"
    assert by_key["item:2"]["tip"] is None

    stew = by_key["menu:김치찌개"]
    assert stew["kind"] == "dish" and stew["price"] == 7000  # 메뉴 가격은 중앙값
    assert stew["name_en"] == "Kimchi stew" and stew["anchor"] is True
    assert by_key["menu:칼국수"]["anchor"] is False


def test_price_cards_endpoint():
    app.dependency_overrides[get_quiz_items] = lambda: ITEMS
    app.dependency_overrides[get_menu_stats] = lambda: MENU_STATS
    try:
        body = TestClient(app).get("/api/quiz/prices").json()
        assert len(body["cards"]) == len(ITEMS) + len(MENU_STATS)
        assert body["reference_date"] == "2026-10-26"
    finally:
        app.dependency_overrides.clear()


def test_price_cards_with_no_data():
    assert build_price_cards([], []) == {"cards": [], "reference_date": None}
