-- F1 검색용 마트·편의점 공산품 가격: 한국소비자원 참가격 생필품 가격 정보 (공공데이터포털 15083256)
-- 원본은 판매점별 가격(월 20만여 행)이고 지역 정보가 없어 전국 기준이다.
-- 수집할 때 상품별로 요약해서 상품 하나당 한 행만 저장한다 (원본 행은 저장하지 않는다).
-- 세일·1+1 가격은 빼고 정상가로만 계산한다.

create table if not exists product_prices (
  product_name      text primary key,           -- 상품명 (예: 참이슬 후레쉬(360ml))
  manufacturer      text,                       -- 제조사 (가장 많이 나온 값)
  price_low         integer not null,           -- 정상가 25번째 백분위 ("보통" 범위 아래)
  price_median      integer not null,
  price_high        integer not null,           -- 정상가 75번째 백분위 ("보통" 범위 위)
  price_min         integer not null,
  price_max         integer not null,
  store_count       integer not null,           -- 정상가로 조사된 판매점 수
  convenience_price integer,                    -- 편의점(CU·GS25·세븐일레븐·이마트24) 정상가 중앙값, 없으면 null
  reference_date    date not null,              -- 조사일
  check (price_low <= price_median and price_median <= price_high)
);

alter table product_prices enable row level security;
