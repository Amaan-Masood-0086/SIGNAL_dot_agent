import { createServer } from "node:http";
import { randomUUID } from "node:crypto";
import { readFileSync } from "node:fs";
const kbBundle = JSON.parse(readFileSync(new URL("../../knowledge_base/v3/knowledge_base.json", import.meta.url), "utf8"));
const kbSources = JSON.parse(readFileSync(new URL("../../knowledge_base/v3/sources.json", import.meta.url), "utf8"));
const kbNotes = new Map();
let kbNoteId = 0;

// Test-only backend. Never imported by app code, never used with real data.
const institution = "11111111-1111-4111-8111-111111111111";
const staffId = "22222222-2222-4222-8222-222222222222";
const stamp = "2026-09-10T09:00:00Z";
const children = ["Test Amina", "Test Bilal", "Test Hania", "Test Ibrahim", "Test Mariam", "Test Zayan"].map((name, i) => ({ id: `33333333-3333-4333-8333-${String(i + 1).padStart(12, "0")}`, institution_id: institution, name, intake_date: "2026-09-09", dob_confirmed: i % 2 === 0, dob: i % 2 === 0 ? "2023-04-15" : null, estimated_age_range: i % 2 ? "30-36 months" : null, estimated_age_note: i % 2 ? "Synthetic intake estimate" : null, is_synthetic: true, created_at: stamp, archived_at: null, archived_reason: null }));
const sessions = new Map();
const observations = new Map();
const referrals = new Map();
const page = items => ({ items, total: items.length, page: 1, page_size: 100 });
const providers = ["stt", "llm"].map(provider => ({ provider, configured: false, backend: "synthetic", detail: "UI test fixture", source: null }));
const usage = { calls: 0, estimated_cost: null, unpriced_calls: 0 };
const server = createServer(async (req, res) => {
  const url = new URL(req.url, "http://127.0.0.1:18119");
  let raw = ""; for await (const chunk of req) raw += chunk;
  const body = raw ? JSON.parse(raw) : {};
  const send = (data, status = 200) => { res.writeHead(status, { "Content-Type": "application/json" }); res.end(JSON.stringify({ success: status < 400, data, meta: { request_id: "ui-test", timestamp: stamp, version: "test" } })); };
  const path = url.pathname;
  const admin = req.headers.authorization === "Bearer fixture-admin";
  if (path === "/health") return send({ test: true });
  if (path === "/api/v1/auth/token") return send({ access_token: body.email?.startsWith("admin") ? "fixture-admin" : "fixture-caretaker" });
  if (!req.headers.authorization?.startsWith("Bearer fixture-")) return send({}, 401);
  if (path === "/api/v1/auth/me") return send({ staff_id: staffId, institution_id: institution, role: admin ? "admin" : "caretaker", email: admin ? "admin@fixture.test" : "caretaker@fixture.test", institution_name: "Synthetic Care Home", is_admin: admin });
  if ((path.includes("/admin/") || path.includes("/audit_log")) && !admin) return send({}, 403);
  if (path === "/api/v1/admin/knowledge-review") return send({ release_id: kbBundle.release_id, runtime_enabled: false, items: kbBundle.rows.map(entry => { const notes = kbNotes.get(entry.citation_ref) ?? []; return { citation_ref: entry.citation_ref, content_sha256: "a".repeat(64), workflow_status: notes[0]?.status ?? "pending", feedback_stale: false, latest_note_id: notes[0]?.id ?? 0, snapshot: { entry, sources: kbSources.filter(source => entry.source_ids.includes(source.source_id)) } }; }) });
  if (/\/admin\/knowledge-review\/[^/]+\/notes$/.test(path)) {
    const ref = path.split("/")[5];
    if (!kbBundle.rows.some(entry => entry.citation_ref === ref)) return send({}, 404);
    const notes = kbNotes.get(ref) ?? [];
    if (req.method === "POST") { if ((notes[0]?.id ?? 0) !== body.expected_note_id) return send({}, 409); const note = { ...body, id: ++kbNoteId, citation_ref: ref, created_at: stamp, recorded_by: staffId }; notes.unshift(note); kbNotes.set(ref, notes); return send(note, 201); }
    return send(notes);
  }
  if (path === "/api/v1/admin/providers") return send({ providers });
  if (path === "/api/v1/admin/credentials") return send({ providers: providers.map(p => ({ provider: p.provider, is_active: false, masked_suffix: null, updated_at: null, model_name: null })) });
  if (path === "/api/v1/admin/usage") return send({ total: usage, by_provider: { stt: usage, llm: usage }, by_staff: [], by_institution: [] });
  if (path === "/api/v1/admin/staff") return send(page([{ id: staffId, institution_id: institution, email: "admin@fixture.test", role: "admin", is_active: true, created_at: stamp }, { id: "other", institution_id: institution, email: "caretaker@fixture.test", role: "caretaker", is_active: true, created_at: stamp }]));
  if (path === "/api/v1/admin/children") return send(page(children.map(c => ({ ...c, institution_name: "Synthetic Care Home" }))));
  if (path === "/api/v1/admin/institutions") return send(page([{ id: institution, name: "Synthetic Care Home", is_synthetic: true, created_at: stamp }]));
  if (path === "/api/v1/audit_log/integrity") return send({ chain_intact: true, entries_checked: 0, first_broken_sequence: null });
  if (path === "/api/v1/audit_log") return send(page([]));
  if (path === "/api/v1/children" && req.method === "POST") { const child = { ...children[0], ...body, id: randomUUID() }; children.push(child); return send(child); }
  if (path === "/api/v1/children") return send(page(url.searchParams.get("status") === "archived" ? [] : children));
  const allFlags = [...sessions.values()].flatMap(session => session.fixtureFlags ?? []);
  if (/\/flags\/[^/]+\/referral$/.test(path) && req.method === "POST") {
    const flagId = path.split("/")[4];
    if (!allFlags.some(flag => flag.id === flagId)) return send({}, 403);
    if (!body.caretaker_confirmed || [...referrals.values()].some(item => item.flag_id === flagId && item.status !== "closed")) return send({}, 409);
    const record = { id: randomUUID(), flag_id: flagId, ...body, status: "referred", created_at: stamp, escalated: body.review_date < new Date().toISOString().slice(0, 10) };
    referrals.set(record.id, record); return send(record, 201);
  }
  if (/\/flags\/[^/]+$/.test(path)) { const flag = allFlags.find(item => item.id === path.split("/").at(-1)); return send(flag ?? {}, flag ? 200 : 403); }
  if (path === "/api/v1/referrals") {
    let items = [...referrals.values()];
    if (url.searchParams.has("flag_id")) items = items.filter(item => item.flag_id === url.searchParams.get("flag_id"));
    if (url.searchParams.has("status")) items = items.filter(item => item.status === url.searchParams.get("status"));
    if (url.searchParams.get("overdue") === "true") items = items.filter(item => item.escalated && item.status !== "closed");
    const number = Number(url.searchParams.get("page") ?? 1), size = Number(url.searchParams.get("page_size") ?? 20);
    return send({ items: items.slice((number - 1) * size, number * size), total: items.length, page: number, page_size: size });
  }
  if (/\/referrals\/[^/]+$/.test(path)) {
    const record = referrals.get(path.split("/").at(-1)); if (!record) return send({}, 403);
    if (req.method === "PATCH") Object.assign(record, body, { escalated: body.status !== "closed" && body.review_date < new Date().toISOString().slice(0, 10) });
    return send(record);
  }
  if (/\/children\/[^/]+\/flags$/.test(path)) return send(page([]));
  if (/\/children\/[^/]+$/.test(path)) return send(children.find(c => c.id === path.split("/").at(-1)) ?? {}, children.some(c => c.id === path.split("/").at(-1)) ? 200 : 403);
  if (path === "/api/v1/sessions" && req.method === "POST") { const session = { id: randomUUID(), institution_id: institution, staff_id: staffId, ...body, status: "in_progress", started_at: stamp, resumed_at: null, created_at: stamp }; sessions.set(session.id, session); observations.set(session.id, []); return send(session); }
  const parts = path.split("/");
  if (parts[3] === "sessions") {
    const session = sessions.get(parts[4]); if (!session) return send({}, 403);
    if (parts[5] === "flags") return send(page(session.fixtureFlags ?? []));
    if (parts[5] === "result") return send(session.fixtureResult ?? null);
    if (parts[5] === "reason" && req.method === "POST") {
      const turns = observations.get(session.id);
      turns.push({ id: randomUUID(), institution_id: institution, session_id: session.id, turn_number: turns.length + 1, raw_input: body.raw_input, extracted_signals: null, created_at: stamp });
      const flag = { id: randomUUID(), session_id: session.id, child_id: session.child_id, domain: "Hearing", confidence_grade: "MODERATE", status: "open", explanation_text: "Synthetic saved explanation for recovery testing.", created_at: stamp, reasoning_trail: [{ citation_ref: "TEST-REF-001", basis: "Original synthetic evidence wording.", description: "Original synthetic evidence wording.", source: "Synthetic test source", kb_drifted: true }] };
      session.fixtureFlags = [flag];
      session.fixtureResult = { status: "flagged", turn: turns.length, max_turns: 5, grade: "MODERATE", domain: "Hearing", explanation_text: flag.explanation_text, citations: ["TEST-REF-001"], age_uncertain: false, loop_exhausted: false, follow_up_question: null, flag_id: flag.id };
      return send(session.fixtureResult);
    }
    if (parts[5] === "complete") { session.status = "completed"; return send(session); }
    if (parts[5] === "observations") { const turns = observations.get(session.id); if (req.method === "POST") { const turn = { id: randomUUID(), institution_id: institution, session_id: session.id, turn_number: turns.length + 1, raw_input: body.raw_input, extracted_signals: null, created_at: stamp }; turns.push(turn); return send(turn); } return send(page(turns)); }
    return send(session);
  }
  return send({}, 404);
});
server.listen(18119, "127.0.0.1", () => console.log("Isolated UI fixture ready on 18119"));
