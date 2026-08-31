import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";

// Route protection (web-development.md Step 3). Next 16's `proxy` convention
// (formerly middleware). Signature verification of the JWT happens on the
// backend on every API call — the proxy enforces session presence and the
// no-cache rule for authenticated HTML.
export function proxy(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  // MUST #18 / MUST-NOT #8: authenticated HTML is never cached at CDN/edge.
  const response = NextResponse.next();
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
