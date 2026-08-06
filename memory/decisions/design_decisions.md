# Design Decisions

## Decision Log

Format:
```
## D-YYYY-MM-DD-NN — Decision Title
Rationale: [Why this was chosen]
Status: Accepted | Superseded | Rejected
Date: YYYY-MM-DD
Ref: [file@hash or #issue]
```

---


---

## D-2026-08-04-01 — Capture the card PNG at draft time; do not re-fetch at publish

**Rationale:** ThaiSwim cards render live from a URL, so fetching at publish (or handing Meta a `url`)
would re-render from whatever the data says then, while the caption was written from the draft-time
snapshot. Capturing once mirrors what the studio's Download button already does. **Supersedes an
earlier plan for a runtime `drift_check`** — user correctly pointed out drift isn't a real workflow
problem; freezing the image removes the question rather than detecting it.

**Status:** Accepted
**Date:** 2026-08-04
**Ref:** apps/api/src/brandcortex/services/assets.py; docs/thaiswim-integration.md@1aea5a

## D-2026-08-04-02 — `card_renders` is the handoff table; no new table, no shared bucket

**Rationale:** It already carries kind/params/snapshot/createdAt, and already means "generated, not
posted" because the history route writes only on Download. The snapshot is resolved server-side from
the same builders the PNG uses, so it cannot claim numbers the image never showed. Overrides spec
§4.3/§5.1.

**Status:** Accepted
**Date:** 2026-08-04
**Ref:** docs/thaiswim-integration.md@1aea5a

## D-2026-08-04-03 — Locale is resolved, never assumed; ThaiSwim card engines stay unmodified

**Rationale:** User first said Thai-only, then reversed — English is needed for future tenants.
`resolve_locale` reads `params.lang` and falls back to `brand_config.default_locale`, so English works
the day `card-history` records `lang` with no change our side. Everything the spec wanted but the
snapshot lacks (`season`, `event_count`) is derived in the adapter instead of asking ThaiSwim to change.
**Supersedes a Thai-only hardening made earlier the same session.**

**Status:** Accepted
**Date:** 2026-08-04
**Ref:** apps/api/src/brandcortex/adapters/source/thaiswim/mapping.py@491811

## D-2026-08-04-04 — Nothing grades its own work: computation > reality > withheld reasoning

**Rationale:** The reflection agent previously produced a claim, its evidence, and its own confidence
in that claim. Ladder now: deterministic checks first (sample floor, permutation test, leave-one-out
stability); a recorded falsifiable prediction scored by reality; a skeptic that never sees the
proposer's reasoning, defaults to refuted, and uses four distinct lenses where any one refutation
blocks. Schema splits proposer's claim from independent verification.

**Status:** Accepted
**Date:** 2026-08-04
**Ref:** apps/api/src/brandcortex/core/learning/verification.py@d97502;
skeptic.py@497b96; playbook.py@4a10dd; db/models/learning.py@b0c87d

## D-2026-08-04-05 — North-star components are z-scored before weighting, and rate-based

**Rationale:** The original config was a weighted sum of raw counts, so whichever metric was naturally
largest dominated regardless of weight — silently redefining the north star. Components also divide by
reach, isolating content quality from the channel's delivery decision. A missing component excludes the
post and is counted; it is never coerced to 0, which after a Meta metric rename would manufacture a
fabricated collapse the reflection agent would then explain.

**Status:** Accepted
**Date:** 2026-08-04
**Ref:** apps/api/src/brandcortex/core/analytics/outcomes.py@c73e1a; seeds/thaiswim.brand_config.json@915bbd

## D-2026-08-04-06 — Brand templates live with the adapter, not in core

**Rationale:** Core owns the registry and the constraints; the brand owns the words. ThaiSwim's Thai
structures register at bootstrap via `templates.register(source_type, locale, fn)`, so brand #2 writes
its own and touches nothing in `core/`.

**Status:** Accepted
**Date:** 2026-08-04
**Ref:** apps/api/src/brandcortex/adapters/source/thaiswim/templates.py@948922

## D-2026-08-04-07 — Failed drafts raise; the engine never silently repairs copy

**Rationale:** A caption quietly "fixed" hides that the engine fabricated a number. `DraftRejected`
carries every reason at once so review shows them together. Numeric grounding is a separate module from
voice because voice is a brand preference that could loosen, while factual grounding is a constraint no
config may switch off.

