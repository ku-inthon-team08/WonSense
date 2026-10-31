import base64
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.db.supabase import get_supabase
from app.main import app
from app.routers.items import get_items, get_menus
from app.core.claude import get_claude
from app.services.scan import ScannedLine, ScanOutput, catalog_text, judge_line, load_reference, summarize, verdict

EGGS = {"item_id": 1, "name_ko": "계란 10개", "unit": "10개", "price_min": 3500, "price_avg": 4000, "price_max": 4800,
        "source": "test", "reference_date": "2026-10-26"}
RAMYEON = {"item_id": 2, "name_ko": "라면 5개입 1봉", "unit": "5개입 1봉", "price_avg": 5000,
           "source": "test", "reference_date": "2026-10-26"}
DISTRICTS = [
    {"item_id": 1, "region": "11440", "region_name": "마포구", "price_avg": 3600, "reference_date": "2026-10-26"},
    {"item_id": 1, "region": "11680", "region_name": "강남구", "price_avg": 4600, "reference_date": "2026-10-26"},
]


# 착한가격업소 김치찌개 5곳: 보통 범위(25~75%) 8,000~9,000원
MENUS = {
    "rows": [
        {"store_id": i, "store_name": f"가게{i}", "menu_name": name, "industry": "한식", "district_code": "11440", "price": p}
        for i, (name, p) in enumerate(
            [("김치찌개", 7000), ("김치찌개(1인)", 8000), ("김치찌개", 8000), ("김치찌게", 9000), ("김치찌개", 10000)], 1
        )
    ],
    "districts": {"11440": "마포구"},
    "reference_date": "2026-10-20",
}


def line(**kw) -> ScannedLine:
    base = {"name": "계란 30구", "name_en": "eggs", "price": 14400, "quantity": "30구",
            "item_id": 1, "reference_id": None, "quantity_ratio": 3.0, "description_en": "A tray of 30 eggs.",
            "spice_level": None, "contains": ["egg"], "vegetarian": True}
    return ScannedLine(**{**base, **kw})


def test_verdict_bands():
    assert verdict(-0.2) == "cheap"
    assert verdict(-0.1) == "fair"
    assert verdict(0.1) == "fair"
    assert verdict(0.25) == "pricey"
    assert verdict(0.31) == "ripoff"


def test_judge_scales_by_quantity_and_uses_seoul_without_district():
    out = judge_line(line(), EGGS, DISTRICTS)
    # 30구 = 10개 × 3 → 서울 평균 12,000원, 14,400원이면 20% 비쌈
    assert out["seoul_avg"] == 12000 and out["compare_avg"] == 12000 and out["compare_region"] is None
    assert out["diff_pct"] == 20.0 and out["seoul_diff_pct"] == 20.0
    assert out["verdict"] == "pricey"
    assert out["district_avg"] is None
    assert out["district_prices"] == {"마포구": 10800, "강남구": 13800}
    assert out["cheapest_district"] == {"region": "11440", "name": "마포구", "price_avg": 10800}
    assert out["basis"] == "official" and out["seoul_range"] == [10500, 14400]


def test_judge_against_selected_district_average():
    # 같은 14,400원이라도 강남구(13,800원)에서는 적정가, 마포구(10,800원)에서는 바가지
    gangnam = judge_line(line(), EGGS, DISTRICTS, district="강남구")
    assert gangnam["compare_avg"] == 13800 and gangnam["compare_region"] == "강남구"
    assert gangnam["verdict"] == "fair" and gangnam["diff_pct"] == 4.3
    assert gangnam["seoul_diff_pct"] == 20.0

    mapo = judge_line(line(), EGGS, DISTRICTS, district="11440")  # 코드로 줘도 된다
    assert mapo["compare_region"] == "마포구" and mapo["verdict"] == "ripoff"

    # 데이터가 없는 구면 서울 평균으로 돌아간다
    assert judge_line(line(), EGGS, DISTRICTS, district="은평구")["compare_region"] is None


def reference_id(name: str) -> int:
    return next(i for i, e in load_reference()["entries"].items() if e["item"].startswith(name))


def test_unmatched_item_is_estimated_from_reference():
    # 김치찌개 15,000원 → Numbeo 저렴한 식당 한 끼 12,000원보다 25% 비쌈
    rid = reference_id("Meal at an Inexpensive Restaurant")
    out = judge_line(line(name="김치찌개", item_id=None, reference_id=rid, quantity_ratio=1, price=15000), None, [])
    assert out["basis"] == "estimate" and out["seoul_avg"] == 12000
    assert out["seoul_range"] == [9000, 15000]
    assert out["verdict"] == "pricey" and out["cheapest_district"] is None
    assert out["source"].startswith("Numbeo")


def test_reference_scales_by_size():
    # 콜라 500ml vs 기준 0.33L 2,120원 → ×1.5
    rid = reference_id("Soft Drink")
    out = judge_line(line(name="콜라 500ml", item_id=None, reference_id=rid, quantity_ratio=1.5, price=3180), None, [])
    assert out["seoul_avg"] == 3180 and out["verdict"] == "fair"


def test_reference_skips_rent_salary_and_cars():
    items = [e["item"] for e in load_reference()["entries"].values()]
    assert not any("Apartment" in i or "Salary" in i or "Corolla" in i or "Preschool" in i for i in items)
    assert "Taxi Start (Standard Tariff)" in items


