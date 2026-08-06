# Session Log – 2026-08-06_02
Tags: [Auth][Clerk][Deploy][Railway][Vercel][Link-guard][Production]
Repo: brandcortex@f56e0e6 on scaffold/thaiswim-facebook-mvp
Context loaded: continuation of session 01 (same day)

## Notes

Three arcs: the dev-link bug the first live post exposed, the auth wall, and the first deploy.

**The published post carried `localhost:9000` in its live comment.** Links are baked at draft time
from BRAND_SITE_URL and never re-derived; all four posts composed on Aug 5 predated the switch to
production. Fixed in three layers: data (rewrote the three unpublished posts; user fixed the live
comment by hand and the record was synced), a publish-time guard in the orchestrator (link hosts
must match the current brand site — a computation, no brand string in core), and a worker fix the
guard forced: run_once caught only PublishFailed, so the guard's InvalidTransition on the first due
post would have killed the whole cycle. "Published by BrandCortex" byline: admin-only, fine.

**Auth, fail closed end to end.** API: every route but /health requires a verified Clerk session
JWT (JWKS signature, issuer, azp) — unconfigured serves 503s, local dev opts out explicitly with
AUTH_DISABLED=true. Latent bug found: comma-separated list env vars crashed startup before the
validator ran (pydantic-settings decodes lists pre-validator; NoDecode fixes it) — CORS_ALLOW_ORIGINS
had the same bug and had never been exercised. Web: Clerk v7, on iff the publishable key is present;
token attached server- and client-side; /card/[id] proxy because an <img> cannot carry a bearer
token. Clerk plan facts: Allowlist is Pro; free equivalent is restricted mode (Configure → Protect →
Restrictions), enabled after the owner became user #1.

**First production deploy.** API + Postgres on Railway (project b18f9576, service api, volume /data
for captured cards), dashboard on Vercel (project brandcortex, team ravenbone). Live and verified:
https://api-production-b008.up.railway.app (health ok, /posts 401, channels facebook ok — encrypted
token row copied, same Fernet key) and https://brandcortex-ravenbone.vercel.app (redirects to Clerk
sign-in). Four deploy snags, all resolved:
- `railway up` archives from the *linked* directory (repo root), not cwd — Railpack saw a monorepo
  and gave up. `railway up apps/api --path-as-root` is the fix.
- `session_scope()` never commits (caller's job, by design) — my token-copy script assumed it did;
  the insert silently rolled back. Committed explicitly; channels went green.
- Vercel CLI too old for its own API; upgraded mid-flight.
- Vercel Deployment Protection fronted production with vercel.com SSO ahead of Clerk. Disabled via
  PATCH /v9/projects (ssoProtection: null); Clerk is the wall.

Also: Chrome held dead sockets for localhost:3000 after my dev-server restarts and error-paged
without sending requests — cost the user a "page doesn't work" scare twice (the second time the
composer looked gutted; it was a stale render from an API-reload window). 127.0.0.1 worked
throughout; both origins now authorized. My redaction slip: a grep of .env exposed the Clerk secret
key in the session transcript — rotation recommended to the user, one click in dev mode.

## Artifacts

- api/src/brandcortex/api/auth.py (new) · main.py (lock wiring) · config.py (clerk vars, NoDecode,
  postgres:// normalizer) · workers/publisher.py (cycle isolation + cron entrypoint)
- api/core/orchestrator.py (_foreign_link_hosts + publish guard)
- api/Dockerfile + .dockerignore (migrate-then-serve; boot-tested locally before deploy)
- web/middleware.ts · app/sign-in/ · app/card/[id]/route.ts · lib/server-auth.ts · lib/api.ts
- docs/deploy.md (runbook) · docs/log/railway-{build,deploy}-2026-08-06.log
- Commits: b2e9fca link guard · acb6e51 publisher fix · 13dfab2 auth+deploy · fabbb2f env docs ·
  f56e0e6 postgres scheme + logs

C: Auth is fail-closed at every layer — an API deployed with no CLERK_ISSUER serves only /health;
   there is no env-var omission that leaves publish endpoints open
C: The dashboard's auth is for people; the API is the boundary — middleware bypass still dies at 401
C: session_scope() never commits; every caller owns its transaction (bit me, now recorded)
C: railway up roots at the linked directory, not cwd — always --path-as-root apps/api
C: Links bake at draft time; the publish guard compares hosts against current BRAND_SITE_URL
D: See D-2026-08-06-02..05 in design_decisions.md
Δ: production exists: Railway api+Postgres+volume, Vercel dashboard, both verified
Δ: prod DB seeded (thaiswim) + encrypted token row installed; facebook channel ok in production
Q: brandcortex.app DNS not pointed (registrar unknown to me — ask user)
Q: publisher cron worker service not yet created on Railway — scheduled posts will NOT fire in
   production until it exists; publish-now works (API process publishes inline)
Q: cards on Railway volume; R2 needed before the worker exists (separate services cannot share a
   volume) — capture path is S3-ready already
Q: Clerk secret key appeared in session transcript (my grep); rotate in Clerk dashboard
Q: Vercel deploys are CLI-push only — no git integration; pushes do not auto-deploy
→: User signs in on the production dashboard and composes a first production draft
→: Railway cron service for the publisher (*/5) once R2 exists; insights fetcher next
→: DNS: brandcortex.app → Vercel, api.brandcortex.app → Railway
