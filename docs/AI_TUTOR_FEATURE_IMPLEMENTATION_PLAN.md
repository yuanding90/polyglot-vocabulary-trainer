## AI‑Tutor Feature – Implementation Plan (Cache‑Aside, JSONB Solution 1)

### 0) Summary
Add an “AI‑Tutor” button in Discovery and Review (visible in Review only after reveal). On click, fetch text insights and an image from OpenAI, store results in `word_ai_content` (JSONB Solution 1), and render a structured panel similar to “Words Similar in Spelling”. Follow the Cache‑Aside pattern so first use may wait; subsequent requests return instantly.

References:
- Data model and RLS: `docs/AI_WORD_CONTENT_JSONB_PROPOSAL.md`
- Engineering/versioning workflow: `docs/ENGINEERING_VERSIONING_AND_RELEASE_GUIDE.md`

### 1) UX and Functional Requirements
- Buttons
  - Discovery: Show an “AI‑Tutor” button near the existing actions.
  - Review: Show the “AI‑Tutor” button only after the answer is revealed.
- Panel behavior
  - On click: show loading state; use Cache‑Aside to fetch or generate.
  - Display sections reminiscent of the HTML app’s Deep Dive, organized under headings:
    - Analysis → Usage context (nuance/register), Collocations (list), Examples (3), Connections (nuanced synonyms with distinction notes; antonyms; word family), Mnemonic aid.
    - Mnemonics → Exactly 3 entries (phonetic link, absurd story, visualization cue).
    - Image → 1024×1024 (low quality) generated from the image brief; displayed with caption.
  - Gracefully hide empty sections (`""` or `[]`).
  - Mobile: stack sections with collapsible details; reuse spacing rules from SimilarWordsPanel.

### 2) Provider and Models (OpenAI)
- Text: `gpt-4.1-nano` (as requested) for JSON output described in the AI Word Content spec.
- Image: `gpt-image-1` with `size=1024x1024`, `quality=low`.
- Env var: `OPENAI_API_KEY` (server‑only; never exposed in client). Add to Vercel (Production/Preview) and `.env.local` for local.

### 3) Data Model (reuse JSONB Solution 1)
- Table: `word_ai_content` (already specified in proposal)
  - `module_type = 'ai_tutor_pack'` (text + image as one logical pack)
  - `provider='openai'`, `model='gpt-4.1-nano'`, `schema_version='v1'`, `prompt_version=CURRENT_PROMPT_VERSION`
  - `payload` JSON structure:
    ```json
    {
      "analysis": { ... },
      "mnemonics": [ {"type": "phonetic_link", "content": "..."}, {"type": "absurd_story", "content": "..."}, {"type": "visualization_cue", "content": "..."} ],
      "image_brief": { "title": "", "prompt": "", "style": "", "elements": [], "composition": "", "lighting": "", "color_palette": "", "aspect_ratio": "1:1", "safety_notes": "" },
      "image_asset": { "storage_path": "", "public_url": "", "width": 1024, "height": 1024 }
    }
    ```
  - Idempotency: `prompt_hash` over normalized inputs.
  - Index: `idx_ai_content_cache_key (vocabulary_id, l1_language, module_type, prompt_version)` filtered on `is_latest AND status='ready'`.

### 4) Cache‑Aside Workflow
- Inputs: `{ vocabularyId, l1Language, includeAnalysis=true }`; derive `(L2 language, target word, translation, L2 IPA?)` from DB.
- Step A (read‑through):
  ```sql
  SELECT payload FROM word_ai_content
   WHERE vocabulary_id=$1 AND l1_language=$2 AND module_type='ai_tutor_pack'
     AND is_latest AND status='ready' AND prompt_version=$3
   LIMIT 1;
  ```
  - If hit: return immediately.
- Step B (miss → generate):
  - Insert `pending` row (idempotent by `prompt_hash`).
  - Call OpenAI Text (gpt‑4.1‑nano) with the structured prompt; parse/validate JSON.
  - Using `image_brief`, call OpenAI Image (`gpt-image-1`, 1024×1024, quality=low).
  - Upload image to Supabase Storage bucket (e.g., `ai_tutor_images/`), get public URL or signed URL.
  - Transaction: flip prior `is_latest=false`, insert `ready` row with merged payload (text + image_asset), `is_latest=true`.
  - Return payload.
- UI: show spinner; on miss, poll until `ready` (or wait synchronously on first run).

### 5) API and Server Components
- Route handlers (Next.js) or Supabase Edge Functions. Start with Next.js Server Route Handlers:
  - POST `/api/ai-tutor/generate`
    - Body: `{ vocabularyId, l1Language, includeAnalysis }`
    - Auth: server‑side; use service role for DB writes
    - Behavior: Cache‑Aside; returns `{ status: 'ready'|'pending', payload? }`
  - GET `/api/ai-tutor/fetch?vocabularyId=&l1Language=&promptVersion=`
    - Returns latest ready payload (if any) for the cache key.
  - Internal helper: `buildAiTutorPrompt({L1, L2, word, translation, ipa?, includeAnalysis })`
  - Internal helper: `uploadImageToStorage(base64) → { storage_path, public_url }`

