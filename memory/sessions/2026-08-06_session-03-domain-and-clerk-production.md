# Session Log – 2026-08-06_03
Tags: [Domain][DNS][Clerk-production][Cutover][Verified]
Repo: brandcortex@HEAD on scaffold/thaiswim-facebook-mvp
Context loaded: continuation of session 02 (same day)

## Notes

brandcortex.app went from unpointed to fully cut over to a production Clerk instance in one arc.

**Domain.** User wired brandcortex.app on Vercel (apex primary, no www — their choice, correct for
a canonical apex URL). DNS lives at Namecheap (registrar-servers nameservers), not Vercel — checked
NS before assuming, which is why the Clerk records went to the right place first try.

**Clerk dev → production.** Cloned instance, new keys. The live publishable key decodes to
clerk.brandcortex.app, which is also the issuer. Five CNAMEs at Namecheap (clerk, accounts,
clkmail, clk._domainkey, clk2._domainkey — read off Clerk's own Domains page rather than quoted
from memory). Clerk's checker lagged behind real DNS (its resolvers negative-cache); dig against
1.1.1.1 + curl --resolve proved the FAPI live while both Clerk's UI and the local Mac resolver
still said otherwise. Verified → certs issued → deployed.

**Key hygiene.** .env keeps BOTH pairs: CLERK_SECRET_KEY (test, localhost — a production Clerk
instance will not accept localhost) and CLERK_SECRET_KEY_LIVE (Vercel only). The user initially
added the live key as a duplicate CLERK_SECRET_KEY line — last-one-wins would have silently broken
local dev; renamed. The previously-leaked dev secret is now moot for production (new instance, new
keys); dev-instance rotation still open.

**Clean sign-in URL.** User flagged /sign-in?redirect_url=... as ugly. Middleware now sends
homepage arrivals to a bare /sign-in and keeps redirect_url only for deep links, which still
return to where they pointed. Typechecked, built, deployed.

**Verified live at cutover:** https://brandcortex.app/sign-in renders clean with no Development
banner; API channels facebook ok; bare /posts 401; user's production account pre-created so
restricted mode never had to drop.

C: Production Clerk refuses localhost — local dev stays on the test instance forever; .env carries
   both pairs, names must differ (last-one-wins in env files)
C: Clerk's DNS checker and local resolvers both lie for a while after records change — verify with
   dig @1.1.1.1 and curl --resolve before believing either
C: DNS for brandcortex.app is at Namecheap; Vercel only hosts. Check NS before adding records
Δ: brandcortex.app live (apex, canonical); 5 Clerk CNAMEs verified; certs issued
Δ: Vercel env: live pk + sk (CLERK_SECRET_KEY_LIVE from .env); Railway: CLERK_ISSUER →
   https://clerk.brandcortex.app; both redeployed together, after JWKS answered
Δ: middleware.ts — clean /sign-in, redirect_url only for deep links
Q: Google sign-in on production may fail until custom Google OAuth credentials are set (Clerk's
   shared creds are dev-only) — email code works regardless; set up Google Cloud OAuth client if
   the Google button matters
Q: dev-instance secret key still worth rotating (leaked into session-02 transcript)
Q: unchanged from session 02: cron worker + R2, insights fetcher, api.brandcortex.app, ~7 commits unpushed
→: User signs in at brandcortex.app and composes the first production draft
→: R2 → cron worker → insights fetcher (in that order; worker needs shared storage)
