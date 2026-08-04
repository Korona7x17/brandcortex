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
