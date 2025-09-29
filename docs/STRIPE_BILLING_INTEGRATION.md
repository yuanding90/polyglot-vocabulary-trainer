## Stripe Billing Integration Guide

### Purpose
This document describes how to add paid subscriptions to the Polyglot Vocabulary Trainer using Stripe. It covers recommended architecture, data model, API routes, webhook processing, entitlement checks, security, testing, and rollout across environments (Local, Preview/Staging, Production).

---

### Summary of Options (and Trade‑offs)
- Stripe Checkout + Billing Portal + Webhooks (recommended MVP)
  - Hosted checkout/portal, minimal PCI/SCA burden, fast to ship. Webhooks drive entitlements.
  - Trade‑off: Less custom UI control compared to fully embedded forms.

- Stripe Elements / Payment Element (custom UI)
  - Full control over UX, fewer redirects, can embed Apple Pay/Google Pay inline.
  - Trade‑off: More code/maintenance, you must handle more edge cases.

- Payment Links
  - Fastest to test pricing with little code; workable for pilots.
  - Trade‑off: Weak in‑app integration; still need webhooks to map entitlements.

- Metered/Usage Billing
  - Bill per AI tokens/requests/time; aligns price to value.
  - Trade‑off: You must report usage and handle proration/edge cases.

Recommendation: Start with Checkout + Portal + Webhooks, then evolve to custom UI/usage billing if needed.

---

### High‑Level Architecture
1) Frontend creates a Checkout Session via `/api/billing/checkout` for a Stripe Price ID (e.g., monthly Pro).
2) User completes payment on Stripe’s hosted Checkout page.
3) Stripe sends webhooks to `/api/stripe/webhook`. We upsert subscription state into Supabase.
4) Frontend uses a simple entitlement check (`active` or `trialing`) to gate premium features.
5) Users manage plan/payment methods in Stripe Billing Portal via `/api/billing/portal`.

Notes
- Use server‑side routes for Checkout/Portal creation. Never expose the secret key client‑side.
- Verify webhook signatures and make DB writes idempotent.

---

### Data Model (Supabase)

Profiles (augment existing)
- `profiles.stripe_customer_id text` — maps Supabase user to Stripe Customer.

Subscriptions (new)
- `subscriptions.id bigserial primary key`
- `user_id uuid not null references auth.users(id) on delete cascade`
- `stripe_customer_id text not null`
- `stripe_subscription_id text not null`
- `status text not null` — e.g., `active`, `trialing`, `incomplete`, `past_due`, `canceled`, `unpaid`
- `price_id text not null` — Stripe Price ID (e.g., `price_...`)
- `current_period_end timestamptz not null`
- `cancel_at_period_end boolean not null default false`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Indexes
- `idx_subscriptions_user_id`
- `idx_subscriptions_subscription_id`

Optional (for audit/idempotency)
- `stripe_events(id text primary key, type text, created_at timestamptz, payload jsonb)` — store processed event IDs.
- `subscription_history(...)` — immutable history of status changes.

RLS
- `subscriptions`: user can select rows where `user_id = auth.uid()`; inserts/updates only allowed via service role (webhooks).
- `profiles`: user can select/update own row; only service role sets `stripe_customer_id` initially.

---

### Environment Variables
- `STRIPE_SECRET_KEY` — server‑side only.
- `STRIPE_WEBHOOK_SECRET` — for the deployed environment. Local obtains from Stripe CLI.
- `NEXT_PUBLIC_STRIPE_PRICE_PRO_MONTHLY` — public price ID for the UI to request checkout.
- `BILLING_PORTAL_RETURN_URL` — where Billing Portal returns after management (e.g., `/dashboard`).

Per‑environment
- Maintain separate variables for Local, Preview/Staging, and Production.

---

### API Routes (Next.js Route Handlers)

POST `/api/billing/checkout`
- Inputs: `priceId` (string), optional `successUrl`, `cancelUrl` (or use defaults)
- Behavior:
  1) Resolve the logged‑in user; read or create `stripe_customer_id` on `profiles`.
  2) Create Checkout Session with mode=subscription and the provided price.
  3) Return session URL to redirect the user.

POST `/api/billing/portal`
- Inputs: none (for the current user)
- Behavior: Create a Billing Portal session for the user’s `stripe_customer_id` with `return_url`.

POST `/api/stripe/webhook`
- Verify signature with `STRIPE_WEBHOOK_SECRET`.
- Handle events (idempotently):
  - `checkout.session.completed`: look up customer/subscription, upsert `subscriptions` row.
  - `customer.subscription.created|updated|deleted`: upsert subscription row.
  - `invoice.payment_failed`: mark status accordingly (e.g., `past_due` or leave to Stripe dunning).
