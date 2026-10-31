from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from supabase import Client

from app.db.supabase import get_supabase
from app.services.reviews import clean_search_term

router = APIRouter(prefix="/api/stores", tags=["stores"])

STORE_COLUMNS = "id, name, category, district, address"

StoreCategory = Literal["restaurant", "cafe", "bar", "convenience", "market", "shop", "other"]


class StoreCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: StoreCategory
    district: str | None = Field(None, max_length=20, description="자치구 이름 (예: 강남구)")
    address: str | None = Field(None, max_length=200)


def find_or_create_store(supabase: Client, store: StoreCreate) -> dict:
    """이름과 자치구가 같은 가게가 있으면 그 가게를, 없으면 새로 만들어 돌려준다."""
    name = store.name.strip()
    query = supabase.table("stores").select(STORE_COLUMNS).eq("name", name)
    query = query.eq("district", store.district) if store.district else query.is_("district", "null")
    existing = query.limit(1).execute().data
    if existing:
        return existing[0]
    return (
        supabase.table("stores")
        .insert({**store.model_dump(), "name": name})
        .execute()
        .data[0]
    )


@router.get("")
def search_stores(
    q: str = Query("", description="가게 이름 자동완성"),
    limit: int = Query(10, ge=1, le=50),
    supabase: Client = Depends(get_supabase),
) -> list[dict]:
    query = supabase.table("stores").select(STORE_COLUMNS).order("name").limit(limit)
    term = clean_search_term(q)
    if term:
        query = query.ilike("name", f"%{term}%")
    return query.execute().data


@router.post("", status_code=201)
def create_store(store: StoreCreate, supabase: Client = Depends(get_supabase)) -> dict:
    return find_or_create_store(supabase, store)
