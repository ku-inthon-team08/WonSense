# WonSense
물가 감각 — 서울의 물가 감각을 외국인에게 알려주는 서비스

- [MVP 기획서](docs/MVP_SPEC.md)

## Run locally

```bash
npm install
cp .env.example .env.local   # fill in the secrets
npm run dev                  # http://localhost:3000
```

## Structure

| Path | What |
| --- | --- |
| `src/app/page.tsx` | Home (① search, ② quiz, ③ heat map, ④ review) |
| `src/app/{search,quiz,heatmap,reviews}` | Feature pages (stubs) |
| `src/components/quiz/` | F2 quiz UI |
| `src/lib/strings.ts` | All UI strings (for the English version later) |
