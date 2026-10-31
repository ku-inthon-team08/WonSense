from app.services.heatmap import aggregate_rows, build_heatmap, normalize_gu_code


def test_aggregate_groups_by_spec_and_skips_bad_prices():
    rows = [
        {"A_NAME": "쌀 10kg", "A_PRICE": "30000", "M_GU_CODE": "170000", "M_GU_NAME": "용산구"},
        {"A_NAME": "쌀 10kg", "A_PRICE": "34000", "M_GU_CODE": "170000", "M_GU_NAME": "용산구"},
        {"A_NAME": "쌀 4kg", "A_PRICE": "14000", "M_GU_CODE": "170000", "M_GU_NAME": "용산구"},
        {"A_NAME": "쌀 4kg", "A_PRICE": "", "M_GU_CODE": "170000", "M_GU_NAME": "용산구"},
    ]
    out = aggregate_rows(rows)
    assert out[("쌀 10kg", "11170", "용산구")]["price_avg"] == 32000
    assert out[("쌀 10kg", "11170", "용산구")]["sample_count"] == 2
    assert out[("쌀 4kg", "11170", "용산구")]["sample_count"] == 1


def test_normalize_gu_code_handles_both_api_formats():
    assert normalize_gu_code("110000") == "11110"
    assert normalize_gu_code("11110") == "11110"
    assert normalize_gu_code("545000") == "11545"
    assert normalize_gu_code("1") is None


def test_aggregate_merges_district_code_formats():
    rows = [
        {"A_NAME": "라면 1봉", "A_PRICE": "1000", "M_GU_CODE": "110000", "M_GU_NAME": "종로구"},
        {"A_NAME": "라면 1봉", "A_PRICE": "1200", "M_GU_CODE": "11110", "M_GU_NAME": "종로구"},
    ]
    out = aggregate_rows(rows)
    assert list(out) == [("라면 1봉", "11110", "종로구")]
    assert out[("라면 1봉", "11110", "종로구")]["sample_count"] == 2


def test_aggregate_skips_duplicate_p_seq_and_discounts():
    base = {"A_NAME": "라면 1봉", "M_GU_CODE": "11110", "M_GU_NAME": "종로구"}
    rows = [
        {**base, "P_SEQ": 1.0, "A_PRICE": "1000", "ADD_COL": ""},
        {**base, "P_SEQ": 1.0, "A_PRICE": "1000", "ADD_COL": ""},  # 페이지 겹침으로 다시 내려온 행
        {**base, "P_SEQ": 2.0, "A_PRICE": "500", "ADD_COL": "할인"},
        {**base, "P_SEQ": 3.0, "A_PRICE": "1400", "ADD_COL": ""},
    ]
    out = aggregate_rows(rows)[("라면 1봉", "11110", "종로구")]
    assert out["sample_count"] == 2
    assert out["price_avg"] == 1200


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
