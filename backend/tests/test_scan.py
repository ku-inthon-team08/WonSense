import base64
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.db.supabase import get_supabase
from app.main import app
from app.routers.items import get_items
from app.routers.quiz import get_claude
from app.services.scan import ScannedLine, ScanOutput, catalog_text, judge_line, summarize, verdict

EGGS = {"item_id": 1, "name_ko": "계란 10개", "unit": "10개", "price_avg": 4000,
        "source": "test", "reference_date": "2026-10-26"}
RAMYEON = {"item_id": 2, "name_ko": "라면 5개입 1봉", "unit": "5개입 1봉", "price_avg": 5000,
           "source": "test", "reference_date": "2026-10-26"}
DISTRICTS = [
    {"item_id": 1, "region": "11440", "region_name": "마포구", "price_avg": 3600, "reference_date": "2026-10-26"},
    {"item_id": 1, "region": "11680", "region_name": "강남구", "price_avg": 4600, "reference_date": "2026-10-26"},
]


def line(**kw) -> ScannedLine:
    base = {"name": "계란 30구", "name_en": "eggs", "price": 14400, "quantity": "30구",
            "item_id": 1, "quantity_ratio": 3.0}
    return ScannedLine(**{**base, **kw})


def test_verdict_bands():
    assert verdict(-0.2) == "cheap"
    assert verdict(-0.1) == "fair"
    assert verdict(0.1) == "fair"
    assert verdict(0.25) == "pricey"
    assert verdict(0.31) == "ripoff"


def test_judge_scales_by_quantity_and_finds_cheapest_district():
    out = judge_line(line(), EGGS, DISTRICTS, district="강남구")
    # 30구 = 10개 × 3 → 서울 평균 12,000원, 14,400원이면 20% 비쌈
    assert out["seoul_avg"] == 12000
    assert out["diff_pct"] == 20.0
    assert out["verdict"] == "pricey"
    assert out["district_avg"] == 13800
    assert out["cheapest_district"] == {"region": "11440", "name": "마포구", "price_avg": 10800}


def test_unmatched_or_bad_ratio_is_not_compared():
    assert judge_line(line(item_id=None, quantity_ratio=None), None, [])["matched"] is False
    assert judge_line(line(quantity_ratio=500), EGGS, DISTRICTS)["matched"] is False
    assert judge_line(line(price=0), EGGS, DISTRICTS)["matched"] is False
    # 비율이 없으면 같은 규격으로 본다
    assert judge_line(line(quantity_ratio=None, price=4000), EGGS, [])["verdict"] == "fair"


def test_summary_totals_only_matched_lines():
    lines = [judge_line(line(), EGGS, []), judge_line(line(item_id=None, quantity_ratio=None), None, [])]
    s = summarize(lines)
    assert s["matched_count"] == 1 and s["total_price"] == 14400 and s["total_seoul_avg"] == 12000
    assert summarize([lines[1]])["verdict"] is None


def test_catalog_is_stable_regardless_of_input_order():
    assert catalog_text([RAMYEON, EGGS]) == catalog_text([EGGS, RAMYEON])


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
        self.beta = SimpleNamespace(messages=SimpleNamespace(parse=self._parse))
        self.output = output

    def _parse(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(parsed_output=self.output, stop_reason="end_turn")


def test_scan_endpoint():
    claude = FakeClaude(ScanOutput(lines=[line(), line(name="떡볶이", item_id=None, quantity_ratio=None, price=5000)]))
    app.dependency_overrides[get_items] = lambda: [EGGS, RAMYEON]
    app.dependency_overrides[get_supabase] = lambda: FakeSupabase()
    app.dependency_overrides[get_claude] = lambda: claude
    image = "data:image/png;base64," + base64.b64encode(b"fake-png").decode()
    try:
        client = TestClient(app)
        body = client.post("/api/scan", json={"image": image, "media_type": "image/png", "district": "마포구"}).json()
        assert [l["matched"] for l in body["lines"]] == [True, False]
        assert body["lines"][0]["district_avg"] == 10800
        assert body["summary"]["verdict"] == "pricey"

        sent = claude.calls[0]
        assert sent["messages"][0]["content"][0]["source"]["data"] == base64.b64encode(b"fake-png").decode()
        assert "1 | 계란 10개 | 10개" in sent["system"][1]["text"]

        assert client.post("/api/scan", json={"image": "not base64!"}).status_code == 400
        claude.output = None
        assert client.post("/api/scan", json={"image": image}).status_code == 502
    finally:
        app.dependency_overrides.clear()
