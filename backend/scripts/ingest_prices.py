"""서울 열린데이터광장 '생필품 농수축산물 가격 정보'를 월 단위로 수집해 price_stats에 저장한다.

사용법 (backend/ 에서):
    python -m scripts.ingest_prices --month 2026-10

환경변수 SEOUL_OPENAPI_KEY 필요 (.env). 최신 데이터가 앞에 오므로 대상 월보다 오래된
페이지가 나오면 수집을 멈춘다. 같은 달을 다시 돌려도 upsert라 중복되지 않는다.
"""
import argparse
from collections import defaultdict
from statistics import mean

import httpx

from app.core.config import get_settings
from app.db.supabase import get_supabase
from app.services.heatmap import SEOUL_REGION, aggregate_rows

SERVICE = "ListNecessariesPricesService"
PAGE_SIZE = 1000
SOURCE = "서울 열린데이터광장 생필품 농수축산물 가격"


def fetch_month(api_key: str, month: str) -> list[dict]:
    rows: list[dict] = []
    start = 1
    with httpx.Client(timeout=30) as client:
        while True:
            url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/{SERVICE}/{start}/{start + PAGE_SIZE - 1}/"
            body = client.get(url).json()
            batch = body.get(SERVICE, {}).get("row", [])
            if not batch:
                break
            in_month = [r for r in batch if str(r.get("P_DATE", "")).startswith(month)]
            rows.extend(in_month)
            if not in_month:  # 최신순이므로 대상 월을 지나쳤다
                break
            start += PAGE_SIZE
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=True, help="YYYY-MM")
    args = parser.parse_args()

    api_key = get_settings().seoul_openapi_key
    if not api_key:
        raise SystemExit("SEOUL_OPENAPI_KEY가 설정되지 않았습니다")

    rows = fetch_month(api_key, args.month)
    if not rows:
        raise SystemExit(f"{args.month} 데이터가 없습니다")

    reference_date = max(r["P_DATE"] for r in rows)[:10]  # 해당 월의 최신 조사일
    stats = aggregate_rows(rows)
    supabase = get_supabase()

    names = sorted({name for name, _, _ in stats})
    # A_UNIT은 항상 비어 있으므로 UNIT(10kg) + QY(1포)로 단위를 만든다
    units = {r["A_NAME"].strip(): f"{r.get('UNIT') or ''} {r.get('QY') or ''}".strip() for r in rows}
    supabase.table("items").upsert(
        [
            {"source_key": n, "name_ko": n, "name_en": n, "category": "grocery", "unit": units.get(n) or "-"}
            for n in names
        ],
        on_conflict="source_key",
        ignore_duplicates=True,  # 사람이 다듬은 영문명 등을 덮어쓰지 않는다
    ).execute()
    item_ids = {
        r["source_key"]: r["id"]
        for r in supabase.table("items").select("id, source_key").in_("source_key", names).execute().data
    }

    out: list[dict] = []
    gu_avgs: dict[str, list[int]] = defaultdict(list)
    for (name, code, gu_name), s in stats.items():
        out.append(
            {"item_id": item_ids[name], "region": code, "region_name": gu_name,
             "source": SOURCE, "reference_date": reference_date, **s}
        )
        gu_avgs[name].append(s["price_avg"])
    for name, avgs in gu_avgs.items():  # 서울 전체 행: 구 평균들의 평균 (히트맵 비율의 기준과 동일)
        out.append(
            {"item_id": item_ids[name], "region": SEOUL_REGION, "region_name": "서울",
             "price_min": min(avgs), "price_avg": round(mean(avgs)), "price_max": max(avgs),
             "sample_count": len(avgs), "source": SOURCE, "reference_date": reference_date}
        )

    for i in range(0, len(out), 500):
        supabase.table("price_stats").upsert(
            out[i : i + 500], on_conflict="item_id,region,reference_date,source"
        ).execute()
    print(f"{reference_date}: 원본 {len(rows)}행 → 품목 {len(names)}개, price_stats {len(out)}행 저장")


if __name__ == "__main__":
    main()
