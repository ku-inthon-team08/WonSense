from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache
def get_supabase() -> Client:
    # service role 키를 쓰므로 RLS를 우회한다. 이 클라이언트는 서버 안에서만 사용할 것
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
