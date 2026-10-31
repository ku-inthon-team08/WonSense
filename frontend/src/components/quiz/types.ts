// GET /api/quiz/random 응답. 로그인이 없어서 정답이 같이 오고 채점은 여기서 한다.
type Common = { key: string; question: string; source: string };

export type GuessQuizData = Common & {
  type: "guess";
  item_id: number;
  quiz_name: string;
  quiz_name_en?: string | null; // null until the quiz_english migration is applied
  answer_price: number;
  tolerance_correct: number;
  tolerance_close: number;
  tip: string;
  tip_en?: string | null;
  reference_date: string;
};

type QuizItem = { item_id: number; name: string; name_en?: string | null; price: number };

export type HigherLowerQuizData = Common & {
  type: "higher_lower";
  base: QuizItem;
  target: QuizItem;
  answer: "higher" | "lower";
  reference_date: string;
};

export type MenuQuizData = Common & {
  type: "menu";
  menu_name: string;
  menu_name_en?: string | null;
  shown_price: number;
  median_price: number;
  normal_low: number;
  normal_high: number;
  store_count: number;
  answer: "normal" | "above";
};

export type QuizData = GuessQuizData | HigherLowerQuizData | MenuQuizData;

// Only the answer is stored; the feedback text is built at render time so it follows a language switch.
export type Outcome = {
  result: "right" | "near" | "wrong";
  direction?: "high" | "low"; // guess quiz: was the guess above or below the average
};
