-- F2 퀴즈를 짧은 고정 형식으로 바꾼다. 문제 문장은 코드의 템플릿으로 만들고,
-- LLM은 영어 이름(name_en)과 구매 팁(tip)만 만든다. 기존 캐시는 새 형식과 맞지 않아 지운다.

delete from quiz_texts;

alter table quiz_texts
  drop column question,
  drop column explanation,
  add column name_en text not null,
  add column tip text not null;
