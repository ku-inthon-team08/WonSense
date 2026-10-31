from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import health, heatmap, items, quiz, reviews, stores

settings = get_settings()

app = FastAPI(title="WonSense API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(items.router)
app.include_router(heatmap.router)
app.include_router(quiz.router)
app.include_router(stores.router)
app.include_router(reviews.router)
