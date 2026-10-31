from app.services.heatmap import aggregate_rows, build_heatmap


def test_aggregate_groups_by_spec_and_skips_bad_prices():
    rows = [
        {"A_NAME": "쌀 10kg", "A_PRICE": "30000", "M_GU_CODE": "1", "M_GU_NAME": "용산구"},
        {"A_NAME": "쌀 10kg", "A_PRICE": "34000", "M_GU_CODE": "1", "M_GU_NAME": "용산구"},
        {"A_NAME": "쌀 4kg", "A_PRICE": "14000", "M_GU_CODE": "1", "M_GU_NAME": "용산구"},
        {"A_NAME": "쌀 4kg", "A_PRICE": "", "M_GU_CODE": "1", "M_GU_NAME": "용산구"},
    ]
    out = aggregate_rows(rows)
    assert out[("쌀 10kg", "1", "용산구")]["price_avg"] == 32000
    assert out[("쌀 10kg", "1", "용산구")]["sample_count"] == 2
    assert out[("쌀 4kg", "1", "용산구")]["sample_count"] == 1


def test_index_is_relative_to_seoul_average():
    stats = [
        {"item_id": 1, "region": "a", "region_name": "A구", "price_avg": 3000},
        {"item_id": 1, "region": "b", "region_name": "B구", "price_avg": 1000},
        {"item_id": 2, "region": "a", "region_name": "A구", "price_avg": 200},
        {"item_id": 2, "region": "b", "region_name": "B구", "price_avg": 200},
    ]
    d = {x["region"]: x for x in build_heatmap(stats)["districts"]}
    # 품목 1: 서울 평균 2000 → A 150%, B 50%. 품목 2: 둘 다 100% → 값 크기가 달라도 균등 반영
    assert d["a"]["index"] == 125.0
    assert d["b"]["index"] == 75.0
