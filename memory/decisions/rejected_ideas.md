# Rejected Ideas

## R-2026-08-04-01 — Runtime drift check between caption and live-rendered card

Proposed a `drift_check` comparing draft-time facts against a re-fetch at publish. User challenged the
premise; they were right. The studio already freezes the image by downloading it, and BrandCortex
fetching at publish *introduced* a window that didn't otherwise exist. Replaced by capturing the PNG at
draft time (D-2026-08-04-01). Superseded, not deferred.

## R-2026-08-04-02 — Hardcoding `locale = "th"` throughout

Briefly hardened after "no need for English cards". Reversed: English is needed for future
English-language tenants. Locale is now resolved per item. Kept as a warning — a constant is cheap to
add and expensive to find later.

## R-2026-08-04-03 — Adding a skeptic agent to the caption path

Considered after the graph-engineering discussion. Rejected as disproportionate: three sentences of
Thai, already covered by numeric grounding + voice validator + human review. Adding an LLM reviewer
there costs latency and money to second-guess something a person reads anyway. Adversarial review
belongs only in the learning loop, where model output silently becomes instructions for every future post.

## R-2026-08-04-04 — OAuth dialog via redirect URI for the Meta token

Three attempts (facebook.com redirect, thaiswim.com redirect, two Graph versions). Blocked by App
Domains rules and then by "No redirect URI in the params". Graph API Explorer separately blocked by a
cached invalid scope. Abandoned in favour of the System User route (D-2026-08-04-T03), which needs no
redirect and no dialog.

## R-2026-08-05-01 — Automated line-wrap sweep to make `ruff check` pass

Wrote a tokenize-based script to wrap over-long comment and docstring lines at column 100. It wrapped
*lines* greedily rather than reflowing *paragraphs*, so a 103-character line became 100 characters
plus an orphaned three-character word on its own line — across ~40 files, including ones the session
had no other reason to touch. Reverted entirely: `git checkout` for files not otherwise changed, full
rewrite for the day's own, then `git diff --name-only` checked against the intended list.

The lesson is the unit, not the tool: prose reflows by paragraph. The underlying question — 281
docstring lines sit at 101–104 against a 100 limit — is still open and is a one-line decision either
way.

## R-2026-08-05-02 — Duplicating the ThaiSwim card engines into BrandCortex

The user asked whether the engines could be copied over and rewired. Rejected: it is 379 lines of
route plus the Prisma client, the payload builders, the format helpers and the font loading — and
from that moment there would be two definitions of what a ThaiSwim card looks like. Change a font on
their side and the card in the Facebook post quietly stops matching the card the studio downloads.
Calling the public render API costs one HTTP GET and keeps one source of truth.

## R-2026-08-05-03 — Facebook Login for Business, both token types

Built the whole flow: configuration with the five permissions, System-user token type first, then a
second configuration with User access token when the system-user variant needed business-portfolio
machinery the app did not have. Both dialogs failed after login. Kept the configurations rather than
deleting them — if the app is ever added to a business portfolio, system-user is still the cleanest
credential.

## R-2026-08-05-04 — Graph API Explorer for the token

Failed again with `Invalid Scopes: pages_read_user_content`, exactly as on 2026-08-04, even though
the permission does not appear in Explorer's own list for this app. Explorer carries cached state per
app that cannot be cleared from its UI. Abandoned in favour of a hand-built OAuth URL — which then
produced the same error, proving the scope is injected by the app configuration rather than by any
request. That is the open question, not Explorer.
