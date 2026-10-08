"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { PageHeader } from "@/src/components/layout/PageHeader";
import { Alert } from "@/src/components/ui/Alert";
import { Badge } from "@/src/components/ui/Badge";
import { Input } from "@/src/components/ui/Input";
import { Button } from "@/src/components/ui/Button";
import { reviewNoteSchema, type ReviewCatalog, type ReviewEntry, type ReviewNote } from "@/src/lib/api/knowledge-review-schemas";
const labels = { pending: "Pending", changes_requested: "Changes requested", reviewed: "Reviewed" };

export function KnowledgeReviewPanel({ initial }: { initial: ReviewCatalog }) {
  const [items, setItems] = useState(initial.items);
  const [query, setQuery] = useState("");
  const [domain, setDomain] = useState("");
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState(initial.items[0]?.citation_ref ?? "");
  const [dirty, setDirty] = useState(false);
  const [draftGeneration, setDraftGeneration] = useState(0);
  const filtered = items.filter(item => (!domain || item.snapshot.entry.domain === domain) && (!status || item.workflow_status === status) && `${item.citation_ref} ${item.snapshot.entry.observation}`.toLowerCase().includes(query.toLowerCase()));
  const current = filtered.find(item => item.citation_ref === selected) ?? filtered[0];
  function allowSwitch() {
    if (!dirty) return true;
    if (!window.confirm("Discard unsaved review feedback?")) return false;
    setDraftGeneration(previous => previous + 1);
    return true;
  }
  return <main className="mx-auto w-full max-w-7xl p-5 sm:p-8">
    <PageHeader title="Knowledge base review" lede="Inspect the draft evidence and record reviewer feedback. Reviewed is a workflow status—not clinical approval or permission to activate V3." />
    <div className="my-5 flex flex-wrap gap-3 text-sm"><Badge tone="warning">Research draft · not live</Badge><span className="text-ink-soft">{initial.release_id}</span>{Object.entries(labels).map(([key, label]) => <span key={key}>{label}: {items.filter(item => item.workflow_status === key).length}</span>)}</div>
    <div className="mb-5 grid gap-3 sm:grid-cols-3">
      <Input id="kb-search" label="Search entries" value={query} onChange={event => { if (allowSwitch()) { setDirty(false); setQuery(event.target.value); } }} />
      <div><label htmlFor="kb-domain" className="block text-sm text-ink-soft">Domain</label><select id="kb-domain" value={domain} onChange={event => { if (allowSwitch()) { setDirty(false); setDomain(event.target.value); } }} className="mt-1 min-h-11 w-full rounded-lg border border-line bg-surface px-3 text-sm"><option value="">All domains</option>{[...new Set(items.map(item => item.snapshot.entry.domain))].sort().map(value => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></div>
      <div><label htmlFor="kb-status" className="block text-sm text-ink-soft">Review status</label><select id="kb-status" value={status} onChange={event => { if (allowSwitch()) { setDirty(false); setStatus(event.target.value); } }} className="mt-1 min-h-11 w-full rounded-lg border border-line bg-surface px-3 text-sm"><option value="">All statuses</option>{Object.entries(labels).map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select></div>
    </div>
    <p className="mb-3 text-sm text-ink-soft">{filtered.length} matching entries</p>
    {!current ? <Alert>No matching entries. Adjust your filters.</Alert> : <div className="grid items-start gap-6 xl:grid-cols-[minmax(240px,1fr)_minmax(0,2fr)]">
      <nav aria-label="Knowledge entries" className="max-h-80 overflow-y-auto rounded-xl border border-line bg-surface xl:max-h-[70vh]">{filtered.map(item => <button type="button" key={item.citation_ref} aria-current={current.citation_ref === item.citation_ref ? "true" : undefined} onClick={() => { if (item.citation_ref !== current.citation_ref && allowSwitch()) { setDirty(false); setSelected(item.citation_ref); } }} className={`block w-full border-b border-line p-4 text-left last:border-0 ${current.citation_ref === item.citation_ref ? "bg-moss" : "hover:bg-paper"}`}><span className="block text-xs font-semibold text-pine">{item.citation_ref} · {labels[item.workflow_status]}</span><span className="mt-2 block text-sm">{item.snapshot.entry.observation}</span></button>)}</nav>
      <ReviewDetail key={`${current.citation_ref}:${draftGeneration}`} item={current} onDirty={setDirty} onSaved={note => { setItems(previous => previous.map(item => item.citation_ref === note.citation_ref ? { ...item, workflow_status: note.status, latest_note_id: note.id, feedback_stale: false } : item)); setDirty(false); }} />
    </div>}
  </main>;
}

function ReviewDetail({ item, onSaved, onDirty }: { item: ReviewEntry; onSaved: (note: ReviewNote) => void; onDirty: (dirty: boolean) => void }) {
  const entry = item.snapshot.entry;
  const [notes, setNotes] = useState<ReviewNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState(false);
  const [dirty, setDirty] = useState(false);
  const form = useRef<HTMLFormElement>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`/api/admin/knowledge-review/${item.citation_ref}/notes`, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error("load");
      const body = await response.json();
      const parsed = reviewNoteSchema.array().parse(body.data);
      if (!controller.signal.aborted) { setNotes(parsed); setLoading(false); }
    }).catch(() => { if (!controller.signal.aborted) { setLoadError(true); setLoading(false); } });
    return () => controller.abort();
  }, [item.citation_ref]);
  useEffect(() => { if (!dirty) return; const warn = (event: BeforeUnloadEvent) => event.preventDefault(); window.addEventListener("beforeunload", warn); return () => window.removeEventListener("beforeunload", warn); }, [dirty]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (pending || loading || loadError) return;
    const data = new FormData(event.currentTarget);
    setPending(true); setSaved(false); setError(null);
    try {
      const file = data.get("attachment") as File;
      if (file?.size && (file.size > 32000 || !file.name.toLowerCase().endsWith(".txt"))) { setError("Attach a plain-text .txt file up to 32 KB, or paste the feedback."); return; }
      const response = await fetch(`/api/admin/knowledge-review/${item.citation_ref}/notes`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content_sha256: item.content_sha256, expected_note_id: notes[0]?.id ?? 0, status: data.get("status"), reviewer_name: data.get("reviewer"), feedback: data.get("feedback"), attachment_name: file?.size ? file.name : null, attachment_text: file?.size ? await file.text() : null }) });
      const body = await response.json();
      if (!response.ok) { setError(body.detail ?? "Feedback could not be saved."); return; }
      const note = reviewNoteSchema.parse(body.data);
      setNotes(previous => [note, ...previous].slice(0,20)); setSaved(true); setDirty(false); onSaved(note); form.current?.reset();
    } catch { setError("Connection failed. Your draft is still here. Reload to check whether the feedback was saved before retrying."); }
    finally { setPending(false); }
  }
  return <section aria-label="Selected knowledge entry" className="min-w-0 space-y-6">
    <header><p className="text-xs font-semibold text-pine">{item.citation_ref} · {entry.domain.replaceAll("_", " ")}</p><h2 className="mt-2 font-display text-2xl font-semibold">{entry.observation}</h2><p className="mt-3 text-sm text-ink-soft">Age: {entry.age_min_months} to under {entry.age_max_months_exclusive} months · {entry.age_semantics.replaceAll("_", " ")} · {entry.age_basis.replaceAll("_", " ")}</p></header>
    {item.feedback_stale && <Alert tone="warning">Evidence changed since the last feedback. This entry is pending again; earlier feedback remains in its history.</Alert>}
    <dl className="space-y-4 text-sm"><div><dt className="font-semibold">English follow-up</dt><dd className="mt-1">{entry.follow_up_en}</dd></div><div><dt className="font-semibold">Roman-Urdu follow-up</dt><dd className="mt-1" dir="auto">{entry.follow_up_ur_latn}</dd></div><div><dt className="font-semibold">Interpretation notes</dt><dd className="mt-1">{entry.interpretation_notes}</dd></div></dl>
    <section><h3 className="font-semibold">Primary sources</h3><ul className="mt-3 space-y-4">{item.snapshot.sources.map(source => <li key={source.source_id} className="text-sm"><a href={source.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-pine underline">{source.title}</a><p className="mt-1">{source.locator}</p><p className="mt-1 text-ink-soft">{source.limitations}</p></li>)}</ul></section>
    <form ref={form} onSubmit={submit} onChange={() => { setDirty(true); onDirty(true); setSaved(false); }} className="space-y-4 border-t border-line pt-6">
      <h3 className="font-display text-xl font-semibold">Record reviewer feedback</h3>
      <p className="text-xs text-ink-soft">Record the actual reviewer&apos;s name. This note does not verify their credentials or approve clinical use. Do not include child or patient details.</p>
      {loading && <p role="status">Loading feedback history…</p>}{loadError && <Alert tone="danger">Feedback history could not be loaded. Reload this page before submitting a review.</Alert>}{error && <Alert tone="danger">{error}</Alert>}{saved && <p role="status" className="text-sm font-semibold text-pine">Feedback saved. Live knowledge base unchanged.</p>}
      <fieldset disabled={pending || loading || loadError} className="space-y-4">
        <Input id="kb-reviewer" label="Reviewer name" name="reviewer" required maxLength={200} />
        <div><label htmlFor="kb-next-status" className="block text-sm text-ink-soft">Set workflow status</label><select id="kb-next-status" name="status" defaultValue={item.workflow_status} className="mt-1 min-h-11 w-full rounded-lg border border-line bg-surface px-3 text-sm">{Object.entries(labels).map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select></div>
        <div><label htmlFor="kb-feedback" className="block text-sm text-ink-soft">Feedback and requested corrections</label><textarea id="kb-feedback" name="feedback" required maxLength={10000} rows={5} className="mt-1 w-full rounded-lg border border-line bg-surface p-3 text-sm" /></div>
        <Input id="kb-attachment" label="Attach written feedback (.txt, up to 32 KB)" name="attachment" type="file" accept=".txt,text/plain" hint="PDF/Word: paste the relevant feedback above or export it as plain text. Binary uploads are not supported." />
        <Button type="submit">{pending ? "Saving…" : "Save review feedback"}</Button>
      </fieldset>
    </form>
    <section aria-label="Feedback history" className="border-t border-line pt-5"><h3 className="font-semibold">Feedback history</h3><p className="mt-1 text-xs text-ink-soft">Latest 20 notes. Earlier notes are preserved in the database.</p>{!loading && !loadError && notes.length === 0 && <p className="mt-3 text-sm">No feedback recorded yet.</p>}<ol className="mt-4 space-y-5">{notes.map(note => <li key={note.id} className="border-b border-line pb-4"><p className="text-sm font-semibold">{note.reviewer_name} · {labels[note.status]}</p><time dateTime={note.created_at} className="text-xs text-ink-soft">{note.created_at.slice(0,10)}</time>{note.content_sha256 !== item.content_sha256 && <p className="text-xs text-amber">Recorded against earlier evidence content.</p>}<p dir="auto" className="mt-2 whitespace-pre-wrap break-words text-sm">{note.feedback}</p>{note.attachment_text && <details className="mt-3"><summary className="cursor-pointer break-all text-sm text-pine">Attached: {note.attachment_name}</summary><pre className="mt-2 whitespace-pre-wrap break-words font-sans text-sm">{note.attachment_text}</pre></details>}</li>)}</ol></section>
  </section>;
}