- Store processed event IDs to prevent duplicate side effects.

Notes
- Use Stripe’s expand params where helpful (e.g., expand `subscription.latest_invoice.payment_intent`).
- Always guard DB writes with idempotency (event ID unique constraint or `stripe_events`).

---

### Entitlement Checks (Gating)
- Server: wrap premium endpoints with a check like `status in ('active','trialing')` AND `current_period_end > now()`.
- Client: read a `/api/me/subscription` endpoint (or include in your session bootstrap) to conditionally render premium UI.
- Never trust the client alone. Server is the source of truth for access control.

Helper Logic
- A user is entitled if:
  - There exists a `subscriptions` row for `user_id` with `status in ('active','trialing')` AND
  - `cancel_at_period_end = false` OR `now() < current_period_end`.

---

### Pricing, Trials, Coupons, Proration
- Stripe Products/Prices are the source of truth. Reference Price IDs from env.
- Trials: either set trial days on the Price or use trial coupons.
- Coupons/Promos: enable on Checkout; Stripe manages tax‑inclusive math.
- Proration: default Stripe behavior is sensible; communicate clearly in UI.

---

### Tax, Invoicing, Receipts
- Stripe Tax (recommended for global customers): auto tax collection and reporting.
- Receipts/Invoices: enabled via Stripe; optionally email via Stripe or your ESP.

---

### Security & Compliance
- Do not expose `STRIPE_SECRET_KEY` to the browser.
- Verify webhook signatures with `STRIPE_WEBHOOK_SECRET`.
- Use idempotency keys for write operations where relevant.
- SCA/3DS is handled by Checkout or Payment Element.

---

### Testing & Local Development
Local Steps
1) Set test keys in `.env.local`.
2) Start dev server.
3) Use Stripe CLI:
   - `stripe listen --forward-to localhost:3000/api/stripe/webhook`
   - Copy the CLI‑provided webhook secret into env while testing.
4) Create a test customer/checkout via the UI.
5) Inspect webhook logs; confirm a `subscriptions` row is created/updated.

Scenarios to Validate
- New checkout success (active/trialing status).
- Upgrade/downgrade proration.
- Cancel at period end and renewal.
- Payment failures -> dunning -> recovery.

---

### Deployment & Environments
- Keep Test vs Live keys distinct; never mix.
- Vercel Preview (Staging): separate Stripe account or test mode; separate webhook endpoint.
- Production: create a new live webhook endpoint and set `STRIPE_WEBHOOK_SECRET` accordingly.
- Database migrations: add `stripe_customer_id` to `profiles` and create `subscriptions` (with indices/RLS).

---

### Mobile & Platform Considerations
- Checkout supports Apple Pay/Google Pay in mobile web (domain verification may be required for Apple Pay).
- If you later ship native apps, review App Store/Play Store policies for in‑app purchases vs external purchases.

---

### Roadmap / Future Enhancements
- Customer Portal deep links for plan changes and payment method updates.
- Usage‑based add‑on for AI content (report usage per period).
- Pausing subscriptions, grace periods, hard locks.
- Admin dashboard: manual entitlements, refunds, promo credits.
- Analytics: revenue, churn, trial conversion funnels.

---

### Appendix A — Suggested SQL (Supabase)

Profiles augmentation
```
alter table profiles add column if not exists stripe_customer_id text;
create index if not exists idx_profiles_stripe_customer_id on profiles (stripe_customer_id);
```

Subscriptions table
```
create table if not exists subscriptions (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  stripe_customer_id text not null,
  stripe_subscription_id text not null,
  status text not null,
  price_id text not null,
  current_period_end timestamptz not null,
  cancel_at_period_end boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_subscriptions_user_id on subscriptions (user_id);
create index if not exists idx_subscriptions_subscription_id on subscriptions (stripe_subscription_id);
```

Basic RLS (adapt as needed)
```
alter table subscriptions enable row level security;
create policy "Users can read own subscription" on subscriptions
  for select using (user_id = auth.uid());
-- Writes via service role only (no insert/update/delete policies for anon/auth)
```

---

### Appendix B — Event Handling Map (Webhooks)
- `checkout.session.completed` →
  - Derive `customer`, `subscription`, `price`; upsert `subscriptions` for the mapped `user_id`.
- `customer.subscription.created|updated` →
  - Upsert status, price, `current_period_end`, `cancel_at_period_end`.
- `customer.subscription.deleted` →
  - Mark as `canceled` (keep row for history).
- `invoice.payment_failed` →
  - Mark `status` or wait for Stripe’s dunning/recovery to update; optionally notify user.

Idempotency
- Reject duplicate processing via a `stripe_events` table keyed by event `id`.


