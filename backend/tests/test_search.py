from fastapi.testclient import TestClient

from app.main import app
from app.routers.items import get_items
from app.services.search import english_name, is_restaurant_query, search_items, split_name, suggest

# price_stats에 실제로 있는 품목명 일부 (2026-10-26 기준)
NAMES = [
    "소주 360ml, 1병", "맥주 500ml 1캔", "쌀(오대쌀) 10kg 1포", "쌀(이천쌀) 4kg 1포", "즉석밥 200g 4개입",
    "계란 10개", "라면 5개입 1봉", "컵라면 1개", "오징어(국산, 냉동) 1마리", "갈치(생물) 1마리(대)",
    "소고기(국산) 100g", "소고기(수입) 100g", "김치 3.3kg 1개", "배추(가을) 1포기", "맛김 16팩",
    "바나나 1송이", "생수 500ml 1병", "콜라 1.5L(1병)", "통조림(참치) 150g",
]
ITEMS = [
    {"item_id": i, "name_ko": n, "name_en": n, "aliases": [], "category": "grocery", "unit": "-",
     "price_min": 1000, "price_avg": 1500, "price_max": 2000, "district_count": 25,
     "source": "test", "reference_date": "2026-10-26"}
    for i, n in enumerate(NAMES, 1)
]


def names(q: str) -> list[str]:
    return [it["name_ko"] for it in search_items(q, ITEMS)]


def test_split_name():
    assert split_name("오징어(국산, 냉동) 1마리") == ("오징어", ["국산", "냉동"])
    assert split_name("소주 360ml, 1병") == ("소주", [])
    assert split_name("콜라 1.5L(1병)") == ("콜라", ["1병"])


def test_english_name_translates_variants():
    assert english_name("오징어(국산, 냉동) 1마리") == "Squid (Korean, frozen)"
    assert english_name("콜라 1.5L(1병)") == "Cola"
    assert english_name("없는품목 1개") is None


def test_english_and_korean_queries_find_same_item():
    assert names("soju")[0] == "소주 360ml, 1병"
    assert names("소주")[0] == "소주 360ml, 1병"
    assert names("SOJU ")[0] == "소주 360ml, 1병"


def test_base_item_ranks_above_synonym_match():
    # "rice"는 쌀이 먼저, 즉석밥(동의어 rice)은 그 뒤
    result = names("rice")
    assert result[:2] == ["쌀(오대쌀) 10kg 1포", "쌀(이천쌀) 4kg 1포"]
    assert "즉석밥 200g 4개입" in result


def test_partial_and_romanized_queries():
    assert "라면 5개입 1봉" in names("ramyeon")
    assert "컵라면 1개" in names("라면")
    assert names("이천")[0] == "쌀(이천쌀) 4kg 1포"
    assert names("tuna") == ["통조림(참치) 150g"]


def test_query_containing_item_name():
    assert "소주 360ml, 1병" in names("소주 한 병")
    assert "소주 360ml, 1병" in names("price of soju")


def test_single_char_size_does_not_match_everything():
    # '소'(small)가 키가 되면 갈치(대)·소고기 등이 엉뚱하게 잡힌다
    assert all(n.startswith("소") for n in names("소"))


def test_no_result_gives_suggestions_and_restaurant_notice():
    assert names("bananna") == []
    assert "banana" in suggest("bananna", ITEMS)
    assert is_restaurant_query("bibimbap")
    assert is_restaurant_query("김치찌개 1인분")
    assert not is_restaurant_query("banana")


def test_search_endpoint():
    app.dependency_overrides[get_items] = lambda: ITEMS
    try:
        client = TestClient(app)
        body = client.get("/api/items/search", params={"q": "soju"}).json()
        assert body["results"][0]["name_en"] == "Soju"
        assert body["results"][0]["district_count"] == 25
        assert "aliases" not in body["results"][0]

        body = client.get("/api/items/search", params={"q": "bibimbap"}).json()
        assert body["results"] == [] and body["not_covered"] is True

        assert client.get("/api/items/search", params={"q": ""}).status_code == 422
        assert client.get("/api/items/1").json()["name_ko"] == "소주 360ml, 1병"
        assert client.get("/api/items/999").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_korean_typo_suggestion():
    assert suggest("맥쥬", ITEMS) == ["맥주"]
