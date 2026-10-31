-- F2 랜덤 퀴즈: Claude가 만든 문제·해설을 품목 + 가격 기준일 단위로 캐시한다.
-- 같은 품목이 다시 나오면 Claude를 다시 부르지 않는다. 가격이 갱신되면(reference_date 변경) 새로 만든다.
-- 로그인이 없으므로 일별 퀴즈(daily_quizzes)와 답안 기록(quiz_answers)은 쓰지 않는다.

create table if not exists quiz_texts (
  item_id         bigint not null references items (id) on delete cascade,
  reference_date  date not null,
  question        text not null,
  explanation     text not null,
  created_at      timestamptz not null default now(),
  primary key (item_id, reference_date)
);

alter table quiz_texts enable row level security;
