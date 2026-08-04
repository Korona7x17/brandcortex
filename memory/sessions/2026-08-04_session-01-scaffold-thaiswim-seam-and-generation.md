# Session Log – 2026-08-04_01
Tags: [Scaffold][ThaiSwim-seam][Generation][Learning-loop][Meta-auth]
Repo: brandcortex@0ac1a41 (all work untracked) | Context loaded: none — ContextLoop initialized this session

## Notes

Built BrandCortex from the architecture doc, then corrected the doc against the real ThaiSwim repo.

**Scaffold** — FastAPI + Next.js monorepo. All 8 tables from spec §5.2 modelled. Core is
brand/channel-agnostic, enforced by an AST test that scans `core/` for brand strings and adapter
imports (docstrings exempt — naming the brand in prose is documentation; `if brand == "thaiswim"` is
the failure).

**Read `dev/thaiswim`** — four findings that overrode spec §4.2–4.3, §5.1:
- No asset bucket exists or is needed; cards render on demand from a deterministic CORS-open URL
- `card_renders` already IS the handoff table, and already means "generated, not posted" (§4.4 needs
  no work — the route writes only on Download, never on preview)
- Canonical links are derived in the browser, never persisted → adapter must rebuild them
- Real snapshot keys differ from the doc's sketch (`goldCount` not `first_rank_count`, etc.)

**Corrected myself twice, both material:**
1. Claimed image/caption "drift" needed a runtime check. User pushed back correctly — the studio's
   Download already freezes the image. Fix was to capture the PNG at draft time, not to detect drift.
   Simpler and removes the question entirely.
2. Hardened everything to Thai-only after user said "no English cards". User then reversed —
   English needed for future tenants. Reverted to resolved-not-assumed locale.

**Self-review architecture** — after discussing a graph-engineering transcript, built the machinery
that stops the reflection agent grading its own work. Ladder: computation > reality > withheld
reasoning > inverted burden > diverse lenses > human.

**Meta auth — burned ~1h, unresolved.** App/secret/Page ID all correct; token still missing 3 scopes.
Root cause found late: Graph API Explorer caches an invalid scope (`pages_read_user_content`) that
kills every OAuth dialog, so Facebook reissues from the old grant. User (rightly) fed up. Parked.

## Bugs caught in own work

- `posts.content_id` typed `UUID`; ThaiSwim's `card_renders.id` is a **cuid** → `String(64)`
- `north_star` was a weighted sum of **raw counts** — scale beats weight, silently redefining the
  north star. Now z-scored before weighting.
- First scale-bug test was **vacuous** (passed under the buggy impl too); rewrote so raw-sum picks the
  opposite arm, and the test asserts that inline so it can't rot back
- `appsecret_proof` test pinned to a **fabricated** digest; re-pinned against `openssl` output
- `season_label` shipped with a broken placeholder body; implemented properly (UTC, matches web app)

## Artifacts

- CLAUDE.md@8b570c
- docs/thaiswim-integration.md@1aea5a
- packages/contracts/schemas/content-item.schema.json@7fc41c
- apps/api/seeds/thaiswim.brand_config.json@915bbd
- apps/api/src/brandcortex/adapters/source/thaiswim/mapping.py@491811
- apps/api/src/brandcortex/adapters/source/thaiswim/templates.py@948922
- apps/api/src/brandcortex/core/generation/engine.py@901c2d
- apps/api/src/brandcortex/core/generation/claims.py@15b73f
- apps/api/src/brandcortex/core/learning/verification.py@d97502
- apps/api/src/brandcortex/core/learning/skeptic.py@497b96
- apps/api/src/brandcortex/core/learning/playbook.py@4a10dd
- apps/api/src/brandcortex/core/analytics/outcomes.py@c73e1a
- apps/api/src/brandcortex/db/models/learning.py@b0c87d
- apps/api/src/brandcortex/adapters/channel/facebook/adapter.py@f7847f
- apps/api/src/brandcortex/adapters/channel/facebook/client.py@8f0784
- apps/api/tests/integration/test_thaiswim_pipeline.py@c8f9e0

Dashboard mockup (artifact): https://claude.ai/code/artifact/07628879-ccba-42d1-aab6-1383e94dd3cd

## Status

97 passed, 9 skipped. Pipeline `card_renders` row → checked Thai copy works offline — no DB, no
network, no Meta token.

C: Core never learns brand/channel identity — AST-enforced, not convention
C: No multi-tenant layer until brand #2 is real; `brand` is a keyed column, not a subsystem
C: Link always in first comment, never caption — photo reach + Meta's ~2-links/month body cap
C: House voice is fixed, not optimizable — `voice.*` structurally unproposable by the learning loop
C: North star = UTM sessions + amplification; reactions weighted 0.0 deliberately
C: ThaiSwim card engines are NOT to be modified — anything missing is derived our side
C: Meta app stays in Development mode; App Review likely never needed for a single owned Page

D: See memory/decisions/design_decisions.md — D-2026-08-04-01..09

Δ: 40+ files created; see Artifacts. Newly *implemented* (not stubs): mapping, templates, engine,
   claims, voice, intro_rotation, verification, outcomes, playbook gate, appsecret_proof
Δ: apps/api/seeds/thaiswim.brand_config.json@915bbd — north_star restructured to {weight, per_reach}
Δ: apps/api/src/brandcortex/db/models/learning.py@b0c87d — +verification/prediction/evidence-window
   columns, splitting proposer's claim from independent checks

Q: Meta Page token still missing pages_manage_posts / pages_manage_engagement / read_insights —
   Explorer caches an invalid scope. Untried: System User token via Business Settings (never expires,
   no OAuth dialog) — this is the recommended path for a server publisher.
Q: Graph version — .env pins v21.0, Meta console is on v26.0. Pin deliberately or move up?
Q: `per_reach: true` on utm_sessions optimizes session *rate* not total traffic. Product call.
Q: Verification thresholds (8/arm, p≤0.05, 50% stability) mean ~2-3 weeks before any comparison is
   evaluable at 1-2 posts/day. Product call, not statistical.
Q: Alembic has no baseline migration — deliberately deferred to autogenerate against a live DB.

→: Real React dashboard (mockup has genuine copy to render now) OR orchestrator + DB so drafts persist
→: Retry Meta token via System User route when user is not fed up
→: `uv sync && alembic revision --autogenerate -m "initial schema"` once Postgres is up
