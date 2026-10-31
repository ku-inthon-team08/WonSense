"""한국소비자원 참가격 생필품 가격(공공데이터포털 15083256)을 상품별로 요약해 product_prices에 저장한다.

사용법 (backend/ 에서):
    python -m scripts.ingest_products            # 가장 최근 달
    python -m scripts.ingest_products --list     # 받을 수 있는 달 목록만 보기

환경변수 DATA_GO_KR_API_KEY 필요 (.env). 데이터는 달마다 별도 API 주소(uddi)로 올라오므로
Swagger 문서에서 가장 최근 달의 주소를 찾아 쓴다. 이번 수집에 없는 상품은 지운다.
"""
import argparse
import re
from collections import Counter, defaultdict
from datetime import date
from statistics import median, quantiles

import httpx

from app.core.config import get_settings
from app.db.supabase import get_supabase
from app.services.menus import round_to

SWAGGER ="https://infuser.odcloud.kr/oas/docs?namespace=15083256/v1"
API = "https://api.odcloud.kr/api"
PER_PAGE = 10000
CONVENIENCE = ("CU", "GS25", "세븐일레븐", "이마트24", "미니스톱")


def parse_dataset_date(summary: str) -> date | None:
    """'한국소비자원_생필품 가격 정보_20260925' / '..._09/24/2021' → date."""
    if m := re.search(r"(\d{4})(\d{2})(\d{2})\s*$", summary):
        return date(int(m[1]), int(m[2]), int(m[3]))
    if m := re.search(r"(\d{2})/(\d{2})/(\d{4})\s*$", summary):
        return date(int(m[3]), int(m[1]), int(m[2]))
    return None


def list_datasets(client: httpx.Client) -> list[tuple[date, str]]:
    """(데이터 날짜, API 경로) 목록, 최신순."""
    spec = client.get(SWAGGER).json()
    out = []
    for path, ops in spec["paths"].items():
        d = parse_dataset_date(ops.get("get", {}).get("summary", ""))
        if d:
            out.append((d, path))
    return sorted(out, reverse=True)


def fetch_rows(client: httpx.Client, path: str, api_key: str) -> list[dict]:
    rows: list[dict] = []
    page = 1
    while True:
        body = client.get(
            f"{API}{path}",
            params={"page": page, "perPage": PER_PAGE, "returnType": "JSON", "serviceKey": api_key},
        ).json()
        batch = body.get("data") or []
        rows.extend(batch)
        if not batch or len(rows) >= body.get("totalCount", 0):
            return rows
        page += 1


def is_convenience(store: str) -> bool:
    return any(store.startswith(c) for c in CONVENIENCE)


def summarize(rows: list[dict]) -> list[dict]:
    """판매점별 가격 행을 상품별 한 행으로 요약한다. 세일·1+1 행과 가격이 없는 행은 뺀다."""
    regular: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        name = (r.get("상품명") or "").strip()
        try:
            price = int(r.get("판매가격"))
        except (TypeError, ValueError):
            continue
        if not name or price <= 0 or r.get("세일여부") or r.get("원플러스원"):
            continue
        regular[name].append({**r, "판매가격": price})

    out = []
    for name, rs in regular.items():
        prices = sorted(r["판매가격"] for r in rs)
        q1, _, q3 = quantiles(prices, n=4, method="inclusive") if len(prices) >= 4 else (prices[0], 0, prices[-1])
        cvs = [r["판매가격"] for r in rs if is_convenience(r.get("판매업소") or "")]
        makers = Counter((r.get("제조사") or "").strip() for r in rs if r.get("제조사"))
        out.append(
            {
                "product_name": name,
                "manufacturer": makers.most_common(1)[0][0] if makers else None,
                "price_low": round_to(q1, 10),
                "price_median": round_to(median(prices), 10),
                "price_high": round_to(q3, 10),
                "price_min": prices[0],
                "price_max": prices[-1],
                "store_count": len({r.get("판매업소") for r in rs}),
                "convenience_price": round_to(median(cvs), 10) if cvs else None,
                "reference_date": max(r["조사일"] for r in rs),
            }
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="받을 수 있는 달 목록만 출력")
    args = parser.parse_args()

    api_key = get_settings().data_go_kr_api_key
    if not api_key:
        raise SystemExit("DATA_GO_KR_API_KEY가 설정되지 않았습니다")

    with httpx.Client(timeout=120) as client:
        datasets = list_datasets(client)
        if args.list:
            for d, path in datasets[:12]:
                print(d, path)
            return
        latest, path = datasets[0]
        rows = fetch_rows(client, path, api_key)
    if not rows:
        raise SystemExit(f"{latest} 데이터가 없습니다")

    records = summarize(rows)
    supabase = get_supabase()
    for i in range(0, len(records), 500):
        supabase.table("product_prices").upsert(records[i : i + 500], on_conflict="product_name").execute()
    # 이번 달 목록에 없는 상품(조사 중단)은 지운다
    supabase.table("product_prices").delete().lt("reference_date", min(r["reference_date"] for r in records)).execute()
    print(f"{latest}: 원본 {len(rows)}행 → 상품 {len(records)}개 저장")


if __name__ == "__main__":
    main()
