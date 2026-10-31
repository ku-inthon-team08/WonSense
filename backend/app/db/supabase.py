import threading

from supabase import Client, create_client

from app.core.config import get_settings

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