def test_unmatched_or_bad_ratio_is_not_compared():
    assert judge_line(line(item_id=None, quantity_ratio=None), None, [])["matched"] is False
    assert judge_line(line(item_id=None, reference_id=9999, quantity_ratio=None), None, [])["matched"] is False
    assert judge_line(line(quantity_ratio=500), EGGS, DISTRICTS)["matched"] is False
    assert judge_line(line(price=0), EGGS, DISTRICTS)["matched"] is False
    # 비율이 없으면 같은 규격으로 본다
    assert judge_line(line(quantity_ratio=None, price=4000), EGGS, [])["verdict"] == "fair"


def test_summary_totals_only_matched_lines():
    lines = [judge_line(line(), EGGS, []), judge_line(line(item_id=None, quantity_ratio=None), None, [])]
    s = summarize(lines)
    assert s["matched_count"] == 1 and s["total_price"] == 14400 and s["total_avg"] == 12000
    assert summarize([lines[1]])["verdict"] is None


def test_catalog_is_stable_regardless_of_input_order():
    assert catalog_text([RAMYEON, EGGS]) == catalog_text([EGGS, RAMYEON])


def stew(**kw) -> ScannedLine:
    base = {"name": "김치찌개", "name_en": "kimchi stew", "quantity": None, "item_id": None, "quantity_ratio": None,
            "description_en": "Spicy kimchi stew with pork and tofu.", "spice_level": 2, "contains": ["pork", "soy"],
            "vegetarian": False}
    return line(**{**base, **kw})


def test_menu_is_judged_against_good_price_store_range():
    out = judge_line(stew(price=9500), None, [], menus=MENUS)
    # 착한가격업소는 일부러 싼 가게라 '보통' 범위 위쪽 끝(9,000원)을 기준으로 본다
    assert out["basis"] == "menu" and out["seoul_avg"] == 9000 and out["seoul_range"] == [8000, 9000]
    assert out["verdict"] == "fair" and out["store_count"] == 5
    assert out["source"].startswith("서울시 가격안정") and out["reference_date"] == "2026-10-20"
    assert judge_line(stew(price=13000), None, [], menus=MENUS)["verdict"] == "ripoff"


def test_menu_beats_numbeo_and_numbeo_is_the_fallback():
    rid = reference_id("Meal at an Inexpensive Restaurant")
    assert judge_line(stew(price=9000, reference_id=rid), None, [], menus=MENUS)["basis"] == "menu"
    assert judge_line(stew(price=9000, reference_id=rid), None, [], menus=None)["basis"] == "estimate"


def test_translation_fields_pass_through_even_when_unmatched():
    out = judge_line(stew(name="수제 막걸리", price=0), None, [], menus=MENUS)
    assert out["matched"] is False
    assert out["description_en"].startswith("Spicy") and out["spice_level"] == 2
    assert out["contains"] == ["pork", "soy"] and out["vegetarian"] is False


class FakeQuery:
    def __init__(self, data):
        self.data = data

    def __getattr__(self, _):
        return lambda *a, **kw: self

    def execute(self):
        return SimpleNamespace(data=self.data)


class FakeSupabase:
    def table(self, _):
        return FakeQuery(DISTRICTS)


class FakeClaude:
    def __init__(self, output):
        self.calls = []
        self.messages = SimpleNamespace(parse=self._parse)
        self.output = output

    def _parse(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(parsed_output=self.output, stop_reason="end_turn")


def test_scan_endpoint():
    claude = FakeClaude(ScanOutput(lines=[line(), line(name="떡볶이", item_id=None, quantity_ratio=None, price=5000), stew(price=9000)]))
    app.dependency_overrides[get_items] = lambda: [EGGS, RAMYEON]
    app.dependency_overrides[get_menus] = lambda: MENUS
    app.dependency_overrides[get_supabase] = lambda: FakeSupabase()
    app.dependency_overrides[get_claude] = lambda: claude
    image = "data:image/png;base64," + base64.b64encode(b"fake-png").decode()
    try:
        client = TestClient(app)
        body = client.post("/api/scan", json={"image": image, "media_type": "image/png", "district": "마포구"}).json()
        assert [l["matched"] for l in body["lines"]] == [True, False, True]
        assert body["lines"][0]["district_avg"] == 10800
        assert body["lines"][2]["basis"] == "menu" and body["lines"][2]["spice_level"] == 2
        assert body["summary"]["total_avg"] == 10800 + 9000  # 마포구 계란 평균 + 김치찌개 기준가

        sent = claude.calls[0]
        assert sent["messages"][0]["content"][0]["source"]["data"] == base64.b64encode(b"fake-png").decode()
        assert sent["model"] == "claude-haiku-5-5"
        assert "1 | 계란 10개 | 10개" in sent["system"][1]["text"]
        assert "Taxi Start" in sent["system"][1]["text"]
        assert "spice_level" in sent["system"][0]["text"]

        assert client.post("/api/scan", json={"image": "not base64!"}).status_code == 400
        claude.output = None
        assert client.post("/api/scan", json={"image": image}).status_code == 502
    finally:
        app.dependency_overrides.clear()
