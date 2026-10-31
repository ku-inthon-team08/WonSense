-- 히트맵용 확장: 서울 열린데이터광장 생필품 가격(상품 규격 단위)을 구별로 집계해 저장한다.
-- items 한 행 = 규격까지 포함한 상품(A_NAME). 예: "쌀 10kg", "쌀 4kg"은 서로 다른 item.

alter table items
  add column source_key text;                      -- 수집 원본의 상품명(A_NAME). upsert 키

create unique index items_source_key_uniq on items (source_key) where source_key is not null;

alter table price_stats
  add column region_name  text,                    -- 자치구 이름 (M_GU_NAME)
  add column sample_count integer not null default 0;

-- 월별 재수집 시 같은 값을 덮어쓸 수 있게 한다
create unique index price_stats_upsert_uniq
  on price_stats (item_id, region, reference_date, source);
