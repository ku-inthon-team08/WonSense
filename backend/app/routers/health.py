from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.db.supabase import get_supabase

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict:
    return {"status": "ok"}


@router.get("/db")
def health_db(supabase: Client = Depends(get_supabase)) -> dict:
    try:
        supabase.table("items").select("id").limit(1).execute()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Supabase connection failed: {e}")
    return {"status": "ok", "database": "connected"}
