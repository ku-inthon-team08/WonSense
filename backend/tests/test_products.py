from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.routers.items import get_items, get_menus, get_products
from app.services.products import match_concepts, search_products
from scripts.ingest_products import is_convenience, parse_dataset_date, summarize


def product(name: str, stores: int = 100, **kw) -> dict:
    return {"product_name": name, "manufacturer": None, "price_low": 1000, "price_median": 1200, "price_high": 1400,
            "price_min": 900, "price_max": 2000, "store_count": stores, "convenience_price": None,
            "reference_date": "2026-09-11", **kw}


# 실제 2026-09 데이터에 있는 상품명 일부 (헷갈리기 쉬운 것 포함)
PRODUCTS = [
    product("참이슬 후레쉬(360ml)", 300), product("처음처럼(360ml)", 250), product("카스 프레쉬(500ml)", 200),
    product("테라(500ml)", 180), product("박카스맛 젤리(50g)", 50), product("폰테라 앵커버터(227g)", 40),
    product("바세린 립테라피 스틱 오리지널(4.8g)", 30), product("삼다수(500ml)", 220), product("신라면(5개입)", 260),
    product("농심 신라면 큰사발면(114g)", 120), product("서울우유 흰우유(1L)", 240), product("촉촉한 우유식빵(330g)", 90),
    product("서울우유 버터(450g)", 60), product("햇반(210g)", 230), product("메디안 치석 치약 오리지널(3개)", 150),
]


def names(q: str) -> list[str]:
    return [p["product_name"] for p in search_products(q, PRODUCTS)]


def test_english_category_finds_brands():
    assert set(names("soju")) == {"참이슬 후레쉬(360ml)", "처음처럼(360ml)"}
    assert names("soju")[0] == "참이슬 후레쉬(360ml)"  # 조사 판매점이 많은 상품부터
    assert set(names("toothpaste")) == {"메디안 치석 치약 오리지널(3개)"}
    assert set(names("ramen")) == {"신라면(5개입)", "농심 신라면 큰사발면(114g)"}


def test_brand_name_lookalikes_are_not_matched():
    assert set(names("beer")) == {"카스 프레쉬(500ml)", "테라(500ml)"}  # 박카스·폰테라·립테라피 제외
    assert set(names("milk")) == {"서울우유 흰우유(1L)"}  # 우유식빵·서울우유 버터 제외
    assert "서울우유 버터(450g)" in names("butter")


def test_korean_queries():
    assert set(names("소주")) == {"참이슬 후레쉬(360ml)", "처음처럼(360ml)"}
    assert names("햇반") == ["햇반(210g)"]
    # 사전에 없는 한글(브랜드명)은 상품명에 들어 있으면 찾는다
    assert set(names("신라면")) == {"신라면(5개입)", "농심 신라면 큰사발면(114g)"}
    assert names("없는상품") == []


def test_match_concepts_ignores_unknown_words():
    assert match_concepts("pizza") == []
    assert match_concepts("") == []


def test_parse_dataset_date_both_formats():
    assert parse_dataset_date("한국소비자원_생필품 가격 정보_20260925") == date(2026, 9, 25)
    assert parse_dataset_date("한국소비자원 생필품 및 서비스 가격 정보_09/24/2021") == date(2021, 9, 24)
    assert parse_dataset_date("이름만 있음") is None


def test_is_convenience():
    assert is_convenience("CU") and is_convenience("GS25 강남점") and is_convenience("세븐일레븐")
    assert not is_convenience("롯데슈퍼전농점") and not is_convenience("GS더프레시 역삼점")


def raw(name: str, price: int, store: str, sale=None, one_plus_one=None) -> dict:
    return {"상품명": name, "판매가격": price, "판매업소": store, "제조사": "하이트진로", "조사일": "2026-09-11",
            "세일여부": sale, "원플러스원": one_plus_one}


def test_summarize_uses_regular_prices_and_convenience_median():
    rows = [
        raw("참이슬(360ml)", 1500, "이마트 A"), raw("참이슬(360ml)", 1600, "롯데슈퍼 B"),
        raw("참이슬(360ml)", 1700, "GS더프레시 C"), raw("참이슬(360ml)", 1800, "이마트 D"),
        raw("참이슬(360ml)", 2100, "CU"), raw("참이슬(360ml)", 2300, "GS25"),
        raw("참이슬(360ml)", 900, "이마트 E", sale="Y"),  # 세일가는 뺀다
        raw("참이슬(360ml)", 1000, "이마트 F", one_plus_one="Y"),  # 1+1도 뺀다
        raw("참이슬(360ml)", 0, "이마트 G"),
    ]
    [s] = summarize(rows)
    assert s["price_min"] == 1500 and s["price_max"] == 2300
    assert s["store_count"] == 6
    assert s["convenience_price"] == 2200  # CU 2100, GS25 2300의 중앙값
    assert s["price_low"] <= s["price_median"] <= s["price_high"]
    assert s["manufacturer"] == "하이트진로" and s["reference_date"] == "2026-09-11"


def test_summarize_without_convenience_rows():
    [s] = summarize([raw("햇반(210g)", 1200, "이마트 A")])
    assert s["convenience_price"] is None
    assert s["price_low"] == s["price_median"] == s["price_high"] == 1200


def test_search_endpoint_returns_products():
    app.dependency_overrides[get_items] = lambda: []
    app.dependency_overrides[get_menus] = lambda: {"rows": [], "districts": {}, "reference_date": None}
    app.dependency_overrides[get_products] = lambda: PRODUCTS
    try:
        body = TestClient(app).get("/api/items/search", params={"q": "beer"}).json()
        assert [p["product_name"] for p in body["products"]] == ["카스 프레쉬(500ml)", "테라(500ml)"]
        assert body["products"][0]["category_en"] == "Beer"
        assert "참가격" in body["products"][0]["source"]
        assert body["not_covered"] is False
    finally:
        app.dependency_overrides.clear()
