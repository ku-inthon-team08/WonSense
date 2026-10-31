import logging
import time

from fastapi import APIRouter, HTTPException

from app.services.fx import build_fx, fetch_rates, main_only

router = APIRouter(prefix="/api/fx", tags=["fx"])
log = logging.getLogger(__name__)

CACHE_TTL = 6 * 60 * 60  # 환율은 하루 한 번 바뀌므로 6시간 캐시. 외부 API 호출을 최소로 줄인다
RETRY_AFTER = 5 * 60  # 실패하면 이 시간 동안은 다시 부르지 않고 마지막 값을 쓴다
_cache: dict = {"at": 0.0, "data": None}


@router.get("")
def get_fx(all: bool = False) -> dict:
    """USD·JPY(100엔)·CNY·EUR의 원화 환율과 최근 14일 추이. all=true면 환율 페이지용으로 통화 20여 개를 준다.
    한 번에 전부 받아 캐시하고, 외부 API가 죽으면 마지막으로 받은 값을 준다."""
    fx = _load()
    return fx if all else main_only(fx)


def _load() -> dict:
    now = time.monotonic()
    if _cache["data"] is not None and now - _cache["at"] < CACHE_TTL:
        return _cache["data"]
    try:
        _cache["data"] = build_fx(fetch_rates())
        _cache["at"] = now
    except Exception as e:  # 네트워크 오류, 응답 형식 변경 등
        log.warning("환율 조회 실패: %s", e)
        if _cache["data"] is None:
            raise HTTPException(status_code=503, detail="환율 정보를 불러오지 못했습니다")
        _cache["at"] = now - CACHE_TTL + RETRY_AFTER
    return _cache["data"]
