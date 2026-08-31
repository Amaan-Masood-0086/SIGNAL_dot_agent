// Server-only typed fetch wrapper for the SIGNAL backend. Import this file
// ONLY from server code (route handlers / Server Components) — MUST-NOT #12.

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

interface BackendInit {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: string;
}

export async function backendFetch<T>(
  path: string,
  token: string,
  init: BackendInit = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}${path}`, {
      method: init.method ?? "GET",
      body: init.body,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      // MUST #18: authenticated data is never cached.
      cache: "no-store",
    });
  } catch {
    throw new ApiError(502, "Backend unavailable");
  }

  if (!response.ok) {
    throw new ApiError(response.status, `Backend responded ${response.status}`);
  }
  return (await response.json()) as T;
}

// Multipart variant for the FEAT-03 audio upload. Content-Type is NOT set:
// fetch generates the multipart boundary, which must reach the backend intact.
export async function backendFetchForm<T>(
  path: string,
  token: string,
  form: FormData,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}${path}`, {
      method: "POST",
      body: form,
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(502, "Backend unavailable");
  }

  if (!response.ok) {
    throw new ApiError(response.status, `Backend responded ${response.status}`);
  }
  return (await response.json()) as T;
}
