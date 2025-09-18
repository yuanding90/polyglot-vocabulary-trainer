## Engineering Versioning and Release Guide

This guide defines how we iterate quickly while keeping production stable across Vercel (frontend) and Supabase (backend).

### Objectives
- Fast iteration with preview environments
- Safe production releases with clear rollback
- Database schema managed as code
- Consistent versioning for code, data, and AI content

### Environments and Isolation
- Supabase projects:
  - Production: Polyglot-Prod (live users)
  - Staging: Polyglot-Staging (preview deploys, QA)
  - Local: Supabase CLI (Docker) for development
- Vercel env vars per context:
  - Production: Prod Supabase URL/Anon Key
  - Preview: Staging Supabase URL/Anon Key
  - Development: .env.local (Local Supabase)

Each environment must have correct OAuth redirect URLs and site URL configured in Supabase.

### Git Workflow – Trunk-Based Development (TBD)
- main: protected trunk; always deployable
- Branches: short-lived from main
  - feat/: features (e.g., feat/ai-deep-dive)
  - exp/: experiments you might discard
  - fix/: bug fixes
- PRs: required; use squash-merge to keep history clean
- Preview Deployments: Vercel builds each PR against Staging Supabase

### Database: Schema-as-Code with Supabase CLI
1) Start local stack for feature work
```bash
supabase start
```
2) Make schema changes locally (Studio or SQL files)
3) Generate migration from local diff
```bash
supabase db diff --schema public -f <migration_name>
```
4) Commit migration under supabase/migrations
5) Apply migrations to Staging before QA
```bash
supabase link --project-ref <STAGING_PROJECT_REF>
supabase db push
```
6) After approval, apply to Production in a controlled window
```bash
supabase link --project-ref <PROD_PROJECT_REF>
supabase db push
```

Best practices:
- Prefer additive, backward-compatible migrations; remove fields only after code no longer depends on them
- Use idempotent SQL (IF NOT EXISTS) where possible
- Separate data backfills from schema changes; make backfills resumable
- Test RLS changes explicitly with anon vs service-role tokens
- Take/verify backups before destructive changes

### Feature Flags
- Purpose: ship code early, release features safely
- Minimal implementation: add `enabled_features JSONB` to `user_profiles` and check flags in code
```ts
if (userHasFeature('experimental_srs')) { /* new path */ } else { /* stable path */ }
```
- Benefits: per-user enablement, instant kill-switch without redeploy
- Optional: move to a hosted flag service later

### Release Flow (End-to-End)
1) Create branch from main
2) Build feature + local tests; run local Supabase; validate RLS
3) Generate and commit migrations
4) Open PR → Vercel Preview (Staging Supabase)
5) Apply migrations to Staging; run smoke/E2E tests against preview URL
6) Stakeholder QA and sign-off
7) Merge to main (squash); apply migrations to Production
8) Promote Vercel Production deployment
9) Post-release checks; monitor logs and metrics

Rollback strategy:
- Code: revert merge commit on main; redeploy
- DB: keep rollback scripts or reversible migrations; if not possible, provide compensating migration or restore from backup
- Flags: disable feature instantly as first response

### Observability and Safety
- Logs: Vercel functions/routes, Supabase Edge Functions, database logs
- Alerts: set basic alerts for high 5xx rate, auth errors, and DB errors
- Cost controls: monitor AI and database usage; set daily caps for AI jobs

### AI Content Versioning (JSONB Solution 1)
- Table: `word_ai_content` (see AI_WORD_CONTENT_JSONB_PROPOSAL.md)
- Versioning:
  - `schema_version`: output schema changes
  - `prompt_version`: prompt iteration
  - `prompt_hash`: idempotency key of normalized inputs
  - `is_latest`: latest per (vocabulary_id, l1_language, module_type)
- Cache-Aside pattern:
  - Try latest row with CURRENT_PROMPT_VERSION; return on hit
  - On miss, insert pending, call LLM, validate, upsert ready, flip latest
- Reasoning policy: never store chain-of-thought; persist only validated JSON

### Environment Variables and Secrets
- Local: `.env.local` (never commit)
- Vercel: set per-environment; do not reuse prod secrets in preview/dev
- Supabase keys: anon key in client only; service key used only in server/Edge Functions

### OAuth and Redirects
- Maintain redirect URIs per environment (Local, Preview, Prod)
- For local device testing (LAN IP), ensure Supabase Site URL and authorized redirect URIs are updated temporarily

### Testing Strategy
- Unit: utils, hooks, pure functions
- Integration: API routes/services with mocked Supabase
- E2E (smoke): against Vercel Preview using Staging Supabase (auth + minimal flows)
- RLS tests: ensure SELECT/INSERT/UPDATE/DELETE behave for anon/auth/service

### Data Management
- Backups: ensure regular backups on Production; take on-demand before major migrations
- Migrations order: add columns/indexes first; deploy code; remove legacy later
- Long-running tasks: use jobs/cron or batch scripts; ensure resumability and logging

### Documentation and Governance
- For every feature:
  - Update docs/ with feature overview and any schema changes
  - Include a “Release Checklist” in PR description (migrations applied? flags default off? redirects updated?)
  - Link to preview URL and test credentials if needed

### Command Reference
```bash
# Start local Supabase
supabase start

# Create migration from local diff
supabase db diff --schema public -f add_ai_module

# Link and push to Staging
supabase link --project-ref <STAGING_PROJECT_REF>
supabase db push

# Link and push to Production
supabase link --project-ref <PROD_PROJECT_REF>
supabase db push
```

### Open Questions
- Who can approve PRs and production migrations?
- Do we want automated E2E gates before merging to main?
- What’s our target SLO for AI job latency and success rate?

### Appendix: Checklist (per release)
- [ ] Migrations generated and committed
- [ ] Staging DB migrated; preview deployment tested
- [ ] Feature flags default set (off unless intended)
- [ ] OAuth redirects verified for target environment
- [ ] RLS verified for new tables
- [ ] Production backup confirmed/recent
- [ ] Monitoring/alerts updated if needed
- [ ] Release notes written and shared


