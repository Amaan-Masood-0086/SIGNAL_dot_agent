import type { NextConfig } from "next";

// web-development.md MUST #2: security headers on all HTML responses.
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
