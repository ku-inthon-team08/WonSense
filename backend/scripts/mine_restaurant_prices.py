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


def load_attempts(path: Path) -> set[str]:
    """이전 실행에서 이미 시도한 장소 ID (가격을 못 찾은 곳 포함). 다시 돌릴 때 비용을 두 번 쓰지 않게 건너뛴다."""
    if not path.exists():
        return set()
    return {json.loads(line)["place_id"] for line in path.read_text().splitlines() if line.strip()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--areas", nargs="+", default=DEFAULT_AREAS)
    parser.add_argument("--query", default="삼겹살", help="카카오 검색어 (업종/메뉴)")
    parser.add_argument("--menu", default="삼겹살 1인분", help="가격을 찾을 메뉴")
    parser.add_argument("--per-area", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true", help="DB에 넣지 않고 JSON 파일로만 저장")
    parser.add_argument("--retry", action="store_true", help="이미 시도한 식당도 다시 찾기")
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

    # 시도 기록은 한 줄에 한 식당씩 바로바로 남긴다 (중간에 멈춰도 결과가 남고, 다시 돌리면 이어서 한다)
    OUT_DIR.mkdir(exist_ok=True)
    attempts_path = OUT_DIR / f"attempts_{args.menu.replace(' ', '_')}{'_dry' if args.dry_run else ''}.jsonl"
    done = set() if args.retry else load_attempts(attempts_path)
    if not args.retry and not args.dry_run:
        done |= {
            r["place_id"]
            for r in supabase.table("restaurant_prices").select("place_id").eq("menu", args.menu).execute().data
        }

    tried = saved = skipped = 0
    stop_reason = None
    with httpx.Client(timeout=30) as kakao, attempts_path.open("a") as attempts:
        for area in args.areas:
            if stop_reason:
                break
            for place in find_places(kakao, settings.kakao_rest_api_key, area, args.query, args.per_area):
                if str(place["id"]) in done:
                    skipped += 1
                    continue
                try:
                    answer, seen, status = ask_claude(claude, place, args.menu)
                except anthropic.RateLimitError:
                    stop_reason = "Claude API 사용량 한도(429)에 걸렸습니다. 잠시 뒤 다시 실행하면 이어서 합니다"
                    break
                except anthropic.APIStatusError as e:
                    # 크레딧 부족·키 오류 등: 더 돌려도 계속 실패하므로 멈춘다
                    stop_reason = f"Claude API 오류로 멈춥니다 ({e.status_code}): {e.message}"
                    break
                tried += 1
                reason = validate(answer, seen) if answer else status
                record = None if reason else to_record(place, area, args.menu, answer, codes_by_name, today)
                if record and not args.dry_run:
                    supabase.table("restaurant_prices").upsert(record, on_conflict="place_id,menu").execute()
                saved += record is not None
                attempts.write(json.dumps({"place_id": str(place["id"]), "area": area, "place": place["place_name"],
                                           "status": reason or "saved", "answer": answer, "record": record,
                                           "search_result_count": len(seen), "checked_on": today}, ensure_ascii=False) + "\n")
                attempts.flush()
                print(f"[{area}] {place['place_name']}: {reason or f'{answer['price']:,}원'}", flush=True)

    note = " (dry-run: DB에는 안 넣음)" if args.dry_run else ""
    print(f"이번 실행: {tried}곳 시도, {saved}곳 저장{note}, 이미 한 곳 {skipped}곳 건너뜀 → {attempts_path}")
    if stop_reason:
        raise SystemExit(stop_reason)


if __name__ == "__main__":
    main()
