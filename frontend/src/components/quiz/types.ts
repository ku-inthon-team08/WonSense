// GET /api/quiz/random 응답. 로그인이 없어서 정답이 같이 오고 채점은 여기서 한다.
type Common = { key: string; question: string; source: string };

export type GuessQuizData = Common & {
  type: "guess";
  item_id: number;
  quiz_name: string;
  answer_price: number;
  tolerance_correct: number;
  tolerance_close: number;
  tip: string;
  reference_date: string;
};

export type HigherLowerQuizData = Common & {
  type: "higher_lower";
  base: { item_id: number; name: string; price: number };
  target: { item_id: number; name: string; price: number };
  answer: "higher" | "lower";
  reference_date: string;
};

export type MenuQuizData = Common & {
  type: "menu";
  menu_name: string;
  shown_price: number;
  median_price: number;
  normal_low: number;
  normal_high: number;
  store_count: number;
  answer: "normal" | "above";
};

export type QuizData = GuessQuizData | HigherLowerQuizData | MenuQuizData;

export type Outcome = {
  result: "right" | "near" | "wrong";
  feedback: string;
  tip?: string;
};
