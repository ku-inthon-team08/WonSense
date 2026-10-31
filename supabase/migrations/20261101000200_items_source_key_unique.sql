-- items.source_key의 부분 유니크 인덱스(where source_key is not null)는
-- ON CONFLICT (source_key) 대상이 될 수 없어서 수집 스크립트의 upsert가 실패한다.
-- 일반 유니크 제약으로 바꾼다. NULL은 서로 다른 값으로 취급되므로 source_key가 없는 품목은 여전히 여러 개 둘 수 있다.

drop index if exists items_source_key_uniq;

alter table items
  add constraint items_source_key_key unique (source_key);
