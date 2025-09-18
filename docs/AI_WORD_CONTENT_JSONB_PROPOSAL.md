## AI Word Content (JSONB) – Proposal (Solution 1)

### Goals
- Store AI‑generated learning aids per vocabulary word, keyed to `vocabulary.id`.
- Share results globally once generated; first request may wait for generation.
- Keep schema flexible to add/remove fields and new content types without heavy migrations.
- Ensure idempotency, versioning, moderation, and safe public read access under RLS.

### Non‑Goals
- No user‑specific personalization in v1 (e.g., user-tailored mnemonics).
- No per-user write access from the client to provider APIs (server/Edge only).

### Scope (v1)
- Support your current prompt output: `{ analysis, mnemonics[3], image_brief }`.
- Support optional inputs: `{ L2_IPA, include_analysis }`.
- Expose simple API to generate and to fetch latest content by `(vocabulary_id, l1_language, module_type)`.

### High-Level Design
- Single table storing JSONB payloads plus robust metadata. JSONB enables rapid evolution.
- One row per content module per word per L1. Example `module_type` values: `deep_dive_pack` (analysis+mnemonics+image_brief), `famous_story`, `frequency_stats`, etc.
- Reads are public/authenticated; writes happen via a controlled server/Edge function.

### Table Schema (Postgres / Supabase)
```sql
CREATE TABLE word_ai_content (
  id BIGSERIAL PRIMARY KEY,
  vocabulary_id INTEGER NOT NULL REFERENCES vocabulary(id) ON DELETE CASCADE,
  l1_language TEXT NOT NULL,                 -- e.g., 'en', 'zh'
  module_type TEXT NOT NULL,                 -- 'deep_dive_pack' | 'famous_story' | 'frequency_stats' | ...
  status TEXT NOT NULL DEFAULT 'ready',      -- 'pending' | 'ready' | 'failed'
  payload JSONB NOT NULL,                    -- exact AI JSON for this module
  prompt_version TEXT NOT NULL,              -- bump when prompt changes materially
  schema_version TEXT NOT NULL DEFAULT 'v1', -- bump if output schema changes
  provider TEXT NOT NULL,                    -- 'anthropic' | 'openai' | ...
  model TEXT NOT NULL,                       -- 'claude-3-5-sonnet-20240620', etc.
  include_analysis BOOLEAN NOT NULL DEFAULT TRUE,
  prompt_hash TEXT NOT NULL,                 -- idempotency key of normalized inputs
  is_latest BOOLEAN NOT NULL DEFAULT TRUE,   -- latest for (vocabulary_id,l1,module)
  moderation_status TEXT NOT NULL DEFAULT 'approved', -- 'approved'|'flagged'|'hidden'
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  -- Idempotency & de-dup
  CONSTRAINT uq_idem UNIQUE (vocabulary_id, l1_language, module_type, prompt_hash),
  -- At most one latest per key
  CONSTRAINT uq_latest UNIQUE (vocabulary_id, l1_language, module_type, is_latest) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX idx_ai_content_vocab ON word_ai_content(vocabulary_id);
CREATE INDEX idx_ai_content_vocab_type ON word_ai_content(vocabulary_id, module_type) WHERE is_latest;
CREATE INDEX idx_ai_content_status ON word_ai_content(status);
CREATE INDEX idx_ai_content_payload_gin ON word_ai_content USING GIN (payload jsonb_path_ops);
```

### Row Level Security (RLS)
- Enable RLS.
- SELECT: allow all authenticated users (or public if desired) to read.
- INSERT/UPDATE/DELETE: only via server role or SECURITY DEFINER RPC/Edge Function.

```sql
ALTER TABLE word_ai_content ENABLE ROW LEVEL SECURITY;

-- Read: allow all authenticated users (or replace with USING (true) for public)
CREATE POLICY ai_content_read ON word_ai_content
  FOR SELECT
  USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- Writes: restricted to service role (via Edge Function) 
CREATE POLICY ai_content_write ON word_ai_content
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);
```

