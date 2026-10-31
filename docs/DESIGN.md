# WonSense 디자인 가이드

> FE 작업 시 따라야 할 디자인 기준. 각자 작업 중인 화면이 있다면 이 문서에 맞춰 수정해 주세요.

| 항목 | 내용 |
| --- | --- |
| 문서 버전 | v0.1 (초안) |
| 작성일 | 2026-11-01 |
| 기준 코드 | `feature/frontend` 브랜치의 `frontend/` |

![홈 화면 (1440×780)](images/home.png)

---

## 0. 원칙 세 가지

1. **색·그림자는 토큰 클래스로만 쓴다.** `#BE9C34` 같은 hex 값을 컴포넌트에 직접 쓰지 않는다. 값은 [`globals.css`](../frontend/src/app/globals.css) 한 곳에만 있다.
2. **화면 문구는 [`strings.ts`](../frontend/src/lib/strings.ts)를 거친다.** 영어 버전(로드맵 1단계)을 위해 문자열을 하드코딩하지 않는다.
3. **있는 컴포넌트를 먼저 쓴다.** 섹션 제목, 검색창, 아이콘 등은 아래 [5. 컴포넌트](#5-컴포넌트)를 확인하고 새로 만들지 않는다.

---

## 1. 색

### 1.1 브랜드 토큰

[`globals.css`](../frontend/src/app/globals.css)의 `@theme`에 정의되어 있다. Tailwind 클래스로 쓴다 (`bg-brand`, `text-brand-pale`, `outline-brand` …).

| 토큰 | 값 | 쓰는 곳 |
| --- | --- | --- |
| `brand` | `#BE9C34` (금색) | 상단부 배경, 섹션 제목의 점·화살표, 주요 버튼, 링크, 아이콘 |
| `brand-pale` | `#ECE4D2` (베이지) | 페이지 배경, 상단부 태그라인 글씨, 선택된 행·드롭다운 hover 하이라이트 |

### 1.2 보조 색 (Tailwind 기본 팔레트)

| 클래스 | 쓰는 곳 |
| --- | --- |
| `bg-white` | 카드, 검색창 |
| `bg-stone-100` | 카드 안쪽의 연한 회색 박스 (예: 퀴즈 문제 영역) |
| `bg-stone-50` | 히트맵 미리보기 바탕 |
| `text-slate-900` | 기본 글씨 (body에 이미 적용) |
| `text-slate-500` / `text-slate-600` | 보조 글씨, 출처, 빈 상태 문구 |

### 1.3 쓰지 않는 색

- **보라·남색·분홍 계열** (`indigo`, `violet`, `purple`, `pink` …): create-next-app 초기 코드에서 남은 색. 보이면 `brand`로 바꾼다.
- **예외 — 의미를 가진 색**: 히트맵 색 스케일(저렴=파랑, 비쌈=빨강, `src/lib/heatmap.ts`), 퀴즈 정답/오답(초록/빨강), 오류 문구(`rose`)는 데이터·상태를 나타내므로 브랜드 색으로 바꾸지 않는다.
- 강조색이 더 필요하면 노란 계열(`yellow`, `amber`)에서 고르고, 새 토큰이 필요하면 `globals.css`에 추가한 뒤 이 문서에 적는다.

---

## 2. 글꼴

| 대상 | 글꼴 | 설정 위치 |
| --- | --- | --- |
| 기본 (전체) | 시스템 한글 폰트 (`system-ui`, Apple SD Gothic Neo, 맑은 고딕, Noto Sans KR 순) | `globals.css`의 `--font-sans` |
| 상단부 태그라인 | 나눔고딕 Bold (700) | `page.tsx`에서 `next/font/google`으로 로드 |

| 용도 | 클래스 |
| --- | --- |
| 섹션 제목 | `text-lg font-semibold` |
| 상세 페이지 제목 | `text-2xl font-bold` |
| 본문 | `text-base` |
| 출처·캡션 | `text-xs text-slate-500` |

---

## 3. 레이아웃

### 3.1 페이지 프레임

상단부와 본문이 같은 좌우 규칙을 써서 왼쪽 끝이 맞는다.

```tsx
const frame = "mx-auto w-full max-w-[1600px] px-4 md:px-10";
```

| 항목 | 모바일 | 데스크톱 (`md` 이상) |
| --- | --- | --- |
| 좌우 여백 | 16px (`px-4`) | 40px (`md:px-10`) |
| 최대 폭 | — | 1600px |
| 카드 사이 간격 | 24px (`gap-6`) | 24px |
| 본문 상하 여백 | 24px (`py-6`) | 32px (`md:py-8`) |

- **모바일 우선.** 기본 스타일은 폰 기준으로 쓰고, 넓은 화면은 `md:`로 덧붙인다.
- 홈 화면은 데스크톱에서 카드 영역이 남은 화면 높이를 꽉 채운다 (노트북 크롬 1440×780에서 스크롤 없이 한 화면).

### 3.2 상단부 (금색 띠)

홈 맨 위의 `bg-brand` 영역. 로고 + 태그라인 + 검색창이 들어간다.

| 항목 | 값 |
| --- | --- |
| 배경 | `bg-brand`, 화면 전체 폭 |
| 위 여백 | 20px (`pt-5`) / 데스크톱 28px (`md:pt-7`) |
| 아래 여백 | 32px (`pb-8`) |
| 로고 | `public/logo_hand_white.png` (흰색 손글씨 "비싼감?"), 높이 56px / 데스크톱 64px |
| 태그라인 | "서울 물가 감각의 모든 것", 나눔고딕 Bold, `text-brand-pale`, 16px / 데스크톱 20px, 로고 밑선에 맞춤 |
| 로고–검색창 간격 | 24px (`mb-6`) |

---

## 4. 카드

```tsx
const card = "flex flex-col rounded-2xl bg-white p-5 shadow-card";
```

| 항목 | 값 |
| --- | --- |
| 배경 | 흰색 |
| 모서리 | `rounded-2xl` (16px) |
| 안쪽 여백 | 20px (`p-5`) |
| 그림자 | `shadow-card` — 금색을 어둡게 한 갈색 계열의 은은한 그림자 |
| 테두리 | 없음 |

- 카드 안쪽에 영역을 나눌 때는 `rounded-xl bg-stone-100 p-4` 박스를 쓴다.
- 회색(`shadow-sm`, `shadow-md` 등) 그림자나 `border`로 입체감을 주지 않는다.
- **예외 — 떠 있는 요소**: 툴팁, 드롭다운 목록처럼 다른 요소 위에 겹쳐 뜨는 것은 `border border-slate-200 shadow-lg`를 쓴다.
- 리뷰 카드처럼 눌러서 이동하는 카드의 hover는 `hover:ring-1 hover:ring-brand/50`.

---

## 5. 컴포넌트

| 컴포넌트 | 위치 | 용도 |
| --- | --- | --- |
| `SectionHeader` | `src/components/SectionHeader.tsx` | 카드 제목. 금색 점 + 제목 + 금색 `→`, 통째로 링크 |
| `SearchBar` | `src/components/SearchBar.tsx` | 흰색 알약 모양 검색창 (`rounded-full`), 테두리·그림자·포커스 외곽선 없음 |
| `SearchIcon` | `src/components/icons/SearchIcon.tsx` | flat 돋보기 SVG. 색은 `text-*` 클래스로 지정 (`currentColor`) |
| `PlaceholderPage` | `src/components/PlaceholderPage.tsx` | 아직 안 만든 상세 페이지용 (← 홈, 제목, "준비 중") |

### 아이콘

- 이모지 대신 **선으로 그린 단색 SVG**를 쓴다 (`stroke="currentColor"`, 굵기 2.5, 둥근 끝).
- 새 아이콘은 `src/components/icons/`에 `SearchIcon`과 같은 형태로 추가한다.

### 버튼·링크

- 주요 버튼: `rounded-lg bg-brand px-4 py-2 font-medium text-white` (hover는 `hover:bg-brand/90`)
- 보조 버튼: `rounded-lg border border-brand px-4 py-2 font-medium text-brand`
- 선택된 칩/토글: `border-brand bg-brand text-white`
- 텍스트 링크: `text-brand`
- 입력칸 포커스: `focus:border-brand`

---

## 6. 문구

- 모든 화면 문구는 [`strings.ts`](../frontend/src/lib/strings.ts)의 `strings.ko`에 추가하고 `t.키이름`으로 쓴다.
- 섹션 이름은 한국어로 통일: **물가 퀴즈 · 히트맵 · 리뷰 · 검색**
- "← 홈" 링크는 `t.home`을 쓴다.

---

## 7. 아직 정하지 않은 것

정해지면 이 문서를 업데이트한다. 그 전까지는 현재 코드 상태를 따른다.

1. 입력칸·리뷰 빈 상태의 회색 테두리(`slate-300`)를 따뜻한 회색/금색 계열로 바꿀지
2. 상세 페이지(`/search`, `/quiz`, `/heatmap`, `/reviews`)에도 금색 상단부를 넣을지, 상세 페이지 최대 폭을 통일할지 (지금은 페이지마다 다름)
3. 금색 배경 위 흰 글씨·베이지 글씨의 대비가 웹 접근성 권장치(4.5:1)보다 낮은 문제를 어떻게 할지

---

## 8. 체크리스트 (PR 올리기 전)

- [ ] 컴포넌트에 hex 색을 직접 쓰지 않았다
- [ ] 보라·남색·분홍 계열 클래스가 없다
- [ ] 카드는 `shadow-card`를 쓰고 `border`/회색 그림자가 없다
- [ ] 화면 문구는 `strings.ts`를 거친다
- [ ] 섹션 제목은 `SectionHeader`를 쓴다
- [ ] 폰 폭(390px 안팎)에서 가로 스크롤 없이 보인다
