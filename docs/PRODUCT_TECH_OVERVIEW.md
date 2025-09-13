## Polyglot Vocabulary Trainer – Product & Technical Overview

### Executive summary
Polyglot Vocabulary Trainer is a Next.js app backed by Supabase that helps learners discover, review, and master vocabulary across language decks using a spaced-repetition system (SRS). It integrates a word-similarity module to surface orthographically similar words as an aid against confusion, and provides a dashboard with recent activity and progress metrics. The product runs on the web (desktop/tablet/phone) with a mobile-optimized study experience.

---

## Architecture at a glance
- **Frontend**: Next.js App Router (React, TypeScript, Tailwind)
  - App pages: `src/app/dashboard`, `src/app/study`, `src/app/auth/callback`
  - Components: `src/components/SimilarWordsPanel`, shared UI components
  - Services: `src/lib/services/word-similarity-service.ts`, `src/lib/daily-summary.ts`, `src/lib/utils.ts`
- **Backend (Supabase)**: Postgres + Supabase Auth + RLS
  - Tables (key): `vocabulary`, `vocabulary_decks`, `deck_vocabulary`, `user_progress`, `rating_history`, `study_sessions`, `daily_summary`, `word_similarities`
  - Policies: RLS enabled; selective open policies for read access, and permissive policies where migration is needed
- **Infra/Deploy**: Vercel (Next.js), Supabase project (managed Postgres)
- **Data tooling**: Migration/verification Python scripts for the word similarity module under `word-relationship-analyzer/`

---

## Data model (key entities)

### Decks & Vocabulary
- `vocabulary_decks`
  - id (uuid), name, language_a/b metadata (names, codes), difficulty_level, is_active
- `vocabulary`
  - id (int), language_a_word, language_b_translation, language_a_sentence, language_b_sentence, timestamps
- `deck_vocabulary`
  - deck_id (uuid) → `vocabulary_decks.id`
  - vocabulary_id (int) → `vocabulary.id`
  - word_order (int)

### User study state & activity
- `user_progress`
  - user_id (uuid), word_id (int), deck_id (uuid)
  - repetitions (int), interval (days), ease_factor (float), next_review_date (timestamptz)
  - again_count (int) – used to identify “leeches”
- `rating_history`
  - user_id, word_id, deck_id, rating (again|hard|good|easy|learn|know), created_at
- `study_sessions`
  - user_id, deck_id, session_type (review|discovery|deep-dive), words_studied, correct_answers, session_duration, completed_at
- `daily_summary`
  - user_id, date, reviews_done, new_words_learned (aggregates for dashboard)

### Similarity graph
- `word_similarities` (directed edges; true directed storage)
  - id (serial), source_word_id (int) → `vocabulary.id`, target_word_id (int) → `vocabulary.id`, created_at
  - Constraints: `no_self_similarity`, `unique_similarity (source_word_id, target_word_id)`

---

## Security & RLS
- RLS enabled on all user-specific tables. Typical patterns:
  - `SELECT` restricted or opened per product need (e.g., `word_similarities` may be public-read for UI).
  - `INSERT/UPDATE/DELETE` allowed for authenticated users for their own rows (`user_id = auth.uid()`), or opened temporarily for migrations.
- Migration helper SQL lives under `word-relationship-analyzer/*.sql` (e.g., `create_word_similarities_table.sql`, `fix_word_similarities_rls.sql`).

---

## SRS model and queues

### SRS update
- Helper: `calculateNextReview` in `src/lib/utils.ts` returns `{ interval, easeFactor, repetitions }` based on rating.
- “Leech” detection: `again_count >= 4` marks hard items; we apply spacing to avoid rapid repeats.

### Word due logic
- `isDueForReview(date)` – due now if `date <= today`.
- `isNearFuture(date)` – due soon if within a near-future window.

### Session types and queue building
- Implemented consistently between dashboard and study page.
- `review` session
  - Build two lists from `user_progress` in the active deck: Due Now and Due Soon.
  - If Due Now empty, load Due Soon for early review.
  - Apply “leech spacing” (mixes regular items and leeches to improve pacing).
- `discovery` session
  - Excludes learned words for that deck (based on presence in `user_progress`).
- `deep-dive` session
  - Filters within deck by user state (leeches, learning, strengthening, consolidating) using thresholds on `again_count`, `interval`, etc.

### “Again” button behavior (review)
- Clicking “Again” re-enqueues the current word immediately into the live session list and increments `again_count`.
- Session does not end when the last word is rated “again”; it continues until a final “hard/good/easy” on the last remaining item.

### Due Soon integrity
- When reviewing a Due Soon word early, next due date is computed from the original due date (not “today”) to preserve spacing. Due Now uses “today”.

---

## Frontend flows

### Authentication
- Supabase Auth with Google OAuth.
- Callback route: `src/app/auth/callback/route.ts` exchanges the code for session and redirects back to `origin + next`.
- For local LAN testing, Supabase “Site URL” and “Additional Redirect URLs” must include your LAN host (e.g., `http://192.168.1.13:3000/auth/callback`).