**Status:** Accepted
**Date:** 2026-08-04
**Ref:** apps/api/src/brandcortex/core/generation/engine.py@901c2d; claims.py@15b73f

## D-2026-08-04-08 — Event captions state `rowCount`, never the requested `n`

**Rationale:** A thin age group returns 8 swimmers for a top-10 request. A caption promising 10 over a
card showing 8 is a public claim the image refutes in the same post.

**Status:** Accepted
**Date:** 2026-08-04
**Ref:** apps/api/src/brandcortex/adapters/source/thaiswim/templates.py@948922

## D-2026-08-04-09 — Alembic baseline deferred to autogenerate; no hand-written initial migration

**Rationale:** Transcribing 8 tables of DDL by eye must match SQLAlchemy's output exactly, and where it
doesn't the drift stays silent until production. Autogenerate against a live Postgres is one command
and correct by construction.

**Status:** Accepted
**Date:** 2026-08-04
**Ref:** apps/api/alembic/README.md

## D-2026-08-05-01 — A rejected draft persists as `failed`; ingest does not raise

**Rationale:** The engine must raise (silently repairing an invented number hides that it invented
one), but ingest is a bulk pass over whatever the brand rendered today and one bad row must not stop
the other forty. Recording the reasons on a `failed` post repairs nothing and hides nothing — the
failure lands in the review queue. Single-post operations (`approve`, `publish`) still raise, because
there the caller is the person waiting for the answer.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/core/orchestrator.py@6da1aa

## D-2026-08-05-02 — Reviewer edits meet the same hard checks; `posts.facts` is frozen at draft time

**Rationale:** A caption asserting a number the card does not show is wrong whoever typed it, and a
link pasted into the body costs reach invisibly. Re-running the check needs the snapshot, so the
content item's `facts` are denormalized onto the post — which the review UI wants anyway, and which is
afterwards the only surviving record of what the image claimed, since the brand's row can change and
the card re-renders from live data.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/core/orchestrator.py@6da1aa; db/models/post.py@fffe23

## D-2026-08-05-03 — UTM campaign is `{source_type}-{8 hex}`, reversed by lookup not by parsing

**Rationale:** Embedding the whole post id is reversible and puts 32 characters of hex in a URL the
reader sees in full, because a channel comment renders the link as plain text — which reads as tooling
and cuts against the voice rule the system exists to protect. A unique index on `posts.utm_campaign`
makes the reverse join exact and turns a collision into a write error at draft time rather than two
posts silently merging their traffic.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/core/analytics/utm.py@c39cce

## D-2026-08-05-04 — Status columns are SQLAlchemy `Enum(native_enum=False)`, never `String`

**Rationale:** Fixes a live bug rather than expressing a preference. A `String` status writes fine and
loads back a bare `str`, so every `status is PostStatus.DRAFT` comparison in the orchestrator was
silently False for a row read from the database while still passing on the object in the identity map.
`native_enum=False` keeps storage a VARCHAR (adding a status stays an ordinary migration, not an
`ALTER TYPE`); `values_callable` stores `draft` rather than `DRAFT` so an API filter passes the string
straight through.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/db/models/enums.py@14772f; tests/unit/test_status_round_trip.py@f5b429

## D-2026-08-05-05 — Ingest cursor is `max(posts.source_generated_at)`, not a stored watermark

**Rationale:** It cannot drift out of step with what was actually drafted, because it *is* what was
actually drafted, and it survives a restart, redeploy or database restore with no separate state to
restore alongside it. Cost is re-polling the boundary row each cycle, which is free — ingest returns
the existing post.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/workers/ingest_watcher.py@407dcc

## D-2026-08-05-06 — `brand_config` round-trips through a `settings` JSON column

**Rationale:** The seed documents carry keys without a dedicated column (`supported_locales`,
`intro_lookback`) and `_comment` keys recording *why* a value is what it is. Dropping them on load
would leave that reasoning in git and nowhere an operator looks; a column per setting would mean a
migration every time a brand grows one. `save` replaces the row wholesale, because a config is
reviewed as a whole document and a partial write is how a voice rule goes missing without anyone
deciding to remove it.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/core/brand_config.py@c2f760; db/models/brand.py