Notes:
- Use server‑only `OPENAI_API_KEY` (Edge runtime or Node runtime). Do not call OpenAI from the client.
- Consider request timeouts and retries with exponential backoff.

### 6) Prompt (OpenAI Text)
- System: “You are an expert linguist, language tutor, and memory coach. Output only a single JSON object; no extra text.”
- User: The structured prompt from `AI_WORD_CONTENT_JSONB_PROPOSAL.md` with required schema keys. Enforce EXACTLY 3 mnemonics. Permit internal reasoning but require the final block to be pure JSON; backend parses only JSON. If fewer high‑quality items, allow `""`/`[]` placeholders.

### 7) Image Generation
- Model: `gpt-image-1` with `size=1024x1024` and `quality=low`.
- Prompt: expand `image_brief.prompt` with title/style/elements/composition/lighting; append safety notes.
- Output: base64; upload to Supabase Storage (`ai_tutor_images`) → obtain `public_url` (or signed URL if private policy is preferred).

### 8) Security, RLS, and Storage
- `word_ai_content` RLS: SELECT for authenticated users (or public if desired); INSERT/UPDATE/DELETE limited to service role.
- Storage bucket: `ai_tutor_images`
  - Default private; app issues short‑lived signed URLs when rendering.
  - Alternative: public bucket for simplicity; configure caching headers.

### 9) UI Integration
- New component: `AITutorPanel.tsx`
  - Props: `{ vocabularyId: number, l1Language: string, show: boolean }`
  - State: `loading | error | payload`
  - Behavior: on mount or button click: call `/api/ai-tutor/fetch`; if miss, call `/api/ai-tutor/generate` then poll.
  - Render:
    - Analysis: grouped subsections with headings; show lists for collocations/examples/synonyms/antonyms/word_family.
    - Mnemonics: 3 cards with labels (phonetic link / absurd story / visualization cue).
    - Image: Next.js `<Image>` with the retrieved URL; caption from `image_brief.title`.
  - Mobile: collapsible details; reuse spacing classes from SimilarWordsPanel; avoid sidebars.
- Buttons placement:
  - Discovery: below main content and above Similar Words.
  - Review: below reveal area; only visible when `showAnswer=true`.

### 10) Feature Flag and Quotas
- Flag key: `ai_tutor` (per‑user in `user_profiles.enabled_features` JSONB)
- Rate limits: e.g., 30 generations/day/user; global ceiling to control cost.
- Cache reuse: idempotency ensures repeated clicks do not multiply costs.

### 11) Validation and Error Handling
- Validate text JSON with Zod/JSON Schema; reject malformed responses.
- If image generation fails, still store text payload; set `image_asset` empty and show a retry button.
- UI shows actionable errors with retry/backoff.

### 12) Observability
- Log: timings, prompt_version, token usage (if exposed), success/failure, storage upload status.
- Metrics: success rate, p95 latency, cache hit ratio, daily cost.

### 13) Migrations and Setup Checklist
- Ensure `word_ai_content` exists with indexes (see proposal doc).
- Create storage bucket `ai_tutor_images` and set policies (private with signed URLs or public).
- Add env vars:
  - Local `.env.local`: `OPENAI_API_KEY`, Supabase local keys
  - Vercel Preview: Staging Supabase keys + `OPENAI_API_KEY`
  - Vercel Production: Prod Supabase keys + `OPENAI_API_KEY`
- OAuth redirects configured for each environment.

### 14) Step‑by‑Step Tasks
1) Add `OPENAI_API_KEY` to local and Vercel envs; verify not exposed to client
2) Create `ai_tutor_images` bucket and set policy; helper for signed URLs
3) Implement server helpers: prompt builder, OpenAI client, image upload
4) Implement `/api/ai-tutor/fetch` (read path)
5) Implement `/api/ai-tutor/generate` (Cache‑Aside write path with transaction)
6) Add `AITutorPanel.tsx` and hook
7) Wire buttons in Discovery and Review (gated by `showAnswer` in Review)
8) Add feature flag check and a basic per‑user quota
9) Styling and mobile UX parity with SimilarWordsPanel
10) Local tests (unit for helpers; integration for routes with mocked OpenAI)
11) Staging rollout: push migrations (if any), test Preview URL, RLS check
12) Production: merge, apply envs, verify minimal smoke tests

### 15) Risks and Mitigations
- Cost spikes → quotas and cache reuse; prompt_version pinning
- Latency → spinner + background polling; show cached results when available
- Invalid JSON → strict validation; provider retries with safer temperature
- RLS misconfig → explicit anon/service tests before prod

### 16) Open Questions
- Make image bucket public for simplicity or private with signed URLs?
- Default `l1_language` selection rules (user profile vs deck default)?
- Allow regenerate force even if cache exists (e.g., `force=true`)?