### Dashboard (`src/app/dashboard/page.tsx`)
- Header shows product name, user email, and Sign Out.
- Recent Activity: reads from `daily_summary` via `DailySummaryManager` (`src/lib/daily-summary.ts`).
- Current Deck tile: name, difficulty, language direction.
- Deck Progress: displays category counts across SRS phases (unseen, learning, strengthening, consolidating, mastered) and progress bar.
- Session launchers: Discovery, Review (prefers Due Now → Due Soon), Deep Dive (category picker).

### Study session (`src/app/study/page.tsx`)
- Shared features
  - Deck selection pulled from `localStorage` (`selectedDeck`).
  - Session type loaded from `localStorage` (`sessionType`).
  - TTS via `ttsService` for language A/B word and example sentences.
  - Daily summary logging at session end (words studied & correct answers) → `study_sessions` + `daily_summary`.

- Discovery
  - Large language A word, translation, and example box.
  - Actions: “Learn This” / “I Know This”. Ratings log to `rating_history` with types `learn` and `know`.

- Review
  - Question side: prompt + input (recognition/production) then “Reveal Answer”. Case-insensitive answer check.
  - Answer side: shows correctness feedback, the word & translation, example box, rating grid (Again/Hard/Good/Easy), and a leech toggle button.
  - “Add to Leeches”/“Remove from Leeches” operates by adjusting `again_count` in `user_progress`.

### Word similarity UX
- Component: `src/components/SimilarWordsPanel.tsx`.
- Service: `src/lib/services/word-similarity-service.ts`.
- Retrieval strategy: global-first lookup; if no in-deck matches, display “all-decks” result.
- Limit: default max 5 similar words (configurable via `setMaxSimilarWords`).
- Fields: word, translation, example sentences where available.
- In review, panel shows only after answer reveal; in discovery, it shows immediately. Rendered under the flash card.

---

## Mobile responsive guidelines

### Global
- Safe areas: `pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)]` around the page when appropriate.
- Typography scales down on phones (`text-xl` or `text-2xl`) while desktop keeps (`text-6xl` for large headlines).
- Button grids switch from 4 columns → 2 columns on phones; full-width buttons where appropriate.

### Study page (key details)
- Review & Discovery example sentence boxes (phones)
  - Same structure and width across both modes.
  - Width: `calc(100% + 4rem)` with `-mx-8` (flush to the flash card’s inner 2rem padding on each side).
  - Centering: resets to `sm:mx-auto` for tablet/desktop.
  - Inner spacing: stacked with `space-y-3` (mobile) and larger on tablet/desktop.
  - Label “Example:” removed globally to save vertical space.
- Stack spacing for word → translation → example reduced for phones (tighter but readable) while preserving desktop spacing.

### Dashboard
- Header wraps on phones; long titles break cleanly with tighter line height.
- “Current Deck” stacks on phones with wrapped deck name and full-width action button.

---

## Daily summary & streaks
- `DailySummaryManager` aggregates per day:
  - Discovery: increments `new_words_learned` on `learn/know`.
  - Review: increments `reviews_done` on each rating.
- Streak calculation uses immutable `Date` handling to avoid ESLint `prefer-const` issues and off-by-ones.

---

## Word similarity system (end to end)

### Analyzer & data prep
- Project folder: `word-relationship-analyzer/`
- Inputs: 16 French decks; generation enforces rules like “same first character” and at most 5 similar words per target.
- Batch processing scripts support progress, partial saves, consolidation (`consolidate_*` scripts) into two-column CSV.

### Migration into Supabase
- Table: `word_similarities` (directed edges A→B and B→A where desired).
- Scripts: `migrate_*` variants, including pagination fixes (avoid 1000-row limits) and canonicalization where needed.
- Policies: temporary permissive insert policies for migration; revert/tighten as needed.

### Frontend service
- `WordSimilarityService.getSimilarWords(wordId, limit)`
  - Reads candidate IDs globally (up to 200), fetches vocabulary rows with sentences/translation, then trims to `MAX_SIMILAR_WORDS`.
  - Fall back to global when in-deck matches are insufficient.

---

## Deployment & environments

### Environment variables (`.env.local`)
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Optional local helper: `NEXT_PUBLIC_AUTH_REDIRECT_BASE` to force a LAN callback base during phone testing.

### Supabase Auth redirect settings
- Set **Site URL** to your environment base (production or temporary LAN host during local phone testing).
- Add **Additional Redirect URLs** for all origins you use, e.g.:
  - `http://localhost:3000/auth/callback`
  - `http://127.0.0.1:3000/auth/callback`
  - `http://<LAN_IP>:3000/auth/callback` (and other ports if your dev server uses 3002, 3003…)

### Local LAN testing on iPhone
- Start dev on 3000; if Next.js chooses 3002, either free 3000 or whitelist 3002 in Supabase redirects.
- Use the LAN URL printed by Next.js (e.g., `http://192.168.1.13:3000`).
- Use a Private/Incognito tab when switching between prod/local to avoid stale sessions.

### Allowed dev origins (Next.js warning)
- To silence the “Cross origin request detected” warning, add in `next.config.js`:
```js
experimental: { allowedDevOrigins: ['http://<LAN_IP>:3000'] }
```

