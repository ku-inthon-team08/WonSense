# WonSense Frontend

Next.js (App Router) + Tailwind. Talks only to the FastAPI backend, except for store search in the review form, which uses the Kakao Maps SDK.

```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL
npm run dev                  # http://localhost:3000
```

| Path | What |
| --- | --- |
| `src/app/page.tsx` | Home: ① search, ② quiz, ③ heat map, ④ review |
| `src/app/reviews` | F4 review board: list/search, `new`, `[id]` (detail, edit, delete) |
| `src/app/{search,quiz,heatmap}` | Feature pages (stubs for now) |
| `src/components/reviews/` | F4 review UI (store picker, form, password dialog) |
| `src/lib/reviews.ts` | Review/store types and API calls |
| `src/components/quiz/` | F2 quiz UI |
| `src/lib/api.ts` | Fetch helper for the backend |
| `src/lib/kakao.ts` | Kakao place search for the review form |
| `src/lib/strings.ts` | All UI strings (for the English version later) |
