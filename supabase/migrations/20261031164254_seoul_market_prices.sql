-- 서울시 생필품 농수축산물 가격 정보 (서울 열린데이터광장 ListNecessariesPricesService)
-- F3 히트맵 데이터. 자세한 설명은 docs/DB_DESIGN.md 참고

-- 자치구. code는 행정표준 시군구 코드(5자리)
-- API의 M_GU_CODE는 '110000'과 '11110'이 섞여 있으므로 수집 시 이 코드로 정규화한다
create table districts (
  code            text primary key,
  name_ko         text not null unique,
  name_en         text not null
);

insert into districts (code, name_ko, name_en) values
  ('11110', '종로구',   'Jongno-gu'),
  ('11140', '중구',     'Jung-gu'),
  ('11170', '용산구',   'Yongsan-gu'),
  ('11200', '성동구',   'Seongdong-gu'),
  ('11215', '광진구',   'Gwangjin-gu'),
  ('11230', '동대문구', 'Dongdaemun-gu'),
  ('11260', '중랑구',   'Jungnang-gu'),
  ('11290', '성북구',   'Seongbuk-gu'),
  ('11305', '강북구',   'Gangbuk-gu'),
  ('11320', '도봉구',   'Dobong-gu'),
  ('11350', '노원구',   'Nowon-gu'),
  ('11380', '은평구',   'Eunpyeong-gu'),
  ('11410', '서대문구', 'Seodaemun-gu'),
  ('11440', '마포구',   'Mapo-gu'),
  ('11470', '양천구',   'Yangcheon-gu'),
  ('11500', '강서구',   'Gangseo-gu'),
  ('11530', '구로구',   'Guro-gu'),
  ('11545', '금천구',   'Geumcheon-gu'),
  ('11560', '영등포구', 'Yeongdeungpo-gu'),
  ('11590', '동작구',   'Dongjak-gu'),
  ('11620', '관악구',   'Gwanak-gu'),
  ('11650', '서초구',   'Seocho-gu'),
  ('11680', '강남구',   'Gangnam-gu'),
  ('11710', '송파구',   'Songpa-gu'),
  ('11740', '강동구',   'Gangdong-gu');

-- 조사 대상 시장/마트. id = API의 M_SEQ
create table markets (
  id              bigint primary key,
  name            text not null,                 -- M_NAME
  type_code       text not null,                 -- M_TYPE_CODE (001 전통시장 / 002 대형마트)
  type_name       text not null,                 -- M_TYPE_NAME
  district_code   text not null references districts (code),
  created_at      timestamptz not null default now()
);

create index markets_district_idx on markets (district_code);

-- 조사 상품 (규격 단위). id = API의 A_SEQ
-- 같은 품목(쌀)이라도 규격(10kg/4kg)이 다르면 다른 상품이므로 평균은 상품 단위로 낸다
create table market_products (
  id              bigint primary key,
  name            text not null,                 -- A_NAME  예) 쌀(이천쌀) 10kg 1포
  category_code   text not null,                 -- PRDLST_CD
  category_name   text not null,                 -- PRDLST_NM 예) 쌀
  unit            text,                          -- UNIT     예) 10kg
  quantity        text,                          -- QY       예) 1포
  item_id         bigint references items (id) on delete set null, -- F1/F2 품목과 연결 (선택)
  created_at      timestamptz not null default now()
);

create index market_products_category_idx on market_products (category_code);
create index market_products_item_idx on market_products (item_id);

-- 가격 조사 결과. id = API의 P_SEQ (한 달에 여러 번 조사되므로 시장+상품+월은 유일하지 않음)
create table market_prices (
  id              bigint primary key,
  market_id       bigint not null references markets (id),
  product_id      bigint not null references market_products (id),
  price           integer not null check (price > 0), -- A_PRICE
  brand           text,                          -- SPCIES
  note            text,                          -- ADD_COL (할인 / 행사가 / 세일 ...)
  year_month      date not null,                 -- P_YEAR_MONTH, 해당 월 1일로 저장
  surveyed_on     date not null,                 -- P_DATE
  created_at      timestamptz not null default now()
);

create index market_prices_month_product_idx on market_prices (year_month, product_id);
create index market_prices_market_idx on market_prices (market_id);

-- 월·자치구·상품별 평균가 (할인/행사 가격 제외)
create view district_product_prices with (security_invoker = true) as
select
  p.year_month,
  m.district_code,
  p.product_id,
  round(avg(p.price))::integer as avg_price,
  count(*)                     as sample_count
from market_prices p
join markets m on m.id = p.market_id
where p.note is null
group by p.year_month, m.district_code, p.product_id;

-- 월·상품별 서울 평균가 (할인/행사 가격 제외)
create view seoul_product_prices with (security_invoker = true) as
select
  year_month,
  product_id,
  round(avg(price))::integer as avg_price,
  count(*)                   as sample_count
from market_prices
where note is null
group by year_month, product_id;

-- 월·자치구별 물가 지수 (서울 평균 = 100)
-- 자치구에서 조사된 상품마다 (구 평균 / 서울 평균)을 구해 평균낸 값
create view district_price_index with (security_invoker = true) as
select
  d.year_month,
  d.district_code,
  round(avg(d.avg_price::numeric / s.avg_price) * 100, 1) as price_index,
  count(*)                                                as product_count
from district_product_prices d
join seoul_product_prices s using (year_month, product_id)
group by d.year_month, d.district_code;

alter table districts       enable row level security;
alter table markets         enable row level security;
alter table market_products enable row level security;
alter table market_prices   enable row level security;
