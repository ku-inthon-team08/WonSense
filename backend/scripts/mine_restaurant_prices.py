"""식당 메뉴 가격 수집 파이프라인: 카카오 로컬 API로 식당 목록 → Claude 웹 검색으로 가격 찾기 → restaurant_prices.

사용법 (backend/ 에서):
    python -m scripts.mine_restaurant_prices --dry-run                    # DB에 넣지 않고 JSON 파일로만 저장
    python -m scripts.mine_restaurant_prices --areas 명동 홍대 --per-area 5
    python -m scripts.mine_restaurant_prices --query 삼겹살 --menu "삼겹살 1인분"

환경변수: KAKAO_REST_API_KEY, ANTHROPIC_API_KEY (.env).
Claude 웹 검색은 검색 횟수만큼 비용이 붙는다. 식당마다 검색을 최대 MAX_SEARCHES번으로 제한한다.

신뢰도 규칙:
- 가격의 출처 URL이 그 호출에서 웹 검색이 실제로 돌려준 URL 중 하나가 아니면 버린다 (지어낸 출처 방지).
- 가격이 MIN_PRICE~MAX_PRICE 밖이면 버린다.
- 저장된 행은 verified = false. 사람이 출처를 열어 확인한 뒤 true로 바꾼다.
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path

import anthropic
import httpx

from app.core.config import get_settings
from app.db.supabase import get_supabase
from scripts.ingest_menus import district_code

KAKAO_SEARCH = "https://dapi.kakao.com/v2/local/search/keyword.json"
MODEL = "claude-opus-5-5"
MAX_SEARCHES = 5  # 식당 하나당 웹 검색 최대 횟수 (비용 상한)
MAX_PAUSES = 3  # 서버 쪽 검색 루프가 pause_turn으로 멈췄을 때 이어서 돌리는 최대 횟수
MIN_PRICE, MAX_PRICE = 3000, 100000
DEFAULT_AREAS = ["명동", "홍대", "강남역", "이태원", "안암"]
OUT_DIR = Path(__file__).resolve().parent / "output"

SYSTEM = """You look up current menu prices of a specific restaurant in Seoul using web search.

Rules:
- Search for the exact restaurant (same name and branch, matching the given address). Korean sources such as Naver/Kakao place pages, the restaurant's own site, and recent blog reviews with menu boards are good sources.
- Report a price only if you actually read it on a page returned by your search, for this restaurant and this menu. Prefer the most recent source (2025 or later).
- Never estimate, average, or use another branch or another restaurant's price. If you cannot find it, set found to false.
- source_url must be the exact URL of the page where you read the price. source_quote is the short text from that page that shows the price (in the original language).
- weight_g is the grams per serving if the source states it, otherwise 0."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "found": {"type": "boolean"},
        "menu_name": {"type": "string", "description": "메뉴 이름 (원문 그대로)"},
        "price": {"type": "integer", "description": "원 단위 가격, 못 찾으면 0"},
        "weight_g": {"type": "integer", "description": "1인분 그램 수, 모르면 0"},
        "source_url": {"type": "string", "description": "가격을 읽은 페이지 URL, 못 찾으면 빈 문자열"},
        "source_quote": {"type": "string", "description": "가격이 적힌 원문 부분"},
    },
    "required": ["found", "menu_name", "price", "weight_g", "source_url", "source_quote"],
    "additionalProperties": False,
}


def find_places(client: httpx.Client, api_key: str, area: str, query: str, limit: int) -> list[dict]:
    """카카오 로컬 키워드 검색 (음식점 FD6). 정확도순으로 limit개."""
    places: list[dict] = []
    page = 1
    while len(places) < limit:
        body = client.get(
            KAKAO_SEARCH,
            params={"query": f"{area} {query}", "category_group_code": "FD6", "size": 15, "page": page},
            headers={"Authorization": f"KakaoAK {api_key}"},
        ).json()
        places.extend(body.get("documents", []))
        if body.get("meta", {}).get("is_end", True):
            break
        page += 1
    return places[:limit]


def _norm_url(url: str) -> str:
    """http/https, www./m. 서브도메인, 끝 슬래시 차이를 없앤다 (같은 페이지 비교용)."""
    return re.sub(r"^(https?://)?(www\.|m\.)?", "", url.strip()).rstrip("/")


def search_result_urls(content: list) -> set[str]:
    """응답에서 웹 검색이 실제로 돌려준 페이지 URL들."""
    urls = set()
    for block in content:
        if getattr(block, "type", None) == "web_search_tool_result" and isinstance(block.content, list):
            urls.update(_norm_url(r.url) for r in block.content if getattr(r, "url", None))
    return urls


