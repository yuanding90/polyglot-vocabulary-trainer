## Progress & Activity Improvements

### Problems Observed
- Today count lags or is incorrect after session end.
- UTC/local-day mismatches cause off-by-one errors in daily buckets.
- Client-only aggregation (write at session end) is fragile; undercounts if client disconnects.

### Goals
- Accurate Today/7/30 totals across all decks.
- Streaks based on consecutive local days with any activity.
- Fast dashboard load (minimal recompute), correct in all timezones.

### Immediate Fixes (Session-End Reliability)
1) Recompute final counts at session end from session state (not transient counters):
   - reviews_done = again + hard + good + easy
   - new_words_learned = actual learned/known count captured during session
2) Upsert `daily_summary` using local date (YYYY-MM-DD local), not UTC split.
3) On redirect to dashboard, prewarm `/api/activity/summary` (no-store) and hand off via `sessionStorage` so Today updates immediately.

### Server-Side Improvements (Recommended)
1) Postgres Triggers
   - On `rating_history` INSERT: upsert `daily_summary.reviews_done` for (user_id, date_in_user_tz).
   - On discovery event INSERT: upsert `daily_summary.new_words_learned` similarly.
   - Create function `daily_summary_upsert(user_id UUID, activity_date DATE, reviews_delta INT, discovery_delta INT)`.
2) Timezone Handling
   - Add `user_settings(timezone TEXT)` with default app TZ.
   - Trigger computes `activity_date` as `timezone(user_tz, now())::date` or from event timestamp.
3) Materialized Views (fast reads)
   - `daily_totals_mv(user_id, date, total_actions)` for Today/7/30 sums.
   - `streaks_mv(user_id, current_streak)` using window functions; `REFRESH CONCURRENTLY` nightly and on-demand per user.
4) APIs
   - `/api/activity/summary?days=...&tz=...` → reads from MVs; falls back to live SQL if missing. Returns Today/7/30 + streak + series.
   - `/api/activity/calendar?from=...&to=...&tz=...` → dense series aligned to tz.
5) Backfill
   - Aggregate from `rating_history` (+ discovery events) into `daily_summary` for last N days; refresh MVs.

### Frontend Changes
1) Dashboard
   - Fetch summary on mount; use prewarm cache when coming from session end.
   - Heatmap uses local or user-selected tz consistently.
2) Optional Live Updates
   - Debounced in-session increments (Again/Hard/Good/Easy) as a UX nicety; keep server triggers as source of truth.

### TODO Checklist
- [ ] Add `user_settings(timezone)` and default values.
- [ ] SQL function `daily_summary_upsert` and triggers on `rating_history` and discovery events.
- [ ] Backfill script to populate `daily_summary` historically; verify counts.
- [ ] Create MVs `daily_totals_mv`, `streaks_mv`; schedule refresh.
- [ ] Update `/api/activity/summary` and `/api/activity/calendar` to accept `tz` and read from MVs.
- [ ] Wire dashboard to pass user tz and to use prewarm handoff.
- [ ] QA: timezone edge cases (near midnight), long sessions, offline/refresh mid-session.

### Rollout Plan
1) Ship immediate fixes behind a feature flag.
2) Deploy triggers/MVs to staging; run backfill; validate vs manual queries.
3) Enable in production; monitor; remove client writes after a steady period.


