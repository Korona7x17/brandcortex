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

## Session 4 addendum
Δ: Dashboard restyled to the AgenticSkills monochrome system (docs/agenticskills-design-system,
untracked); empty queue redirects to /new; sign-in is lockup+box via (dashboard) route group;
all deployed to brandcortex.app; branch PUSHED fb4640a..1093111 (12 commits, diff secret-scan clean)
C: inversion is the only selection signal; Geist needs Noto Sans Thai fallback; pnpm build
corrupts a live next dev (.next shared) — restart dev after local prod builds
Q: commit the design-system folder or keep the pointer (user's call)
→: R2 → cron worker → insights fetcher; first production compose still pending

## Session 5 addendum
Δ: Bare Thai names fixed at three levels — `_person()` is the only route a name takes into copy,
`voice.Honorific`/`check_names()` REJECT a draft without `คุณ` (caption + first comment), prompt and
approved example follow. Prefixed mentions stripped before looking, so a second bare mention still fails
Δ: Congratulatory register added from the owner's own post (🏆 headline · ขอแสดงความยินดีกับ คุณ<name>
จาก <club> · 👏) on `sweep`+`longevity`; four angles stay factual; two first-comment banks, register
carried through both halves of a variant
Δ: MERGED to main --no-ff (751ac81) — main went 2 tracked files -> 324. 190 pass / 9 skip
C: emoji ceiling 2, both carrying the congratulation, nudge carries none; honorific is a config-declared
voice rule scoped to declared locales; voice is the owner's to change, never the loop's (§10.4 holds)
D: D-06 honorific enforced by validator not prompt; D-07 two registers + ceiling 1->2, guidance
rewritten around respect not adjectives
Q: nothing pushed (origin still at 1400de5, main unpushed); stray untracked apps/web/lib/*.ts now
overlap the merged apps/web
→: push main → R2 → cron worker → insights fetcher; first production compose still pending

## Session 6 addendum
Δ: Copy rewritten — promo scaffolding (rotating opener + inspirational sign-off) CUT; variants now
3–5 lines differing by FORM not wording; club angle leads with คุณ{name}, club on line two
Δ: PRODUCTION finally emits คุณ — needed BOTH `railway up` AND a seed run inside the container
(`uv run python -m brandcortex.db.seed`); verified against the prod row from inside Railway
Δ: Seed-on-boot added (D-08): two fingerprints, file vs row, refuses to clobber a /settings/voice edit
Δ: Vercel connected to GitHub properly (was CLI-upload-only; the branch shown in its dashboard was a
stamp on the upload, not an integration). root=apps/web, prodBranch=main
Δ: .gitignore's bare `lib/` had hidden apps/web/lib/*.ts from the repo entirely — first git build
failed on @/lib/api; anchored the pattern and committed the three files
C: brand_config is a DB row, not code — deploying code and applying config are separate acts
C: no scene-setter, no sign-off; variants differ in shape; the club never leads a swimmer's post
Q: Railway git connection did not fire on push (container lacked the new module) — check dashboard
Q: prod row has no _seeded_from stamp, so boot-seeding will refuse until db.seed runs once there
Q: existing drafts keep frozen post_text — old queue rows still show old copy by design
→: confirm the in-flight railway up; run the one-time stamped seed in prod; then R2 → cron worker