### Idempotency & Versioning
- `prompt_hash = sha256(normalized({ vocabulary_id, l1_language, module_type, prompt_version, schema_version, include_analysis, l2_language, target_word, translation, l2_ipa }))`.
- If a row with same `(vocabulary_id, l1_language, module_type, prompt_hash)` exists in `pending|ready`, return it (no duplicate jobs).
- On successful generation, set prior rows for same `(vocabulary_id, l1_language, module_type)` to `is_latest=false` and new row to `is_latest=true`.

### Payload Schema (JSON)
- For `module_type = 'deep_dive_pack'`, store exactly the object produced by your prompt. Include deck‑sense context and an additional section for other meanings not covered by the current deck:
```json
{
  "analysis": { "usage_context": { "nuance_register_note": "", "collocations": [], "examples": [] }, "connections": { "nuanced_synonyms": [], "antonyms": [], "word_family": [], "mnemonic_aid": "" }, "clarification": { "confusables": [], "common_mistakes": [] } },
  "mnemonics": [ { "type": "phonetic_link", "content": "" }, { "type": "absurd_story", "content": "" }, { "type": "visualization_cue", "content": "" } ],
  "image_brief": { "title": "", "prompt": "", "style": "", "elements": [], "composition": "", "lighting": "", "color_palette": "", "aspect_ratio": "", "safety_notes": "" },
  "other_meanings": [
    {
      "meaning_l1": "",
      "examples": [ { "l2_sentence": "", "l1_translation": "" } ]
    }
  ],
  "deck_sense_context": {
    "l2_word": "",
    "l1_translation": "",
    "l2_example_sentence": "",
    "l1_example_translation": ""
  }
}
```
- Validate on ingest (e.g., Zod/JSON Schema) to enforce required keys, EXACTLY 3 mnemonics, and empty values `""` or `[]` for missing fields.

### API Surface (Edge Function or Next.js Route Handler)
- POST `/ai-content/generate`
  - Input: `{ vocabularyId, l1Language, moduleType = 'deep_dive_pack', includeAnalysis = true }`.
  - Behavior: compute `prompt_hash`, upsert `pending` row if none exists, enqueue job, return 202 with job reference.
- GET `/ai-content/fetch?vocabularyId=&l1Language=&moduleType=&latest=true`
  - Returns latest `ready` payload + metadata.
- POST `/ai-content/regenerate`
  - Force a new generation (bumps `prompt_version` in the request), leaves history intact.

Notes:
- Never expose provider API keys to the client. The generate/regenerate endpoints run server-side.
- Use Supabase Edge Functions or a serverless route with a service key to bypass write RLS.

### Generation Workflow
1) Client requests generate → server checks idempotency → creates `pending` row → queues job.
2) Worker calls provider (Anthropic) with prompt inputs built from DB (`vocabulary`, languages, etc.).
3) Validate JSON response; on success: upsert `ready` row (`is_latest=true`), flip previous to `false`.
4) On failure: mark row `failed`, include error metadata.
5) Client polls GET until `ready` or receives webhook/socket event.

### Prompt Inputs & Assembly
- Inputs: `{ L1_Language, L2_Language, Target_Word, Translation, L2_IPA?, include_analysis }`.
- Use your draft prompt verbatim for `deep_dive_pack`.
- Normalize inputs (trim, NFC, lowercase where appropriate) before hashing.

### UI/UX (v1)
- In study/discovery card, add “Generate AI Insights” button.
- If latest exists → render immediately.
- If not → show spinner and a non-blocking toast; poll every 2–3 seconds up to N seconds; then offer “Keep running in background.”
- Display: tabs or collapsible sections for Analysis / Mnemonics / Image Brief.
- Provide a “Regenerate” option (with note it may replace the latest version).

### Extensibility
- New modules: just set a new `module_type` and store any JSON; no migration.
- New fields inside existing modules (e.g., add IPA per synonym): start writing them in `payload`. Add GIN index or promote to hybrid later if you need targeted SQL queries.
- Large payloads later: move to Storage + keep pointer in this table (optional v2).

### Rate Limits & Caching
- Per‑user daily generation cap (e.g., 50) and global backoff if provider limits are hit.
- Idempotent reuse ensures repeated clicks don’t spawn duplicate jobs.

### Moderation & Safety
- `moderation_status`: `approved|flagged|hidden` with optional audit columns (`moderation_reason`, `moderated_by`).
- Hide non‑approved rows from general UI.

