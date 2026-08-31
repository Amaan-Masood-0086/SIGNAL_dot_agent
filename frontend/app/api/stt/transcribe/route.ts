import { NextResponse, type NextRequest } from "next/server";

import { SESSION_COOKIE } from "@/src/lib/auth/constants";
import { isSameOrigin } from "@/src/lib/auth/csrf";
import { ApiError } from "@/src/lib/api/client";
import { transcribeAudio } from "@/src/lib/api/sessions";

// Voice mode only (FEAT-03). The browser records a clip with MediaRecorder
// and POSTs it here; this route forwards it to the backend STT seam. The text
// fallback never touches this route — zero STT dependency for typed input.
export async function POST(request: NextRequest) {
  if (!isSameOrigin(request)) {
    return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  }
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  let audio: Blob;
  try {
    const form = await request.formData();
    const file = form.get("audio");
    if (!(file instanceof Blob) || file.size === 0) {
      return NextResponse.json({ detail: "Missing audio" }, { status: 422 });
    }
    audio = file;
  } catch {
    return NextResponse.json({ detail: "Invalid audio payload" }, { status: 422 });
  }

  try {
    const transcript = await transcribeAudio(token, audio);
    return NextResponse.json({ transcript });
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return NextResponse.json({ detail: "Not permitted" }, { status: error.status });
    }
    // 503 = STT not configured: surface distinctly so the UI can fall back
    // to text without treating it as a crash.
    if (error instanceof ApiError && error.status === 503) {
      return NextResponse.json(
        { detail: "Voice input is unavailable; use the text box" },
        { status: 503 },
      );
    }
    if (error instanceof ApiError && error.status === 413) {
      return NextResponse.json({ detail: "Recording is too long" }, { status: 413 });
    }
    if (error instanceof ApiError && error.status === 429) {
      return NextResponse.json(
        { detail: "Too many requests; try again in a minute" },
        { status: 429 },
      );
    }
    return NextResponse.json({ detail: "Transcription failed" }, { status: 502 });
  }
}
