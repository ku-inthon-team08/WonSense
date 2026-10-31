-- F1 검색용 식당 메뉴 가격: 서울시 가격안정 모범업소(착한가격업소) 상품목록
-- 서울 열린데이터광장 ListPriceModelStoreProductService. 한 행 = 가게 하나의 메뉴 하나.
-- 착한가격업소만 모은 데이터라 일반 시세보다 낮게 나온다 (화면에 그렇게 표시한다).

create table if not exists menu_prices (
  store_id        text not null,                 -- SH_ID
  menu_name       text not null,                 -- IM_NAME
  store_name      text not null,                 -- SH_NAME
  industry        text not null,                 -- INDUTY_CODE_SE_NAME (한식, 중식, 이미용 ...)
  address         text,                          -- SH_ADDR
  district_code   text references districts (code), -- 주소에서 뽑은 자치구 (못 찾으면 null)
  price           integer not null check (price > 0), -- IM_PRICE
  fetched_on      date not null,                 -- 수집한 날. 이번 수집에 없던 행은 지운다
  primary key (store_id, menu_name)
);

create index if not exists menu_prices_industry_idx on menu_prices (industry);

alter table menu_prices enable row level security;
