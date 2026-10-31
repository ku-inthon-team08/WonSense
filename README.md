# WonSense

물가 감각 — 서울의 물가 감각을 외국인에게 알려주는 서비스

- [MVP 기획서](docs/MVP_SPEC.md)
- [디자인 가이드](docs/DESIGN.md)
- [Backend (FastAPI)](backend/README.md)
- [Frontend (Next.js)](frontend/README.md)

## Run locally

프론트엔드 실행:

```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL 설정
npm run dev                  # http://localhost:3000
```

백엔드는 [Backend 시작 안내](backend/README.md)를 참고하세요.

## Structure

| Path | What |
| --- | --- |
| `frontend/src/app/page.tsx` | 홈: ① 검색, ② 퀴즈·환율, ③ 물가 지도, ④ 리뷰 |
| `frontend/src/app/{search,quiz,heatmap,reviews,scan}` | 기능 페이지 |
| `frontend/src/components/` | 기능별 UI (`quiz`, `heatmap`, `reviews`, `scan`, `search`, `fx`) |
| `frontend/src/lib/api.ts` | FastAPI 백엔드 요청 도우미 |
| `frontend/src/lib/strings.ts` | 한국어·영어 UI 문자열 |
| `backend/app/` | FastAPI 앱: 라우터(API), 서비스(계산), Supabase 연결 |
| `backend/scripts/` | 가격 데이터 수집 스크립트 (로컬에서 실행) |
| `supabase/migrations/` | 데이터베이스 마이그레이션 |
