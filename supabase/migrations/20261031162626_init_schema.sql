-- WonSense 초기 스키마 (docs/MVP_SPEC.md 4. 데이터 모델 기준)
-- 모든 테이블은 RLS를 켜고 정책을 두지 않는다.
-- → anon/authenticated 키로는 접근 불가, FastAPI 백엔드(service role)만 접근한다.

create extension if not exists pg_trgm;

-- 검색/퀴즈 대상 품목
create table items (
  id              bigint generated always as identity primary key,
  name_en         text not null,
  name_ko         text not null,
  aliases         text[] not null default '{}',
  category        text not null,                 -- food / drink / goods / transport ...
  unit            text not null,                 -- per serving, per bottle ...
  quiz_enabled    boolean not null default false,
  quiz_tolerance_correct numeric(4, 3) not null default 0.10,
  quiz_tolerance_close   numeric(4, 3) not null default 0.25,
  description_en  text,
  created_at      timestamptz not null default now()
);

create index items_name_en_trgm on items using gin (name_en gin_trgm_ops);
create index items_name_ko_trgm on items using gin (name_ko gin_trgm_ops);
create index items_aliases_gin on items using gin (aliases);

-- 품목 가격 통계
create table price_stats (
  id              bigint generated always as identity primary key,
  item_id         bigint not null references items (id) on delete cascade,
  region          text not null default 'seoul', -- 'seoul' 또는 자치구 코드
  price_min       integer not null,
  price_avg       integer not null,
  price_max       integer not null,
  source          text not null,                 -- 참가격 / 서울 열린데이터 / 웹 검색 ...
  reference_date  date not null,
  created_at      timestamptz not null default now(),
  check (price_min <= price_avg and price_avg <= price_max)
);

create index price_stats_item_region_idx on price_stats (item_id, region, reference_date desc);

-- 오늘의 퀴즈
create table daily_quizzes (
  date            date primary key,
  item_id         bigint not null references items (id),
  question        text not null,
  answer_price    integer not null,
  explanation     text,
  created_at      timestamptz not null default now()
);

-- 퀴즈 답변 익명 통계
create table quiz_answers (
  id              bigint generated always as identity primary key,
  date            date not null references daily_quizzes (date) on delete cascade,
  guessed_price   integer not null,
  result          text not null check (result in ('correct', 'close', 'wrong')),
  created_at      timestamptz not null default now()
);

create index quiz_answers_date_idx on quiz_answers (date);

-- 리뷰에 태그되는 가게
create table stores (
  id              bigint generated always as identity primary key,
  name            text not null,
  category        text not null,                 -- restaurant / cafe / convenience / market ...
  district        text,                          -- 자치구
  address         text,
  created_at      timestamptz not null default now()
);

create index stores_name_trgm on stores using gin (name gin_trgm_ops);

-- 리뷰 (익명 + 글별 비밀번호)
create table reviews (
  id              bigint generated always as identity primary key,
  store_id        bigint not null references stores (id),
  nickname        text not null default 'Anonymous',
  password_hash   text not null,                 -- bcrypt 해시. 응답에 절대 포함하지 말 것
  title           text not null,
  body            text not null,
  paid_price      integer,
  price_feeling   text check (price_feeling in ('cheap', 'fair', 'expensive')),
  rating          smallint check (rating between 1 and 5),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index reviews_created_at_idx on reviews (created_at desc);
create index reviews_title_trgm on reviews using gin (title gin_trgm_ops);
create index reviews_body_trgm on reviews using gin (body gin_trgm_ops);

create or replace function set_updated_at() returns trigger
language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger reviews_set_updated_at
  before update on reviews
  for each row execute function set_updated_at();

alter table items         enable row level security;
alter table price_stats   enable row level security;
alter table daily_quizzes enable row level security;
alter table quiz_answers  enable row level security;
alter table stores        enable row level security;
alter table reviews       enable row level security;
