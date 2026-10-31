import { currentStrings } from "@/lib/i18n";

// All data goes through the FastAPI backend (see backend/README.md).
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

// FastAPI sends `detail` as a string (HTTPException) or a list of field errors (422).
function errorMessage(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (d as { msg?: string }).msg)
      .filter(Boolean)
      .join("\n") || fallback;
  }
  return fallback;
}

// fetch() itself rejects (no status) when the server is unreachable or CORS blocks the request.
function networkErrorMessage(): string {
  const pointsAtLocalhost = /^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(API_URL);
  const onLocalhost =
    typeof window !== "undefined" && ["localhost", "127.0.0.1"].includes(window.location.hostname);
  if (pointsAtLocalhost && !onLocalhost) {
    // Deployed build without NEXT_PUBLIC_API_URL: it fell back to the visitor's own machine.
    return currentStrings().apiNoUrl;
  }
  return currentStrings().apiUnreachable;
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      // Only with a body: on a GET this header would make the browser send a CORS preflight first.
      headers: { ...(init?.body ? { "Content-Type": "application/json" } : {}), ...init?.headers },
    });
  } catch {
    throw new ApiError(0, networkErrorMessage());
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, errorMessage(body, `${res.status} ${res.statusText}`));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}
