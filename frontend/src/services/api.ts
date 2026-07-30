/* ──────────────────────────────────────────────
   API Client — fetch wrapper tipado
   ────────────────────────────────────────────── */

const BASE_URL = import.meta.env.VITE_API_URL ?? '';

class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API Error ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
    this.name = 'ApiError';
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const url = `${BASE_URL}${path}`;

  const headers: Record<string, string> = {};
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const errBody = await res.json();
      if (typeof errBody.detail === 'string') {
        detail = errBody.detail;
      } else if (Array.isArray(errBody.detail)) {
        detail = errBody.detail.map((e: { msg: string }) => e.msg).join('; ');
      }
    } catch {
      // ignore parse errors
    }
    throw new ApiError(res.status, detail);
  }

  // 204 No Content (DELETE, etc.)
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export const api = {
  get<T>(path: string): Promise<T> {
    return request<T>('GET', path);
  },

  post<T>(path: string, body: unknown): Promise<T> {
    return request<T>('POST', path, body);
  },

  put<T>(path: string, body: unknown): Promise<T> {
    return request<T>('PUT', path, body);
  },

  del<T = void>(path: string): Promise<T> {
    return request<T>('DELETE', path);
  },
};

export { ApiError };
