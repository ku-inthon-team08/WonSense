from fastapi.testclient import TestClient

from app.main import app
from app.routers.items import get_items, get_menus, get_products, get_restaurants
from app.services.restaurants import search_restaurant_prices


def row(place: str, area: str, price: int, menu: str = "삼겹살 1인분", verified: bool = False) -> dict:
    return {"place_id": place, "menu": menu, "place_name": f"{place}고깃집", "area": area, "price": price,
            "weight_g": 150, "source_url": f"https://blog.example/{place}", "place_url": f"http://place.map.kakao.com/{place}",
            "verified": verified, "checked_on": "2026-11-01"}


ROWS = [
    row("a", "명동", 19000), row("b", "명동", 21000, verified=True), row("c", "홍대", 16000),
    row("d", "홍대", 17000), row("e", "안암", 15000), row("f", "명동", 9000, menu="김치찌개"),
]


def test_english_and_korean_queries_find_menu():
    for q in ["samgyeopsal", "pork belly", "삼겹살"]:
        out = search_restaurant_prices(q, ROWS)
        assert [m["menu"] for m in out] == ["삼겹살 1인분"], q
    assert search_restaurant_prices("pizza", ROWS) == []


def test_stats_by_area_and_examples():
    [m] = search_restaurant_prices("삼겹살", ROWS)
    assert m["name_en"] == "Pork belly (samgyeopsal)"
    assert m["count"] == 5 and m["price_median"] == 17000
    assert [a["area"] for a in m["by_area"]] == ["명동", "홍대", "안암"]  # 비싼 지역부터
    assert m["by_area"][0] == {"area": "명동", "count": 2, "price_median": 20000}
    assert m["verified_count"] == 1
    assert m["examples"][0]["verified"] is True  # 사람이 확인한 가격을 먼저 보여준다
    assert all(e["source_url"] for e in m["examples"])


def test_search_endpoint_returns_web_menus():
    app.dependency_overrides[get_items] = lambda: []
    app.dependency_overrides[get_menus] = lambda: {"rows": [], "districts": {}, "reference_date": None}
    app.dependency_overrides[get_products] = lambda: []
    app.dependency_overrides[get_restaurants] = lambda: ROWS
    try:
        body = TestClient(app).get("/api/items/search", params={"q": "samgyeopsal"}).json()
        assert body["web_menus"][0]["menu"] == "삼겹살 1인분"
        assert "웹 검색" in body["web_menus"][0]["source"]
        assert body["not_covered"] is False
    finally:
        app.dependency_overrides.clear()
