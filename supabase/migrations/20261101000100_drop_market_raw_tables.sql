-- 히트맵은 price_stats에 구별 집계값을 저장하는 방식(20261101000000_heatmap_price_stats.sql)으로 통일한다.
-- 원본 행을 저장하던 테이블과 뷰는 쓰지 않으므로 삭제한다.
-- districts는 남긴다: price_stats.region(자치구 코드)의 이름·영문명 조회에 쓴다.

drop view if exists district_price_index;
drop view if exists district_product_prices;
drop view if exists seoul_product_prices;

drop table if exists market_prices;
drop table if exists market_products;
drop table if exists markets;
