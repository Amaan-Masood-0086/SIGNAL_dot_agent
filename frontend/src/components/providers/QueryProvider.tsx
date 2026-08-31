"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

// TanStack Query v5 setup (web-development.md Step 4) — all server data
// flows through query hooks; the client is created once per browser session.
export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Authenticated data is never cached across navigations longer
            // than the active session (MUST #18 spirit).
            staleTime: 0,
            retry: false,
          },
        },
      }),
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
