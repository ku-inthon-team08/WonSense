from types import SimpleNamespace as NS

from scripts.mine_restaurant_prices import search_result_urls, to_record, validate

SEEN = {"blog.naver.com/abc/123", "place.map.kakao.com/15809642"}


def answer(**kw) -> dict:
    return {"found": True, "menu_name": "삼겹살(150g)", "price": 17000, "weight_g": 150,
            "source_url": "https://blog.naver.com/abc/123", "source_quote": "삼겹살 150g 17,000원", **kw}


def test_validate_accepts_price_from_search_results():
    assert validate(answer(), SEEN) is None
    # http/https, www, m., 끝 슬래시 차이는 같은 페이지로 본다
    assert validate(answer(source_url="http://m.blog.naver.com/abc/123/"), {"blog.naver.com/abc/123"}) is None


def test_validate_rejects_made_up_source():
    assert validate(answer(source_url="https://example.com/menu"), SEEN) == "source_not_in_search_results"
    assert validate(answer(source_url=""), SEEN) == "source_not_in_search_results"


def test_validate_rejects_not_found_and_odd_prices():
    assert validate(answer(found=False), SEEN) == "not_found"
    assert validate(answer(price=0), SEEN) == "price_out_of_range"
    assert validate(answer(price=1700), SEEN) == "price_out_of_range"  # 자릿수 실수 등
    assert validate(answer(price=1_700_000), SEEN) == "price_out_of_range"


def test_search_result_urls_reads_only_search_results():
    content = [
        NS(type="server_tool_use"),
        NS(type="web_search_tool_result", content=[NS(url="https://blog.naver.com/abc/123"), NS(url="https://www.place.map.kakao.com/15809642/")]),
        NS(type="web_search_tool_result", content=NS(error_code="max_uses_exceeded")),  # 오류면 content가 목록이 아니다
        NS(type="text", text="{}"),
    ]
    assert search_result_urls(content) == SEEN


def test_to_record_maps_kakao_place():
    place = {"id": "15809642", "place_name": "불타는다동화로", "road_address_name": "서울 중구 을지로3길 33",
             "x": "126.98", "y": "37.56", "category_name": "음식점 > 한식 > 육류,고기 > 삼겹살",
             "place_url": "http://place.map.kakao.com/15809642"}
    r = to_record(place, "명동", "삼겹살 1인분", answer(weight_g=0), {"중구": "11140"}, "2026-11-01")
    assert r["district_code"] == "11140"
    assert r["weight_g"] is None  # 0은 "모름"
    assert r["lat"] == 37.56 and r["lng"] == 126.98
    assert r["price"] == 17000 and r["source_url"].startswith("https://blog.naver.com")
