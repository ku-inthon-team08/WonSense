from collections import defaultdict
from statistics import mean

SEOUL_REGION = "seoul"


def normalize_gu_code(code) -> str | None:
    """API의 M_GU_CODE를 행정표준 시군구 코드(5자리, districts.code)로 바꾼다.

    API에는 '110000'(시군구 3자리 + 000)과 '11110'(표준 5자리)이 섞여 있어서
    그대로 쓰면 같은 구(종로구)가 두 지역으로 나뉜다. 알 수 없는 형식이면 None.
    """
    code = str(code or "").strip().split(".")[0]
    if len(code) == 5 and code.startswith("11"):
        return code
    if len(code) == 6 and code.endswith("000"):
        return "11" + code[:3]
    return None


def aggregate_rows(rows: list[dict]) -> dict[tuple[str, str, str], dict]:
    """수집 원본 행을 (상품명, 구 코드, 구 이름) 단위로 묶어 min/avg/max/건수를 구한다.

    같은 품목명이라도 규격이 다르면 가격 수준이 다르므로 A_NAME(규격 포함) 기준으로 묶는다.
    다음 행은 버린다.
    - 가격이 비었거나 0 이하인 행
    - 이미 본 P_SEQ: API 페이지가 서로 겹쳐서 같은 조사 결과가 여러 번 내려온다
    - ADD_COL(할인/행사가/세일 등)이 있는 행: 정상가끼리 비교하기 위해
    - 구 코드를 알 수 없는 행
    """
    buckets: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    seen: set[str] = set()
    for row in rows:
        seq = row.get("P_SEQ")
        if seq is not None:
            if seq in seen:
                continue
            seen.add(seq)
        try:
            price = int(float(row.get("A_PRICE")))
        except (TypeError, ValueError):
            continue
        if price <= 0 or not row.get("A_NAME") or (row.get("ADD_COL") or "").strip():
            continue
        gu_code = normalize_gu_code(row.get("M_GU_CODE"))
        if gu_code is None:
            continue
        key = (row["A_NAME"].strip(), gu_code, (row.get("M_GU_NAME") or "").strip())
        buckets[key].append(price)

    return {
        key: {
            "price_min": min(prices),
            "price_avg": round(mean(prices)),
            "price_max": max(prices),
            "sample_count": len(prices),
        }
        for key, prices in buckets.items()
    }


def build_heatmap(stats: list[dict]) -> dict:
    """price_stats 행들로 구별 히트맵 데이터를 만든다.

    stats: [{item_id, region, region_name, price_avg}, ...] (같은 기준월, region != 'seoul')
    - 품목마다 구 평균들의 평균을 '서울 평균'으로 보고, 각 구 가격을 그 대비 비율(%)로 바꾼다.
    - 구의 지수 = 그 구가 가진 품목들의 비율 평균. 100이 서울 평균, 높을수록 비쌈.
    """
    by_item: dict[int, list[dict]] = defaultdict(list)
    for s in stats:
        by_item[s["item_id"]].append(s)

    ratios: dict[str, list[float]] = defaultdict(list)
    names: dict[str, str] = {}
    prices: dict[str, int] = {}
    for item_rows in by_item.values():
        seoul_avg = mean(r["price_avg"] for r in item_rows)
        if seoul_avg <= 0:
            continue
        for r in item_rows:
            ratios[r["region"]].append(r["price_avg"] / seoul_avg * 100)
            names[r["region"]] = r.get("region_name") or r["region"]
            prices[r["region"]] = r["price_avg"]

    districts = [
        {
            "region": region,
            "name": names[region],
            "index": round(mean(vals), 1),
            "diff_pct": round(mean(vals) - 100, 1),
            "price_avg": prices[region] if len(by_item) == 1 else None,
            "item_count": len(vals),
        }
        for region, vals in ratios.items()
    ]
    districts.sort(key=lambda d: d["index"], reverse=True)
    return {"districts": districts}
