// Picks the quiz text for the current language. The server sends Korean text plus English names where it has them.
import type { Strings } from "@/lib/strings";
import type { Outcome, QuizData } from "./types";

const pick = (t: Strings, ko: string, en?: string | null) => (t.lang === "en" && en ? en : ko);

export function quizName(t: Strings, quiz: QuizData): string {
  if (quiz.type === "guess") return pick(t, quiz.quiz_name, quiz.quiz_name_en);
  if (quiz.type === "menu") return pick(t, quiz.menu_name, quiz.menu_name_en);
  return pick(t, quiz.target.name, quiz.target.name_en);
}

export function quizQuestion(t: Strings, quiz: QuizData): string {
  if (quiz.type === "guess")
    return t.quizGuessQuestion && quiz.quiz_name_en ? t.quizGuessQuestion(quiz.quiz_name_en) : quiz.question;
  if (quiz.type === "higher_lower" && t.quizHigherLowerQuestion)
    return t.quizHigherLowerQuestion(
      pick(t, quiz.target.name, quiz.target.name_en),
      pick(t, quiz.base.name, quiz.base.name_en),
      quiz.base.price,
    );
  if (quiz.type === "menu" && t.quizMenuQuestion) return t.quizMenuQuestion(quizName(t, quiz), quiz.shown_price);
  return quiz.question;
}

export function quizFeedback(t: Strings, quiz: QuizData, outcome: Outcome): string {
  if (quiz.type === "guess") return t.quizFeedback.guess(outcome.result, outcome.direction ?? "low", quiz.answer_price);
  if (quiz.type === "higher_lower") return t.quizFeedback.higherLower(quizName(t, quiz), quiz.target.price);
  return t.quizFeedback.menu(quiz.answer, quiz.normal_low, quiz.normal_high);
}

export function quizTip(t: Strings, quiz: QuizData): string | null {
  if (quiz.type !== "guess") return null;
  // No English tip yet → hide it rather than show Korean in the English UI.
  return (t.lang === "ko" ? quiz.tip : quiz.tip_en) || null;
}
