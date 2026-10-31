import Link from "next/link";

export default function QuizPage() {
  return (
    <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
      <Link href="/" className="text-sm text-indigo-600">← Home</Link>
      <h1 className="mt-2 text-2xl font-bold">Quiz</h1>
      <p className="mt-2 text-slate-500">준비 중</p>
    </main>
  );
}
