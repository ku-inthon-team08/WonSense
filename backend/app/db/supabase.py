import threading
from collections.abc import Callable
from typing import Any

from supabase import Client, create_client

from app.core.config import get_settings

PAGE = 1000  # PostgREST가 한 응답에 주는 최대 행 수

_local = threading.local()


def get_supabase() -> Client:
    # service role 키를 쓰므로 RLS를 우회한다. 이 클라이언트는 서버 안에서만 사용할 것
    # 동기 엔드포인트는 스레드풀에서 동시에 돌고, 클라이언트의 HTTP/2 연결은 스레드 간에 공유하면
    # 요청이 겹칠 때 ReadError가 난다. 그래서 스레드마다 클라이언트를 하나씩 둔다.
    client = getattr(_local, "client", None)
    if client is None:
        settings = get_settings()
        client = _local.client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return client


def fetch_all(build_query: Callable[[], Any]) -> list[dict]:
    """조건에 맞는 행을 끝까지 나눠 받는다.

    build_query는 호출할 때마다 새 쿼리를 만들어야 한다: range()는 값을 덮어쓰지 않고 쌓여서 쿼리를 재사용할 수 없다.
    페이지 사이에 행이 빠지거나 겹치지 않도록 쿼리는 유일한 컬럼까지 포함해 정렬해 둔다.
    """
    rows: list[dict] = []
    while True:
        batch = build_query().range(len(rows), len(rows) + PAGE - 1).execute().data
        rows.extend(batch)
        if len(batch) < PAGE:
            return rows
