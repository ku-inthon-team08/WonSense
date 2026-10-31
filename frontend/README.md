# WonSense Frontend

Next.js (App Router) + Tailwind. Talks only to the FastAPI backend.

```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL
npm run dev                  # http://localhost:3000
```

| Path | What |
| --- | --- |
| `src/app/page.tsx` | Home: ① search, ② quiz, ③ heat map, ④ review |
| `src/app/{search,quiz,heatmap,reviews}` | Feature pages (stubs for now) |
| `src/components/quiz/` | F2 quiz UI |
| `src/lib/api.ts` | Fetch helper for the backend |
| `src/lib/strings.ts` | All UI strings (for the English version later) |
