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
