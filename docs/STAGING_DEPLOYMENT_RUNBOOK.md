## Staging-First Deployment Runbook (Supabase + Vercel)

### Purpose
Ship safely by validating DB changes and endpoints on Staging before Production. This runbook covers env setup, migrations, verification, rollout, and rollback.

### Environments
- Supabase:
  - Production: Polyglot-Prod
  - Staging: Polyglot-Staging
- Vercel env vars per context:
  - Production → Prod Supabase URL/ANON; OPENAI keys; service role only in server routes
  - Preview (PRs) → Staging Supabase URL/ANON; OPENAI keys; service role only in server routes

### Env Vars (Staging)
- NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
- SUPABASE_SERVICE_ROLE_KEY (server-side only)
- OPENAI_API_KEY, OPENAI_ORG_ID, OPENAI_PROJECT (server-side only)

### Apply DB Changes (Staging)
Option A: Supabase Studio → SQL Editor (recommended for simplicity)
1) Paste the migration SQL (additive CREATE TABLE/INDEX/Policies) and Run.
2) Optional: create `ai_tutor_images` storage bucket (private).

Option B: Supabase CLI (schema-as-code)
```bash
supabase link --project-ref <STAGING_PROJECT_REF>
supabase db push
```

### Verify on Staging
1) Table `public.word_ai_content` exists; RLS policies present.
2) (If created) Storage bucket `ai_tutor_images` exists.
3) Vercel Preview URL → call endpoints:
   - POST /api/ai-tutor/generate { vocabularyId, l1Language }
   - GET  /api/ai-tutor/fetch?vocabularyId=&l1Language=&promptVersion=ai-tutor-v1
4) Confirm status=ready and payload; check storage for image file.

### Rollout to Production
1) Set Production env vars in Vercel (Prod Supabase URL/ANON, OPENAI, service role for server routes).
2) Apply same SQL to Production (Studio or CLI `supabase link --project-ref <PROD_REF> && supabase db push`).
3) Enable feature flag for your user first; validate UI; then enable globally.

### Rollback
- Fast disable (no data loss): tighten read RLS or set policy to `USING (false)`.
- Clean drop:
```sql
DROP TABLE IF EXISTS public.word_ai_content CASCADE;
-- optional: select storage.delete_bucket('ai_tutor_images');
```
- Park data:
```sql
ALTER TABLE public.word_ai_content RENAME TO word_ai_content_bak_YYYYMMDD;
```

### Notes
- Migrations are additive (no existing tables touched).
- Data versioning lives in the table (`schema_version`, `prompt_version`, `prompt_hash`, `is_latest`).
- Server routes must use SUPABASE_SERVICE_ROLE_KEY on the server only.


