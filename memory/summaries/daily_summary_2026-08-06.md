# BRIEF_SUMMARY (2026-08-06)

C: Login for Business injects the use case's permission bundle — every referenced permission must
be Added or all logins fail. Auth fails closed everywhere: no CLERK_ISSUER → 503, opt-out is
explicit. session_scope() never commits. railway up roots at linked dir — use --path-as-root
D: pages_read_user_content Added (D-01); fail-closed auth (D-02/03); publish refuses foreign-host
links (D-04); volume now, R2 before cron worker (D-05)
Δ: Meta wall fell (one "+ Add"); PAGE token minted, expires never, encrypted in channel_tokens
Δ: First live post's comment carried localhost:9000 — data fixed, guard added, worker isolates it
Δ: PRODUCTION EXISTS: api-production-b008.up.railway.app (channels ok, /posts 401) +
brandcortex-ravenbone.vercel.app (Clerk wall). Prod DB seeded, token row copied
Q: brandcortex.app DNS unpointed; no cron worker yet (scheduled posts won't fire — publish-now
works); Vercel is CLI-push only; rotate Clerk secret (leaked into session transcript, my grep)
→: Sign in on prod, compose first production draft → R2 + cron worker → insights fetcher → DNS

## Session 3 addendum
Δ: brandcortex.app LIVE with production Clerk (issuer clerk.brandcortex.app, 5 CNAMEs at
Namecheap, certs issued); clean /sign-in URL deployed; both platforms redeployed post-JWKS
C: prod Clerk refuses localhost — .env keeps test pair + CLERK_SECRET_KEY_LIVE (Vercel-only);
DNS checkers lie after changes — dig @1.1.1.1 + curl --resolve are the truth
Q: Google button needs custom OAuth creds on prod (email code fine); dev secret rotation open
→: first production compose → R2 → cron worker → insights fetcher