## D-2026-08-05-07 — The orchestrator owns its commits, including failure states

**Rationale:** A publish that fails must leave the post `failed` even though the caller is about to
see an exception. A caller that rolled back on that exception would erase the only record of what
happened, which is exactly the case where the record matters most.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/core/orchestrator.py@6da1aa

## D-2026-08-05-08 — The asset store picks filesystem or S3 from the shape of `ASSET_BUCKET`

**Rationale:** Local development needs no credentials and no bucket; production needs no code change.
The key format is identical either way, so moving a deployment between them rewrites no stored key.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/services/assets.py@87aacb

## D-2026-08-05-09 — API startup logs a bootstrap failure; workers let it raise

**Rationale:** `registry.bootstrap()` reads `brand_config`, so an unseeded or unreachable database
would otherwise take down the whole API including the endpoints that would explain why. Unregistered
adapters make the routes that need one return a clear error, which is a better first thing to see than
a container that will not start. A publisher with no channel adapter has nothing useful to do, so
workers keep the loud behaviour.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/main.py; adapters/registry.py@a30566

## D-2026-08-05-10 — BrandCortex composes cards; ThaiSwim still renders them

**Rationale:** The card routes are a public, deterministic API and the swimmer search is CORS-open,
so composing needs no change to the card engines. Duplicating the renderer would fork the brand's
visual identity into two definitions that drift silently — the caption's card and the studio's card
would stop matching and nobody would notice until they were side by side.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/adapters/source/thaiswim/adapter.py; thaiswim@b9c14b2

## D-2026-08-05-11 — Composed content ids are derived from the render params

**Rationale:** A composed card has no `card_renders` row and BrandCortex never writes to the brand
DB, so the id must come from somewhere. Deriving it from the params keeps `ingest` idempotent —
composing the same board twice is one draft, not two — and the `bc-` prefix means a composed id is
never mistaken for a brand cuid.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/adapters/source/thaiswim/adapter.py

## D-2026-08-05-12 — The model writes captions; templates become the fallback

**Rationale:** Six hand-written angles have a low ceiling and made the assistant the bottleneck on a
Thai brand's voice — the wrong author for copy the owner should control. The guardrails that make an
LLM safe here already existed and already run: numeric grounding, notation and voice checks are
computations, and a person picks. Templates stay as the floor so a missing key or an outage degrades
the copy rather than stopping the queue.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/core/generation/writer.py@7af7ff

## D-2026-08-05-13 — Angles, notation and claim bindings are data, not code

**Rationale:** The brand owner edits the voice without a code change, which is the whole point of
`brand_config`. What is deliberately *not* editable is the hard rules — numbers must exist in the
facts, no link in the caption, the emoji ceiling — because they run after the model answers. The
brief is guidance; the validator is the guarantee.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/seeds/thaiswim.brand_config.json; apps/web/app/settings/voice/editor.tsx@3c5776

## D-2026-08-05-14 — Claims are bound to the fact they must equal

**Rationale:** "Every number exists in the facts" stops invention and not misattachment: with
goldCount 3 and rankedCount 12, `อันดับ 1 ของประเทศ 12 รายการ` is false and every number in it is
real. A phrase pattern now names the fact it must match. Brand-declared, so the core executes it
without learning what a stroke is.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/core/generation/claims.py@5f2e3e

## D-2026-08-05-15 — Brand notation is stripped before numbers are extracted

**Rationale:** Fixes a check that rejected correct copy. `สระ 50 ม.` is a 50-metre pool, not a claim
about the swim; on a 50m event it coincidentally matched and passed, and the first 100m event was
refused for an invented "50". A check that rejects correct copy is worse than no check, because it
teaches people to click through it.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/core/generation/claims.py@5f2e3e

## D-2026-08-05-16 — BrandCortex holds the schedule; Meta's native scheduling is refused

**Rationale:** `published=false` + `scheduled_publish_time` would show the post in Business Suite,
but a comment cannot attach to a post that does not exist yet, so the link would depend on a second
job firing later. A live card with no link is the single failure the design exists to prevent.
Atomicity beats visibility, and the queue already shows what is scheduled.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/adapters/channel/facebook/adapter.py@fc6ba8; workers/publisher.py@f54b34

