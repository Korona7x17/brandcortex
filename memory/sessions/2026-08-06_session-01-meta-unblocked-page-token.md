# Session Log – 2026-08-06_01
Tags: [Meta-auth][Unblocked][Facebook][Browser-driven]
Repo: brandcortex@fb4640a on scaffold/thaiswim-facebook-mvp (pushed; no code changes this session)
Context loaded: active_context.json, daily_summary_2026-08-05.md, session-02

## Notes

The Meta wall from 2026-08-05 fell to one click. Root cause, found and verified by driving the
user's browser (Claude-in-Chrome) rather than sending them around Meta's UI:

- The "Manage Pages" use case *referenced* `pages_read_user_content` but the permission had never
  been **added** to the app — empty Status column, un-clicked "+ Add" button on the use-case
  customize page.
- Facebook Login for Business injects the use case's whole permission bundle server-side, so a
  dialog request whose `scope` param carried only our five scopes still failed on the un-added one.
  Reproduced firsthand: my own request provably contained no `pages_read_user_content`, dialog
  rejected it anyway.
- Clicked "+ Add" → status "Ready for testing" → the identical dialog rendered normally two
  minutes after failing.

Also learned before the browser connected (mechanical checks, no UI): the `.env` token was a USER
token from ~Aug 3-4 that expired Aug 4 — proof the dialog had worked *before* the use-case/config
setup on Aug 5 introduced the injection. And unauthenticated probes of the dialog showed no scope
was invalid pre-login, which localized the failure to session + app-config evaluation.

Then drove the full flow: Continue as user → ThaiSwim.com Page only (current-pages-only, second
Page left unchecked) → Save → captured the auth code off the thaiswim.com/oauth/callback redirect
→ `authorize.py` exchange chain: code → user token → long-lived → **PAGE token, page
1223598310834457, expires never, 7 scopes, stored encrypted in channel_tokens**.

`GET /health/channels` → `facebook: ok, problems: []`.

Cleanup: root `.env` `FACEBOOK_PAGE_ACCESS_TOKEN` line commented out (was the expired Aug-4 user
token; only `authorize.py` reads that var as an optional input — the adapter reads the DB).
Note `apps/api/.env` is a symlink to the repo root `.env`.

## Artifacts

- No code changed. State changes only: Meta app config (permission added), channel_tokens row
  (encrypted page token for thaiswim), root .env (dead line commented).
- memory/state/active_context.json@this-commit

C: Login for Business injects the use case's permission bundle — every permission a use case
   references must be Added to the app or all logins fail, even ones not requesting it
C: The Page token never expires; data-access windows and App Review remain the renewal surfaces
C: Diagnose Meta by driving the browser or by API probe — never by sending the user on UI guesses
   (yesterday's lesson, applied today, and it worked first try)
D: D-2026-08-06-01 — pages_read_user_content added to the app ahead of Phase 3 need
Δ: Meta app 1278952477505548: +pages_read_user_content (Ready for testing)
Δ: channel_tokens: +thaiswim facebook PAGE token (never expires, 7 scopes)
Δ: .env: FACEBOOK_PAGE_ACCESS_TOKEN cleared — channel_tokens is authoritative
Q: First real publish not yet attempted — the queued approved draft is ready; needs user go-ahead
   (public post on the live Page)
→: Publish the queued draft → verify photo + first-comment link on the real Graph
→: Insights fetcher next — every day before it runs is audience data lost forever
→: Then: editor-preference loop, Clerk auth, Railway deploy, R2 for captured cards
