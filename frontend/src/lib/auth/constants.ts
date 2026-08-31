// Shared between middleware (edge) and server modules. Keep this file
// dependency-free: middleware must never transitively import next/headers.
export const SESSION_COOKIE = "signal_session";
