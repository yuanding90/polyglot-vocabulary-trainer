## Backend-Authoritative SRS with FSRS — Architecture, Migration, and Rollout

### Objective
- Move all Spaced Repetition System (SRS) computations and time checks from the client to the server to ensure consistency, integrity, and easier evolution of the algorithm.
- Adopt FSRS (Free Spaced Repetition Scheduler) as the primary scheduler for improved retention with fewer reviews; keep SM‑2 compatibility for rollback.

### Outcomes / Benefits
- Server authority: Eliminates client clock tampering and version drift. All next-review dates are anchored to server `now()`.
- Easier iteration: Update the SRS algorithm (parameters, bugfixes) without requiring users to refresh or update clients.
- Better data: Full review audit trail enables analytics, A/B tests, and model personalization later.
- Reliability: Row-level locking avoids race conditions with multiple tabs/devices.

### Risks / Mitigations
- Additional moving parts: Edge Function + web API. Mitigate with tests, retries, and idempotency keys.
- Latency vs UX: A server call per rating can add latency. Mitigate via optimistic UI and background persistence where acceptable; server remains source of truth.
- Schema changes (Supabase): Additive and backward‑compatible; plan and test migrations. Keep SM‑2 columns alongside FSRS fields.
- FSRS complexity: New parameters/fields. Start with default FSRS parameters; personalize later.

### Is this a one‑way door?
- No. The migration is additive and reversible.
  - We keep SM‑2 fields (`interval`, `ease_factor`) and add FSRS fields (`stability`, `difficulty`).
  - Each `user_progress` row has `srs_algorithm` and `scheduler_version` for safe rollbacks.
  - We can flip feature flags to switch cohorts back to SM‑2 while retaining data integrity.
  - The new `review_logs` table is additive; removing it later is non‑destructive (but not recommended).

---

### Architecture Overview (Recommended)
1) Client initiates a review and displays cards; when a user rates a card (again/hard/good/easy), the client calls a server function.
2) Supabase Edge Function `apply-srs` performs all SRS logic inside a DB transaction using server time.
3) The function:
   - SELECTs the `user_progress` row with `FOR UPDATE` (row lock), anchors time via `now()`.
   - Computes next state with FSRS (or SM‑2 fallback based on `srs_algorithm`).
   - UPSERTs `user_progress` with new values and inserts a `review_logs` row (audit).
   - Returns the new state to the client.
4) A server endpoint (or RPC) can provide the authoritative “due” set to start a session, preventing early reviews.

Why Supabase Edge Functions?
- TypeScript implementation is faster to develop/test than PL/pgSQL for FSRS math.
- Runs close to the database, low latency, easy auth with Supabase JWT.

---

### Data Model Changes (Additive)

Existing: `user_progress` (retained)
- `user_id uuid`, `word_id int`, `deck_id text`, `interval int`, `ease_factor float`, `next_review_date timestamptz`, `repetitions int`, `again_count int` …

Add to `user_progress` (new columns)
- `srs_algorithm text not null default 'sm2'` — current algorithm per row.
- `scheduler_version int not null default 1` — algorithm version for safe migrations.
- `last_reviewed_at timestamptz` — last server‑anchored review time.
- FSRS fields (per card):
  - `stability double precision` — long‑term memory strength estimate.
  - `difficulty double precision` — ease/difficulty estimate for the item.
  - `retrievability double precision` — optional; can be derived; stored if useful.
  - `elapsed_days int` — optional; days since last review (for diagnostics).

New: `review_logs` (audit)
- `id bigserial primary key`
- `user_id uuid not null`
- `deck_id text not null`
- `word_id int not null`
- `rating text not null` — one of `again|hard|good|easy`
- `reviewed_at timestamptz not null default now()`
- `prev_state jsonb not null` — snapshot of progress fields before update
- `next_state jsonb not null` — snapshot after update
- `scheduler_version int not null`
- Optional: `client_event_id text unique` — for idempotency in case of client retries

Indexes & RLS (sketch)
```
create index if not exists idx_review_logs_user on review_logs(user_id, reviewed_at desc);
-- RLS policies so users can only see their own logs
```

RLS for `user_progress`
- Allow users to `select` and `update` only rows matching `auth.uid()`.
- Edge Function can run with the user’s JWT (not service role) to respect RLS.

---

### API / Function Contracts

