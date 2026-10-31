-- 식당 메뉴 가격 (LLM 웹 검색으로 수집): scripts/mine_restaurant_prices.py
-- 식당 목록은 카카오 로컬 API, 가격은 Claude 웹 검색으로 찾는다.
-- 웹 검색 결과는 틀리거나 오래됐을 수 있으므로 가격마다 출처 URL과 근거 문장을 저장하고,
-- 사람이 확인한 행만 verified = true 로 표시한다. 화면에는 "웹 검색 기반 추정"으로 보여준다.

create table if not exists restaurant_prices (
  place_id        text not null,                 -- 카카오 장소 ID
  menu            text not null,                 -- 찾은 메뉴 (예: 삼겹살 1인분)
  place_name      text not null,
  area            text not null,                 -- 수집할 때 쓴 지역 검색어 (예: 명동)
  district_code   text references districts (code),
  address         text,
  lat             double precision,
  lng             double precision,
  category        text,                          -- 카카오 업종 (음식점 > 한식 > 육류,고기 > 삼겹살)
  place_url       text,                          -- 카카오맵 장소 페이지
  price           integer not null check (price > 0),
  weight_g        integer check (weight_g > 0),  -- 1인분 중량, 모르면 null
  source_url      text not null,                 -- 가격을 찾은 웹 페이지 (웹 검색 결과에 실제로 있었던 URL만)
  source_quote    text,                          -- 그 페이지에서 가격이 적힌 부분
  model           text not null,                 -- 가격을 찾은 모델
  checked_on      date not null,
  verified        boolean not null default false, -- 사람이 출처를 열어 확인했는지
  primary key (place_id, menu)
);

create index if not exists restaurant_prices_area_idx on restaurant_prices (area, menu);

alter table restaurant_prices enable row level security;
