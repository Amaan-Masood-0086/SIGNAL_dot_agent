import type { NextConfig } from "next";

// web-development.md MUST #2: security headers on all HTML responses.
// Content-Security-Policy is NOT here: it needs a per-request nonce, so it
// is set in middleware.ts instead. These five are static and belong here.
// NOTE: microphone is explicitly needed for this product — never use the
// generic template's microphone=() blanket block (web-development.md §Voice).
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(self), geolocation=()",
  },
  { key: "X-Frame-Options", value: "DENY" },
  {
    key: "Strict-Transport-Security",
    value: "max-age=31536000; includeSubDomains; preload",
  },
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Remove the framework banner — free reconnaissance for an attacker
  // (OWASP A02 information disclosure).
  poweredByHeader: false,
  // MUST NOT serve source maps publicly in production (web-development.md #6).
  productionBrowserSourceMaps: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
