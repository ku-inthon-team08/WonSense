import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.supabase import get_supabase
from app.routers import fx, health, heatmap, items, quiz, reviews, scan, stores

logger = logging.getLogger(__name__)
settings = get_settings()


def _preload() -> None:
    """품목·식당 메뉴 가격을 미리 캐시에 올린다. 안 하면 서버가 깬 뒤 첫 판독이 Supabase 로딩(약 6초)을 기다린다."""
    try:
        supabase = get_supabase()
        items.get_items(supabase)
        items.get_menus(supabase)
    except Exception as e:  # 미리 못 올려도 첫 요청이 다시 불러온다
        logger.warning("시작 시 미리 불러오기 실패: %s", e)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 백그라운드로 돌려서 서버는 바로 요청을 받는다
    threading.Thread(target=_preload, daemon=True).start()
    yield


app = FastAPI(title="WonSense API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(fx.router)
app.include_router(items.router)
app.include_router(heatmap.router)
app.include_router(quiz.router)
app.include_router(stores.router)
app.include_router(reviews.router)
app.include_router(scan.router)