### Observability
- Log: `job_id`, `vocabulary_id`, timings, model, tokens (if available), cost estimates, success/failure.
- Add a simple admin view to list recent jobs and statuses.

### Migration Plan
1) Create table + indexes + RLS.
2) Deploy Edge Function(s): `generate`, `fetch`, `regenerate` with validation.
3) Add minimal UI button and polling hook; ship behind a feature flag.
4) Pilot on a few decks; monitor costs and latency.

### Open Questions
- Public vs authenticated read? (Default: authenticated.)
- Feature flag rollout per language/deck?
- Cost ceiling strategy (daily/monthly budget)?
- How long to cache failures before allowing retry?

### Acceptance Criteria (v1)
- Able to generate, store, and fetch `deep_dive_pack` for any word with L1=EN.
- Idempotent generate: repeated requests return same pending/ready job.
- Versioning: regenerate creates a new latest; history retained.
- RLS: only server can write; clients can read latest.
- Validation: malformed AI responses never persist; clear error surfaced.

### Cache-Aside Retrieval Workflow (adapted to JSONB Solution 1)
1) User requests enhanced info for `(vocabulary_id, l1_language)` with `module_type='deep_dive_pack'`.
2) Backend defines `CURRENT_PROMPT_VERSION` and computes `cache key = (vocabulary_id, l1_language, module_type, CURRENT_PROMPT_VERSION)`.
3) Cache lookup:
   - Query `word_ai_content` for `is_latest=true AND status='ready' AND module_type='deep_dive_pack' AND l1_language=$1 AND vocabulary_id=$2 AND prompt_version=$3`.
   - If hit → return `payload` immediately.
4) Cache miss:
   - Insert `pending` row (idempotent via `prompt_hash`).
   - Call LLM, parse and validate JSON.
   - Transaction: set previous `is_latest=false` for this (word,l1,module), insert new `ready` row with `prompt_version=CURRENT_PROMPT_VERSION`, `is_latest=true`, validated `payload`.
   - Return the new payload.
5) UI: show spinner during miss; optionally poll `/fetch` until `ready`.

Suggested retrieval SQL (conceptual):
```sql
SELECT payload
FROM word_ai_content
WHERE vocabulary_id = $1
  AND l1_language = $2
  AND module_type = 'deep_dive_pack'
  AND is_latest = true
  AND status = 'ready'
  AND prompt_version = $3
LIMIT 1;
```

### Additional Indexes for Versioned Cache Keys
```sql
CREATE INDEX idx_ai_content_cache_key
  ON word_ai_content(vocabulary_id, l1_language, module_type, prompt_version)
  WHERE is_latest AND status = 'ready';
```

### Prompt Guidance Adjustments
- Counts: keep the stored UI contract as EXACTLY 3 mnemonics for consistency; allow the model to return up to 5 internally, then select top 3 (see ranking below). If fewer than 3 high-quality items arrive, backfill with empties `""` to preserve schema.
- Optional reasoning (scratchpad): optionally allow a hidden scratchpad to improve quality, but require the model to output the final JSON object after the scratchpad. The backend discards non‑JSON and persists only the validated JSON object. Never store chain‑of‑thought.
- Determinism: include `prompt_version` and `prompt_hash` for reproducibility.
- Sense anchoring: Always provide the deck‑sense context to the model (`deck_sense_context`) composed of the exact L1 translation and the L2/L1 example sentence pair from the vocabulary row. Instruct the model to tailor all outputs to this sense and separately list “other_meanings” not covered by the current deck.

### Mnemonics Ranking (optional)
- Accept an optional `score` field per mnemonic in `payload.mnemonics[*].score` (0–1). If absent, compute a lightweight heuristic score (e.g., penalize overlaps, reward imagery keywords) and select top 3 for display while storing full array in payload.
- If later cross‑word analytics on mnemonic quality are needed, introduce a small normalized index table and backfill lazily.

### Handling New Modules and Field Additions
- New content modules (e.g., `famous_story`, `frequency_stats`) → create rows with new `module_type` values; store their JSON payloads without migrations.
- Per‑item field additions (e.g., IPA in `nuanced_synonyms`) → start writing the new keys into `payload`. If query performance over these new keys becomes important, add a GIN JSONB index or promote hot fields to a small auxiliary index table.



