from collections import defaultdict
from statistics import mean

SEOUL_REGION = "seoul"


def aggregate_rows(rows: list[dict]) -> dict[tuple[str, str, str], dict]:
    """수집 원본 행을 (상품명, 구 코드, 구 이름) 단위로 묶어 min/avg/max/건수를 구한다.

    같은 품목명이라도 규격이 다르면 가격 수준이 다르므로 A_NAME(규격 포함) 기준으로 묶는다.
    가격이 비었거나 0 이하인 행은 버린다.
    """
    buckets: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for row in rows:
        try:
            price = int(float(row.get("A_PRICE")))
        except (TypeError, ValueError):
            continue
        if price <= 0 or not row.get("A_NAME") or not row.get("M_GU_CODE"):
            continue
        key = (row["A_NAME"].strip(), str(row["M_GU_CODE"]), (row.get("M_GU_NAME") or "").strip())
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