def validate(answer: dict, seen_urls: set[str]) -> str | None:
    """저장해도 되는 답이면 None, 아니면 버리는 이유."""
    if not answer.get("found"):
        return "not_found"
    if not MIN_PRICE <= answer.get("price", 0) <= MAX_PRICE:
        return "price_out_of_range"
    if not answer.get("source_url") or _norm_url(answer["source_url"]) not in seen_urls:
        return "source_not_in_search_results"
    return None


def ask_claude(claude: anthropic.Anthropic, place: dict, menu: str) -> tuple[dict | None, set[str], str]:
    """(답, 검색 결과 URL들, 상태). 상태는 ok / refusal / no_answer."""
    user = (
        f"식당: {place['place_name']}\n주소: {place.get('road_address_name') or place.get('address_name')}\n"
        f"카카오맵: {place.get('place_url')}\n찾을 메뉴: {menu}"
    )
    messages: list = [{"role": "user", "content": user}]
    seen: set[str] = set()
    response = None
    for _ in range(MAX_PAUSES + 1):
        response = claude.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": MAX_SEARCHES}],
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
            # 안전 분류기가 거절하면 서버가 다른 모델로 다시 돌린다
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=messages,
        )
        seen |= search_result_urls(response.content)
        if response.stop_reason != "pause_turn":
            break
        # 서버 쪽 검색 루프가 멈춤: 지금까지의 응답을 붙여 다시 보내면 이어서 진행한다
        messages = [messages[0], {"role": "assistant", "content": response.content}]

    if response.stop_reason == "refusal":
        return None, seen, "refusal"
    text = next((b.text for b in response.content if getattr(b, "type", None) == "text"), None)
    if not text:
        return None, seen, "no_answer"
    try:
        return json.loads(text), seen, "ok"
    except json.JSONDecodeError:
        return None, seen, "no_answer"


def to_record(place: dict, area: str, menu: str, answer: dict, codes_by_name: dict[str, str], today: str) -> dict:
    address = place.get("road_address_name") or place.get("address_name") or ""
    return {
        "place_id": str(place["id"]),
        "menu": menu,
        "place_name": place["place_name"],
        "area": area,
        "district_code": district_code(address, codes_by_name),
        "address": address or None,
        "lat": float(place["y"]) if place.get("y") else None,
        "lng": float(place["x"]) if place.get("x") else None,
        "category": place.get("category_name"),
        "place_url": place.get("place_url"),
        "price": answer["price"],
        "weight_g": answer["weight_g"] or None,
        "source_url": answer["source_url"],
        "source_quote": (answer.get("source_quote") or "")[:500] or None,
        "model": MODEL,
        "checked_on": today,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--areas", nargs="+", default=DEFAULT_AREAS)
    parser.add_argument("--query", default="삼겹살", help="카카오 검색어 (업종/메뉴)")
    parser.add_argument("--menu", default="삼겹살 1인분", help="가격을 찾을 메뉴")
    parser.add_argument("--per-area", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true", help="DB에 넣지 않고 JSON 파일로만 저장")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.kakao_rest_api_key:
        raise SystemExit("KAKAO_REST_API_KEY가 설정되지 않았습니다")
    if not settings.anthropic_api_key:
        raise SystemExit("ANTHROPIC_API_KEY가 설정되지 않았습니다")

    claude = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    supabase = get_supabase()
    codes_by_name = {d["name_ko"]: d["code"] for d in supabase.table("districts").select("code, name_ko").execute().data}
    today = date.today().isoformat()

    records, log = [], []
    with httpx.Client(timeout=30) as kakao:
        for area in args.areas:
            for place in find_places(kakao, settings.kakao_rest_api_key, area, args.query, args.per_area):
                answer, seen, status = ask_claude(claude, place, args.menu)
                reason = validate(answer, seen) if answer else status
                log.append({"area": area, "place": place["place_name"], "place_id": place["id"], "status": reason or "saved",
                            "answer": answer, "search_result_count": len(seen)})
                print(f"[{area}] {place['place_name']}: {reason or f'{answer['price']:,}원'}")
                if reason is None:
                    records.append(to_record(place, area, args.menu, answer, codes_by_name, today))

    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"restaurant_prices_{today}.json"
    out.write_text(json.dumps({"records": records, "log": log}, ensure_ascii=False, indent=2))

    if not args.dry_run and records:
        supabase.table("restaurant_prices").upsert(records, on_conflict="place_id,menu").execute()
    print(f"식당 {len(log)}곳 중 {len(records)}곳 가격 저장{' (dry-run: DB에는 안 넣음)' if args.dry_run else ''} → {out}")


if __name__ == "__main__":
    main()
