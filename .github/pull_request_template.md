## PR Title

Short summary of the change. Use conventional prefixes in branch names: `feat/`, `exp/`, `fix/`.

### What’s in this PR?
- [ ] Feature/bug summary
- [ ] Screenshots or recordings (if UI)
- [ ] Linked issue(s): #

### Release Checklist
- [ ] Migrations generated and committed (`supabase/migrations/*`)
- [ ] Staging DB migrated (`supabase link --project-ref <STAGING>` + `supabase db push`)
- [ ] Preview URL tested (Vercel Preview, connected to Staging):
      - URL: 
      - Key flows verified (auth, study, dashboard)
- [ ] Feature flags default set (off unless intended) and ramp plan noted
- [ ] OAuth redirect URIs updated for target environment (Supabase → Auth settings)
- [ ] RLS verified for new/changed tables (anon vs authenticated vs service-role)
- [ ] `word_ai_content` RLS verified if touched (read: public/auth; writes: service only)
- [ ] Backups confirmed/recent for Production before release
- [ ] Monitoring/alerts updated if needed
- [ ] Rollback plan included below

### Database
- Affected tables: 
- New migrations: 
- Backfill or data migration required: [ ] No  [ ] Yes (describe)

### Environment Variables
- Added:
- Changed:
- Removed:

### Rollout Plan
- Feature flag gating: 
- Rollout steps (Staging → Production): 
- Owner(s) watching logs post-release: 

### Testing
- Unit/Integration: 
- E2E/Smoke on Preview URL: 
- RLS test results (anon/auth/service): 

### Risk and Rollback
- User-impacting risk: 
- Rollback steps:
  1) Disable flag(s)
  2) Revert commit on `main`
  3) DB rollback or compensating migration (if needed)


