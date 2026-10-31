"""서울시 가격안정 모범업소(착한가격업소) 상품목록을 수집해 menu_prices에 저장한다.

사용법 (backend/ 에서):
    python -m scripts.ingest_menus

환경변수 SEOUL_OPENAPI_KEY 필요 (.env). 월 1회 갱신되는 데이터라 전체를 다시 받아 upsert하고,
이번 수집에 없던 행(폐업·메뉴 삭제)은 지운다.
"""
import re
from datetime import date

import httpx

from app.core.config import get_settings
from app.db.supabase import get_supabase

SERVICE = "ListPriceModelStoreProductService"
PAGE_SIZE = 1000
_GU = re.compile(r"(\S+구)(?:\s|$)")


def fetch_all(api_key: str) -> list[dict]:
    rows: list[dict] = []
    start = 1
    with httpx.Client(timeout=30) as client:
        while True:
            url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/{SERVICE}/{start}/{start + PAGE_SIZE - 1}/"
            body = client.get(url).json().get(SERVICE, {})
            batch = body.get("row", [])
            rows.extend(batch)
            if len(batch) < PAGE_SIZE or start + PAGE_SIZE > body.get("list_total_count", 0):
                break
            start += PAGE_SIZE
    return rows


def district_code(address: str, codes_by_name: dict[str, str]) -> str | None:
    """'서울특별시 서울 양천구 은행정로5길 48-3' → 양천구의 코드."""
    for name in _GU.findall(address or ""):
        if name in codes_by_name:
            return codes_by_name[name]
    return None


def to_records(rows: list[dict], codes_by_name: dict[str, str], today: str) -> list[dict]:
    """API 행을 menu_prices 행으로 바꾼다. 가격이 없거나 0 이하면 버리고, (가게, 메뉴)가 겹치면 마지막 값을 쓴다."""
    out: dict[tuple[str, str], dict] = {}
    for r in rows:
        store_id = str(r.get("SH_ID") or "").strip()
        menu = (r.get("IM_NAME") or "").strip()
        try:
            price = int(float(r.get("IM_PRICE")))
        except (TypeError, ValueError):
            continue
        if not store_id or not menu or price <= 0:
            continue
        address = (r.get("SH_ADDR") or "").strip()
        out[(store_id, menu)] = {
            "store_id": store_id,
            "menu_name": menu,
            "store_name": (r.get("SH_NAME") or "").strip(),
            "industry": (r.get("INDUTY_CODE_SE_NAME") or "").strip(),
            "address": address or None,
            "district_code": district_code(address, codes_by_name),
            "price": price,
            "fetched_on": today,
        }
    return list(out.values())


def main() -> None:
    api_key = get_settings().seoul_openapi_key
    if not api_key:
        raise SystemExit("SEOUL_OPENAPI_KEY가 설정되지 않았습니다")

    rows = fetch_all(api_key)
    if not rows:
        raise SystemExit("받은 데이터가 없습니다")

    supabase = get_supabase()
    codes_by_name = {d["name_ko"]: d["code"] for d in supabase.table("districts").select("code, name_ko").execute().data}
    today = date.today().isoformat()
    records = to_records(rows, codes_by_name, today)

    for i in range(0, len(records), 500):
        supabase.table("menu_prices").upsert(records[i : i + 500], on_conflict="store_id,menu_name").execute()
    supabase.table("menu_prices").delete().lt("fetched_on", today).execute()

    no_gu = sum(1 for r in records if r["district_code"] is None)
    print(f"{today}: 원본 {len(rows)}행 → 메뉴 {len(records)}개 저장 (자치구 못 찾음 {no_gu}개)")


if __name__ == "__main__":
    main()