Edge Function: `apply-srs`
- Auth: Supabase user JWT (required)
- Input JSON:
```
{
  "deckId": "string",
  "wordId": 123,
  "rating": "again" | "hard" | "good" | "easy",
  "clientEventId": "optional-idempotency-key"
}
```
- Behavior:
  1) Validate ownership (deck/word belongs to user’s deck), begin transaction.
  2) `SELECT ... FOR UPDATE` from `user_progress`.
  3) Anchor time via `now()` from DB; compute elapsed days; run scheduler (FSRS or SM‑2 by `srs_algorithm`).
  4) UPSERT `user_progress` with new `next_review_date` and fields.
  5) INSERT `review_logs` with `prev_state`/`next_state` and `scheduler_version`.
  6) Commit; return new progress state to client.

Due Set Endpoint (optional but recommended)
- Returns authoritative lists: due now, near future, unseen.
- Ensures sessions use only eligible items.

---

### Scheduler Details

FSRS (recommended)
- Better alignment to human forgetting curve than SM‑2.
- Use community default params initially (deterministic), later personalize per user (batch fitting over `review_logs`).
- Store per‑card `stability` and `difficulty`. Compute `retrievability` on the fly or store for diagnostics.

SM‑2 (fallback)
- Keep current fields (`interval`, `ease_factor`, `repetitions`).
- Continue to be supported under `srs_algorithm = 'sm2'` for rollback.

Versioning
- `scheduler_version` increments on algorithm parameter changes or formula updates.
- Web UI can show version for debugging; migration scripts can transform states if needed.

---

### Migration Plan

1) Schema (additive)
- Add columns to `user_progress`; create `review_logs`.
- Write RLS policies for secure user‑level updates.

2) Edge Function MVP
- Implement `apply-srs` with SM‑2 first (parity) using server `now()` and row locks.
- Add idempotency via `clientEventId` (unique per user+word+time window).

3) Client Integration
- Replace local `calculateNextReview` calls with a POST to `apply-srs`.
- Optimistic UI: show rating feedback instantly; on failure, revert.

4) FSRS Enablement
- Switch `srs_algorithm` default to `fsrs` for a small cohort (feature flag/query param).
- Monitor daily; compare review loads and retention.

5) Full Rollout
- Promote FSRS to everyone; keep ability to set `srs_algorithm = 'sm2'` for targeted rollback.

6) Personalization (optional, later)
- Fit FSRS parameters per user weekly/monthly using `review_logs`.
- Gate behind a feature flag; compare metrics.

Rollback Strategy
- Set `srs_algorithm = 'sm2'` globally or per cohort; `apply-srs` automatically uses SM‑2 branch.
- Because schema changes are additive, no destructive down‑migration is needed.

---

### Testing Strategy
- Unit tests for FSRS/SM‑2 pure functions (deterministic given inputs).
- Integration tests for `apply-srs` (transactional behavior, idempotency, RLS).
- Time anchoring tests: ensure `now()` usage and timezone correctness.
- Race tests: simulate concurrent ratings; verify row locks prevent double‑writes.

Manual QA Scenarios
- New user, first review; edge cases around day boundaries; changing ratings; long gaps.
- Cohort A (SM‑2) vs Cohort B (FSRS) for a week.

Observability
- Log events (success/error) with timings; dashboard panels for error rate and latency.

---

### Performance & Offline
- Latency target: < 150ms for function call (Edge + single transaction).
- Offline path (optional): queue ratings locally, replay on reconnect; server still anchors times to its `now()`.

---

### Example SQL (sketch)
```
alter table user_progress add column if not exists srs_algorithm text not null default 'sm2';
alter table user_progress add column if not exists scheduler_version int not null default 1;
alter table user_progress add column if not exists last_reviewed_at timestamptz;
alter table user_progress add column if not exists stability double precision;
alter table user_progress add column if not exists difficulty double precision;
alter table user_progress add column if not exists retrievability double precision;
alter table user_progress add column if not exists elapsed_days int;

create table if not exists review_logs (
  id bigserial primary key,
  user_id uuid not null,
  deck_id text not null,
  word_id int not null,
  rating text not null,
  reviewed_at timestamptz not null default now(),
  prev_state jsonb not null,
  next_state jsonb not null,
  scheduler_version int not null
);

create index if not exists idx_review_logs_user_time on review_logs(user_id, reviewed_at desc);
```

---

### Example Client Call (contract)
```ts
// POST /functions/apply-srs
const res = await fetch('/functions/v1/apply-srs', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  body: JSON.stringify({ deckId, wordId, rating, clientEventId }),
})
const json = await res.json() // { nextReviewDate, againCount, ... }
```

---

### Summary
- Move SRS computations server‑side via a Supabase Edge Function using DB `now()` and row locks.
- Adopt FSRS with default parameters, maintain SM‑2 compatibility for rollback.
- Add minimal, additive schema (columns + `review_logs`) to enable analytics and future personalization.
- Implement in phases with feature flags and a clear rollback path.