---

## Operations & runbooks

### Creating/repairing tables
- `word-relationship-analyzer/create_word_similarities_table.sql` – create similarity table (directed edges only).
- `word-relationship-analyzer/fix_word_similarities_rls.sql` – add temporary permissive RLS policies for data migration.
- `create_daily_summary_table.sql` – creates daily summary table + policies.

### Verifying RLS and structure
- `word-relationship-analyzer/verify_word_similarities_table.py` – sanity checks schema, indexes, and policies.

### Populating similarity edges
- `word-relationship-analyzer/populate_french16_pairs.py` – directed inserts for the 16 French decks.
- `word-relationship-analyzer/migrate_simple_word_mapping_fixed.py` – simplified CSV → table import.

### Git secrets & history
- A stray API key was removed via history rewrite (`git filter-branch`) and a force push. Ensure future secrets only reside in `.env*`.

---

## UX specifics (reference)

### Review – ratings & sequencing
- Ratings log to `rating_history` and update `user_progress` (interval, ease factor, repetitions, next_review_date).
- `Again` re-queues immediately in-session; others move to next item.

### Similar words
- Title: “Words Similar in Spelling”.
- Default global-first lookup; if no in-deck items are found, indicates “(all decks)”.
- Card content: French word → English translation → example sentence + translation.

### Mobile polish
- Buttons: min height 44px; grid switches to 2 columns on phones.
- Example box: full-bleed to inner flash-card padding on phones; clamped lines for long sentences; label removed.

---

## User experience (detailed)

### Personas and goals
- **Learner**: efficient discovery and high-retention review with minimal friction; wants pronunciation and short contextual examples.
- **Returning learner**: clear counts of Due Now/Soon and a session queue that matches the dashboard.

### Global navigation & state
- Start at Dashboard after login. Deck selection persists via `localStorage.selectedDeck`; study mode via `localStorage.sessionType`.
- Learning type preferences (recognition/production/listening) persist and apply to sessions.

### Dashboard experience
1) Header: product name, signed-in email, Sign Out.
2) Recent Activity: Today, 7 Days, 30 Days, Streak from `daily_summary`.
3) Current Deck: name, difficulty, language direction; Change Deck opens the selection grid.
4) Deck Progress: category counts and an overall progress bar.
5) Session launchers: Discovery, Review (Due Now → Due Soon), Deep Dive (pick a category), requiring at least one learning type.

### Discovery session flow
1) Counters (Remaining Unseen / Reviewed)
2) Large French word with TTS
3) English translation with TTS
4) Example box (full-bleed on phones): French sentence + TTS; English sentence + TTS
5) Actions: Learn This / I Know This; Similar Words panel always visible under the card
- Results: `rating_history` logs, `user_progress` upserts, `daily_summary` increments `new_words_learned`.

### Review session flow
1) Question side: prompt → input (Enter = Reveal), TTS for the prompt term
2) Answer side: correctness banner, word + translation (TTS), example box (same layout and width as discovery), ratings (Again/Hard/Good/Easy), leech toggle
3) Similar Words panel appears after reveal, under the card
- Results: `rating_history` + `user_progress` updated; `Again` re-queues current item; Due Soon spacing preserved from original due date; session ends with non-Again on last item; summary recorded.

### Deep Dive
- Choose category (e.g., Leeches) on the Dashboard, then study that filtered list with review-like interactions.

### Mobile-first specifics
- Safe areas for notch; minimum 44px tap targets; rating grid collapses to two columns on phones.
- Example boxes use `calc(100% + 4rem)` width with negative margins inside the flash card on phones; auto-center on tablet/desktop.
- Tightened spacing between word → translation → example on phones; desktop/tablet keep larger spacing.

### Error/edge cases
- Empty session states show a friendly message and a Back-to-Dashboard button.
- Similar Words panel may show “No similar words found.”
- Auth/callback issues redirect to `/`.

### Completion & logging
- On session end/back: write `study_sessions` and aggregate `daily_summary` (reviewsDone/newWordsLearned). Dashboard refreshes on focus.

---
## Future improvements
- Server-side aggregation for daily stats (materialized views) to reduce client work.
- A/B testing of SRS parameters; adaptive ease-factor tuning.
- Caching for similarity lookups; precomputed subsets per deck/language.
- Accessibility pass (aria-labels for TTS buttons; focus management on Reveal → Rate).
- E2E tests for session sequencing and answer validation.

---

## File index (high-value)
- `src/app/study/page.tsx` – study flows, SRS updates, example box, SimilarWordsPanel integration
- `src/app/dashboard/page.tsx` – deck selection, metrics, session launchers, recent activity
- `src/app/auth/callback/route.ts` – OAuth code exchange & redirect
- `src/components/SimilarWordsPanel.tsx` – similar words UI
- `src/lib/services/word-similarity-service.ts` – similarity fetch logic & limits
- `src/lib/daily-summary.ts` – summary aggregation & streaks
- `src/lib/utils.ts` – SRS helpers & due checks
- `docs/PRODUCT_TECH_OVERVIEW.md` – this document


