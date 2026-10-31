import type { ReactNode } from "react";

// Inline error: what failed, the server's message, and optionally a retry button (children).
export function ErrorBox({ title, message, children }: { title: string; message: string; children?: ReactNode }) {
  return (
    <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
      <p>{title}</p>
      <p className="mt-1 text-xs opacity-80">{message}</p>
      {children}
    </div>
  );
}