## D-2026-08-05-17 — A failed publish records the live post id; a late slot is skipped, not published

**Rationale:** Two failures that had to stay recoverable. If the photo lands and the comment does
not, the id must be stored or nobody can find the card to fix or delete it. And a worker down
overnight must not wake and publish yesterday's post into an audience that has moved on — those stay
`scheduled` so a person picks the new moment.

**Status:** Accepted
**Date:** 2026-08-05
**Ref:** apps/api/src/brandcortex/core/orchestrator.py; workers/publisher.py@f54b34

## D-2026-08-06-01 — `pages_read_user_content` added to the app before Phase 3 needs it

**Rationale:** Facebook Login for Business injects the use case's whole permission bundle
server-side; the "Manage Pages" use case referenced this permission, and any use-case permission
not Added to the app invalidates *every* login dialog — including requests that never ask for it
(verified by reproducing the failure with a five-scope request, then watching the same request
succeed after "+ Add"). Adding it was the fix; the alternative — removing it from the use case —
is not offered by Meta's UI. It stays unused until Phase 3 inbox triage (`FUTURE_PERMISSIONS`),
and it does widen a future App Review.

**Status:** Accepted
**Date:** 2026-08-06
**Ref:** Meta app 1278952477505548 use case PAGES_API; adapters/channel/facebook/adapter.py (FUTURE_PERMISSIONS)

## D-2026-08-06-02 — Auth fails closed: no CLERK_ISSUER means 503, not open

**Rationale:** An API that approves and publishes to a live Page must never be reachable bare
because a deployment forgot one env var. Local development opts out with an explicit
AUTH_DISABLED=true — a statement a person wrote, not a default they fell into. Tests prove the
unconfigured state is a lock.

**Status:** Accepted
**Date:** 2026-08-06
**Ref:** apps/api/src/brandcortex/api/auth.py; tests/unit/test_api_auth.py

## D-2026-08-06-03 — The API verifies Clerk JWTs offline; the dashboard's auth is only for people

**Rationale:** Verification is signature-against-JWKS + issuer + azp, pure computation with cached
keys — Clerk down leaves signed-in reviewers working, and a bypassed Next middleware still dies at
the API with 401. The card image goes through a Next proxy because an <img> cannot carry a bearer
token.

**Status:** Accepted
**Date:** 2026-08-06
**Ref:** api/auth.py; web/middleware.ts; web/app/card/[id]/route.ts

## D-2026-08-06-04 — Publish refuses links whose host differs from the current BRAND_SITE_URL

**Rationale:** Links bake into a post at draft time and are never re-derived; the first live post
shipped localhost:9000 in its comment this way. Host comparison is a computation, names no brand in
core, and still permits a deliberate staging configuration. The worker treats the refusal as one
failed post, not a dead cycle.

**Status:** Accepted
**Date:** 2026-08-06
**Ref:** core/orchestrator.py (_foreign_link_hosts); workers/publisher.py; the localhost:9000 comment

## D-2026-08-06-05 — Captured cards on a Railway volume now; R2 before the cron worker exists

**Rationale:** Publish-now runs in the API process, so a mounted volume suffices for the MVP. But
Railway volumes cannot be shared between services, and the scheduled-publish worker is a separate
service — R2 is the precondition for the cron worker, not an optimization. Key format is identical
either way (assets.py dispatches on ASSET_BUCKET shape), so migration is a file copy.

**Status:** Accepted
**Date:** 2026-08-06
**Ref:** services/assets.py; docs/deploy.md

## D-2026-08-06-06 — The honorific is a config-declared voice rule, enforced by validator

**Rationale:** Every profile post named masters swimmers — most of them decades older than the
reviewer — with no `คุณ`, in the caption and again in the first comment, and the seed config's one
approved example did it too, so the model was learning the mistake. A prompt instruction drifts and a
template fix leaves the model path open, so it lands in three places: `_person()` as the only route a
name takes into copy, `voice.Honorific` + `check_names()` rejecting a draft that drops it, and the
prompt stating it. Prefix, locales and the `facts` keys holding names all come from `brand_config`,
so core learns which fields are people without learning whose. Prefixed mentions are stripped before
looking for a bare one, so one polite mention doesn't excuse a second.

