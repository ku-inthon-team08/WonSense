# WonSense Backend

FastAPI + Supabase

## 구조

```text
backend/
├── app/
│   ├── main.py            # FastAPI 앱, CORS, 라우터 등록
│   ├── core/              # 설정(config), 메모리 캐시(cache), LLM 클라이언트(claude)
│   ├── db/supabase.py     # Supabase 클라이언트 (service role), 전체 행 읽기(fetch_all)
│   ├── routers/           # API 엔드포인트: items, heatmap, quiz, reviews, stores, scan, fx, health
│   ├── services/          # 계산·매칭 로직. DB를 직접 읽지 않아서 테스트하기 쉽다
│   └── data/              # Numbeo 서울 생활물가 (바가지 판독기의 마지막 기준가)
├── scripts/               # 가격 수집 (서버가 아니라 로컬에서 실행)
├── tests/
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

## 배포 (Render)

리포 루트의 `render.yaml`(Blueprint)로 배포한다. 무료 플랜, 싱가포르 리전, `main`에 커밋되면 자동 배포.

1. [render.com](https://render.com)에 GitHub로 로그인 → **New → Blueprint** → 이 리포 선택
2. 입력하라는 값을 채운다: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `ANTHROPIC_API_KEY`
   (Claude 대신 Lablup Token Factory의 DeepSeek를 쓰려면 `LLM_BASE_URL`·`LLM_API_KEY`·`LLM_MODEL`, `.env.example` 참고)
3. 배포가 끝나면 `https://<서비스 주소>/health/db`가 `{"status":"ok","database":"connected"}`인지 확인
4. Vercel 프로젝트 → Settings → Environment Variables에 `NEXT_PUBLIC_API_URL=https://<서비스 주소>`(끝에 `/` 없이)를 넣고 **Redeploy**. 빌드할 때 코드에 박히는 값이라 다시 배포해야 반영된다

- CORS: `won-sense*.vercel.app`은 코드에서 자동 허용한다. 프론트 주소가 다르면 Render 환경변수에 `CORS_ORIGINS`를 추가한다.
- 무료 플랜은 15분 동안 요청이 없으면 잠들고, 다음 첫 요청이 30초~1분 걸린다. 시연 전에 한 번 열어 깨워 둔다.
- 가격 수집(`scripts/`)은 서버에서 돌지 않는다. 새 달 데이터는 로컬에서 실행한다.
- 가격 API는 메모리에 10분 캐시한다. 새 데이터를 넣으면 최대 10분 뒤에 화면에 반영된다 (재배포하면 바로 반영).

## 보안 메모

- 백엔드는 `service_role` 키로 접속하므로 RLS를 우회한다. 이 키는 `.env`에만 두고 커밋하지 않는다.
- 모든 테이블은 RLS가 켜져 있고 정책이 없어서, 프론트엔드가 `anon` 키로 직접 DB에 접근할 수 없다. 데이터는 항상 이 API를 거친다.
- `reviews.password_hash`는 API 응답에 절대 포함하지 않는다.
