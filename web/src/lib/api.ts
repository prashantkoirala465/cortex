const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `request failed with status ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

async function parseResponse(res: Response) {
  if (res.status === 204) return null;

  const text = await res.text();
  const body = text ? JSON.parse(text) : null;

  if (!res.ok) {
    throw new ApiError(res.status, body?.detail ?? body);
  }
  return body;
}

/** Low-level fetch wrapper. `credentials: "include"` so the httpOnly
 * refresh cookie rides along on auth endpoints; harmless elsewhere. */
export async function apiFetch(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  return parseResponse(res);
}

export function withAuth(token: string | null): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {};
}