**Status:** Accepted
**Date:** 2026-08-06
**Ref:** core/generation/voice.py@4903de; adapters/source/thaiswim/templates.py@656eec;
seeds/thaiswim.brand_config.json@0a0dc8; tests/unit/test_honorific.py

## D-2026-08-06-07 — Two registers, and the emoji ceiling moves 1 -> 2 to admit the warm one

**Rationale:** The owner found the generated copy dry and supplied a post they wrote by hand. Its
shape became `sweep` and `longevity` (the angles it is written for); `plain`, `breadth`, `standout`
and `club` stay factual, so the reviewer picks register as well as angle. Register carries through
both halves of a variant — a warm caption over a flat first comment reads as two people writing one
post. The ceiling settled at 2: 🏆 and 👏 carry the congratulation, the 👉/👇 arrows came off a nudge
that already says where the link is. Guidance rewritten so warmth comes from respect and from the
numbers, never from adjectives. **An owner decision, not the learning loop's** — §10.4 stands and
`voice.*` remains structurally unproposable.

**Status:** Accepted
**Date:** 2026-08-06
**Ref:** adapters/source/thaiswim/templates.py@656eec (_assemble_warm, COMMENTS_WARM_TH);
seeds/thaiswim.brand_config.json@0a0dc8 (max_emoji 2, guidance, examples[1]);
tests/unit/test_congratulatory_register.py

## D-2026-08-06-08 — Seed `brand_config` on boot, gated by two fingerprints

**Rationale:** A voice change could be written, tested, committed and deployed while every post
ignored it, because `brand_config` is a database row and the seed file is only its reviewed source.
That shape of bug is the worst kind — file, code and tests all say fixed. The API now applies
`seeds/*.brand_config.json` at start-up. The constraint that makes it safe: `/settings/voice` writes
the same row, and a deploy silently reverting someone's tuning is the worse bug, because they have no
reason to look. So each row carries `file_sha256` (has the file changed?) and `row_sha256` (has
anyone written to the row since?). File changed + row pristine → apply; both changed → refuse, log
both hashes, leave it to a human. Two hashes rather than one because a row does not round-trip to its
file — `to_document` returns columns the file never mentions, so the single-hash version made every
untouched row look edited and refused every change. A test caught that; the logic read fine.
`db.seed` stamps too, or a hand-run seed disables boot-seeding for that brand forever.

**Amended same day (adopt rule):** the first production boot refused with
`file=34b942d201fc row=34b942d201fc expected=(none)` — identical content, refused on provenance
alone, because the row had been seeded by hand before stamping existed. Refusing every unstamped row
leaves boot-seeding inert until someone runs the manual command it replaces. An unstamped row is now
adopted and stamped when applying the file would change nothing; one that differs is still refused.
"Would applying this change anything?" is computed against what the row would become
(`_projected`), not against the raw file — `save` overwrites only the columns a document names, so
for a partial seed file those differ. `brand_config._COLUMNS` is now public `COLUMNS`.

**Status:** Accepted
**Date:** 2026-08-06
**Ref:** db/bootstrap_config.py@34dac7; main.py@10632c; core/brand_config.py@b653b6; db/seed.py;
tests/unit/test_bootstrap_config.py

## D-2026-08-06-09 — No opener, no sign-off; variants differ by form, and the club never leads

**Rationale:** Four of six variants were one skeleton with a single line swapped, and the skeleton's
two fixed lines — a rotating scene-setter and an inspirational closing — were the advertising voice
the brand is defined against: they tell the reader how to feel about a fact the card already shows.
Both cut. Variants are now 3–5 short lines and differ in shape (record-card chain, trophy
congratulation, one prose sentence, counts headline, the swim itself, name-led), because a different
opener over the same skeleton is one variant written twice. The club angle leads with `คุณ{name}`,
not the club: it is the swimmer's achievement, and the club is prominent on line two so it still has
a reason to repost. Consequence: `intro_bank`/`intro_rotation` are unused by swimmer posts; the
mechanism stays and the engine records an `intro_line` only when the caption opens with one.

**Status:** Accepted (supersedes the intro-rotation half of §6.2/§6.4)
**Date:** 2026-08-06
**Ref:** adapters/source/thaiswim/templates.py@99ed18; seeds/thaiswim.brand_config.json@4cde02;
docs/BrandCortex-architecture.md §6.1–6.5
