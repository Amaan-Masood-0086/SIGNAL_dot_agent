import { notFound } from "next/navigation";

import { SessionConversation } from "@/src/components/features/session-chat/SessionConversation";
import { getChild } from "@/src/lib/api/children";
import { listSessionFlags } from "@/src/lib/api/flags";
import { getSavedResult } from "@/src/lib/api/reasoning";
import { getSession, isAuthorizationError, listObservations } from "@/src/lib/api/sessions";
import { getSessionToken } from "@/src/lib/auth/session";

export const metadata = { title: "Observation session — SIGNAL" };
export const dynamic = "force-dynamic";

// MUST #9: loading.tsx + error.tsx sit alongside; auth/absence → notFound.
export default async function SessionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const token = await getSessionToken();
  if (!token) {
    notFound();
  }

  let session;
  try {
    session = await getSession(token, id);
  } catch (error) {
    if (isAuthorizationError(error)) {
      notFound();
    }
    throw error;
  }

  // Child name is display context only; its absence must not block capture.
  let childName: string | null = null;
  try {
    const child = await getChild(token, session.child_id);
    childName = child.name;
  } catch {
    childName = null;
  }

  // Do not present a blank result or allow another screening when history
  // cannot be verified. The route error boundary provides a retry.
  const [page, flags, result] = await Promise.all([
    listObservations(token, id, 1, 100),
    listSessionFlags(token, id),
    getSavedResult(token, id),
  ]);

  return (
    <SessionConversation
      key={session.id}
      session={session}
      childName={childName}
      initialTurns={page.items}
      savedFlags={flags.items}
      savedFlagTotal={flags.total}
      initialResult={result}
    />
  );
}
