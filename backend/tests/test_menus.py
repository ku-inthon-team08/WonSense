from fastapi.testclient import TestClient

from app.main import app
from app.routers.items import get_items, get_menus, get_products
from app.services.menus import match_keywords, price_stats, search_menus
from scripts.ingest_menus import district_code, to_records

DISTRICTS = {"11470": "양천구", "11680": "강남구", "11110": "종로구"}


def row(store: str, menu: str, price: int, gu: str = "11470") -> dict:
    return {"store_id": store, "store_name": f"{store}식당", "menu_name": menu, "industry": "한식",
            "district_code": gu, "price": price, "fetched_on": "2026-11-01"}


ROWS = [
    row("a", "김치찌개", 7000), row("b", "김치찌개(1인)", 8000, "11680"), row("c", "김치 찌개", 9000, "11110"),
    row("d", "김치찌개", 6000), row("a", "된장찌개", 7000), row("b", "물냉면", 8000), row("c", "비빔냉면", 9000),
    row("d", "냉면", 7000), row("e", "청국장", 8000), row("f", "청국장", 8500), row("g", "청국장", 9000),
]


def test_match_keywords_english_and_korean():
    assert match_keywords("kimchi stew") == ["김치찌개"]
    assert match_keywords("Kimchi-Jjigae") == ["김치찌개"]
    assert match_keywords("김치찌개") == ["김치찌개"]
    assert "냉면" in match_keywords("naengmyeon")
    assert match_keywords("jajangmyeon") == ["짜장면"]
    assert match_keywords("자장면") == ["짜장면"]  # 표기가 달라도 같은 메뉴
    assert match_keywords("haircut") == ["커트"]
    assert match_keywords("banana") == []


def test_price_stats_uses_middle_half():
    s = price_stats([5000, 6000, 7000, 8000, 30000])
    assert s["price_median"] == 7000
    assert s["price_low"] == 6000 and s["price_high"] == 8000  # 30000 같은 극단값은 범위에 안 들어간다
    assert s["price_min"] == 5000 and s["price_max"] == 30000
    assert price_stats([7000])["price_low"] == price_stats([7000])["price_high"] == 7000


def test_search_menus_groups_spelling_variants():
    out = search_menus("kimchi stew", ROWS, DISTRICTS)
    assert len(out) == 1
    m = out[0]
    assert m["name_ko"] == "김치찌개" and m["name_en"] == "Kimchi stew"
    assert m["count"] == 4 and m["store_count"] == 4  # "김치찌개(1인)", "김치 찌개"도 포함
    assert {e["district"] for e in m["examples"]} <= set(DISTRICTS.values())
    assert len({e["district"] for e in m["examples"]}) == len(m["examples"])  # 예시 가게는 구가 겹치지 않게


def test_search_menus_cold_noodles_includes_variants():
    m = search_menus("냉면", ROWS, DISTRICTS)[0]
    assert m["count"] == 3  # 물냉면, 비빔냉면, 냉면


def test_search_menus_unknown_korean_word_falls_back_to_substring():
    out = search_menus("청국장", ROWS, DISTRICTS)
    assert out[0]["name_ko"] == "청국장" and out[0]["count"] == 3


def test_search_menus_needs_enough_stores():
    assert search_menus("된장찌개", ROWS, DISTRICTS) == []  # 가게 1곳뿐이면 시세라고 하기 어렵다


def test_district_code_from_address():
    codes = {v: k for k, v in DISTRICTS.items()}
    assert district_code("서울특별시 서울 양천구 은행정로5길 48-3", codes) == "11470"
    assert district_code("서울특별시 종로구 종로 1", codes) == "11110"
    assert district_code("경기도 성남시", codes) is None


def test_to_records_skips_bad_rows_and_dedupes():
    raw = [
        {"SH_ID": "1", "SH_NAME": "가게", "INDUTY_CODE_SE_NAME": "한식", "SH_ADDR": "서울 강남구 x", "IM_NAME": "김밥", "IM_PRICE": 3000.0},
        {"SH_ID": "1", "SH_NAME": "가게", "INDUTY_CODE_SE_NAME": "한식", "SH_ADDR": "서울 강남구 x", "IM_NAME": "김밥", "IM_PRICE": 3500.0},
        {"SH_ID": "2", "SH_NAME": "가게2", "INDUTY_CODE_SE_NAME": "한식", "SH_ADDR": "", "IM_NAME": "라면", "IM_PRICE": 0.0},
        {"SH_ID": "3", "SH_NAME": "가게3", "INDUTY_CODE_SE_NAME": "한식", "SH_ADDR": "", "IM_NAME": "", "IM_PRICE": 1000.0},
    ]
    recs = to_records(raw, {"강남구": "11680"}, "2026-11-01")
    assert len(recs) == 1
    assert recs[0]["price"] == 3500 and recs[0]["district_code"] == "11680"


def test_search_endpoint_returns_menus():
    app.dependency_overrides[get_items] = lambda: []
    app.dependency_overrides[get_menus] = lambda: {"rows": ROWS, "districts": DISTRICTS, "reference_date": "2026-11-01"}
    app.dependency_overrides[get_products] = lambda: []
    try:
        body = TestClient(app).get("/api/items/search", params={"q": "bibimbap"}).json()
        assert body["menus"] == [] and body["not_covered"] is True  # 비빔밥 메뉴가 없는 데이터

        body = TestClient(app).get("/api/items/search", params={"q": "kimchi stew"}).json()
        assert body["results"] == [] and body["not_covered"] is False
        assert body["menus"][0]["name_ko"] == "김치찌개"
        assert body["menus"][0]["reference_date"] == "2026-11-01"
        assert "착한가격" in body["menus"][0]["source"]
    finally:
        app.dependency_overrides.clear()
