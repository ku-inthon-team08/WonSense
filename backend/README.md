# WonSense Backend

FastAPI + Supabase

## 구조

```text
backend/
├── app/
│   ├── main.py            # FastAPI 앱, CORS, 라우터 등록
│   ├── core/config.py     # 환경변수 설정
│   ├── db/supabase.py     # Supabase 클라이언트 (service role)
│   └── routers/health.py  # 헬스체크
├── requirements.txt
└── .env.example
supabase/
├── config.toml
└── migrations/            # DB 스키마
```

## 시작하기

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY 입력
uvicorn app.main:app --reload
```

- API 문서: http://localhost:8000/docs
- 연결 확인: http://localhost:8000/health/db

## DB 스키마 적용

리포 루트에서 Supabase 프로젝트에 연결한 뒤 마이그레이션을 반영한다.

```bash
supabase login
supabase link --project-ref <project-ref>
supabase db push
```

## 보안 메모

- 백엔드는 `service_role` 키로 접속하므로 RLS를 우회한다. 이 키는 `.env`에만 두고 커밋하지 않는다.
- 모든 테이블은 RLS가 켜져 있고 정책이 없어서, 프론트엔드가 `anon` 키로 직접 DB에 접근할 수 없다. 데이터는 항상 이 API를 거친다.
- `reviews.password_hash`는 API 응답에 절대 포함하지 않는다.
